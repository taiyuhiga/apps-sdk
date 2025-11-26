"""Video Emotion Analyzer MCP server.

This server provides tools to analyze YouTube videos through three sequential steps:
1. Scenario Analysis - Transcribe video using Gemini 2.5 Flash-Lite
2. Comment Analysis - Fetch and analyze viewer comments
3. Emotion Analysis - Synthesize insights from both analyses
"""

from __future__ import annotations

import os
import re
import tempfile
import time
from typing import Any, Dict, List, Optional

import mcp.types as types
from googleapiclient.discovery import build
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, ValidationError
import google.generativeai as genai
import yt_dlp

from prompts import (
    COMMENT_ANALYSIS_PROMPT,
    EMOTION_ANALYSIS_PROMPT,
)

# API Keys
YOUTUBE_API_KEY = "AIzaSyDp1LoSRBU8-xMoPDqbYNjG6p4NfID5VXs"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBRJ-342UGbJH9h52XDdXTwmzG22BOuQs8")

# Configure Gemini API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class ScenarioAnalysisInput(BaseModel):
    """Schema for scenario analysis tool."""

    video_url: str = Field(
        ...,
        alias="videoUrl",
        description="YouTube動画のURL（例: https://www.youtube.com/watch?v=VIDEO_ID）",
    )

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class CommentAnalysisInput(BaseModel):
    """Schema for comment analysis tool."""

    video_url: str = Field(
        ...,
        alias="videoUrl",
        description="YouTube動画のURL（例: https://www.youtube.com/watch?v=VIDEO_ID）",
    )
    max_comments: int = Field(
        1000,
        alias="maxComments",
        description="取得する最大コメント数（デフォルト: 1000）",
    )

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class EmotionAnalysisInput(BaseModel):
    """Schema for emotion analysis tool."""

    video_url: str = Field(
        ...,
        alias="videoUrl",
        description="YouTube動画のURL",
    )

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


mcp = FastMCP(
    name="video-emotion-analyzer",
    stateless_http=True,
)


def extract_video_id(url: str) -> Optional[str]:
    """YouTubeのURLから動画IDを抽出する"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([a-zA-Z0-9_-]+)',
        r'(?:youtube\.com\/embed\/)([a-zA-Z0-9_-]+)',
        r'(?:youtu\.be\/)([a-zA-Z0-9_-]+)',
        r'(?:youtube\.com\/v\/)([a-zA-Z0-9_-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def download_youtube_audio(video_url: str) -> str:
    """yt-dlpを使用してYouTube動画の音声をダウンロードする"""
    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, "audio.mp3")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(temp_dir, 'audio.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        return output_path
    except Exception as e:
        raise Exception(f"音声のダウンロード中にエラーが発生しました: {str(e)}")


def transcribe_with_gemini(audio_path: str) -> str:
    """Gemini 2.5 Flash-Liteを使用して音声を文字起こしする"""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY環境変数が設定されていません")
    
    try:
        # 音声ファイルをアップロード
        audio_file = genai.upload_file(audio_path)
        
        # ファイルの処理完了を待つ
        while audio_file.state.name == "PROCESSING":
            time.sleep(2)
            audio_file = genai.get_file(audio_file.name)
        
        if audio_file.state.name == "FAILED":
            raise Exception("ファイルの処理に失敗しました")
        
        # Gemini 2.5 Flash-Liteモデルを使用
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        
        # 文字起こしを依頼（シンプルなプロンプト）
        prompt = """この音声の内容を日本語で文字起こししてください。
話者の発言をそのまま正確に書き起こしてください。
タイムスタンプは不要です。発言内容のみを記載してください。"""
        
        response = model.generate_content([prompt, audio_file])
        
        # アップロードしたファイルを削除
        genai.delete_file(audio_file.name)
        
        return response.text
        
    except Exception as e:
        raise Exception(f"Geminiでの文字起こし中にエラーが発生しました: {str(e)}")


def get_video_transcript_with_gemini(video_url: str) -> str:
    """YouTube動画をダウンロードしてGeminiで文字起こしする"""
    audio_path = None
    try:
        # 音声をダウンロード
        audio_path = download_youtube_audio(video_url)
        
        # Geminiで文字起こし
        transcript = transcribe_with_gemini(audio_path)
        
        return transcript
        
    finally:
        # 一時ファイルを削除
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
            # 親ディレクトリも削除
            parent_dir = os.path.dirname(audio_path)
            if os.path.exists(parent_dir):
                os.rmdir(parent_dir)


def get_youtube_comments(video_id: str, max_results: int = 1000) -> List[Dict[str, Any]]:
    """YouTube Data APIを使用してコメントを取得する"""
    api_key = YOUTUBE_API_KEY or os.environ.get('YOUTUBE_API_KEY')
    if not api_key:
        raise ValueError("YOUTUBE_API_KEYが設定されていません")
    
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    comments = []
    next_page_token = None
    
    while len(comments) < max_results:
        try:
            request = youtube.commentThreads().list(
                part='snippet,replies',
                videoId=video_id,
                maxResults=min(100, max_results - len(comments)),
                pageToken=next_page_token,
                textFormat='plainText',
                order='relevance'
            )
            response = request.execute()
            
            for item in response.get('items', []):
                snippet = item['snippet']['topLevelComment']['snippet']
                comment_data = {
                    'text': snippet['textDisplay'],
                    'author': snippet['authorDisplayName'],
                    'likes': snippet['likeCount'],
                    'reply_count': item['snippet']['totalReplyCount'],
                    'published_at': snippet['publishedAt'],
                }
                comments.append(comment_data)
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
                
        except Exception as e:
            raise Exception(f"コメントの取得中にエラーが発生しました: {str(e)}")
    
    return comments


def format_comments_for_analysis(comments: List[Dict[str, Any]]) -> str:
    """コメントを分析用のフォーマットに整形する"""
    formatted = []
    sorted_comments = sorted(comments, key=lambda x: x['likes'], reverse=True)
    
    for i, comment in enumerate(sorted_comments, 1):
        formatted.append(
            f"【コメント {i}】\n"
            f"投稿者: {comment['author']}\n"
            f"内容: {comment['text']}\n"
            f"👍 いいね数: {comment['likes']}\n"
            f"💬 返信数: {comment['reply_count']}\n"
            f"📅 投稿日時: {comment['published_at']}\n"
        )
    return "\n".join(formatted)


SCENARIO_TOOL_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "videoUrl": {
            "type": "string",
            "description": "YouTube動画のURL（例: https://www.youtube.com/watch?v=VIDEO_ID）",
        }
    },
    "required": ["videoUrl"],
    "additionalProperties": False,
}

COMMENT_TOOL_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "videoUrl": {
            "type": "string",
            "description": "YouTube動画のURL（例: https://www.youtube.com/watch?v=VIDEO_ID）",
        },
        "maxComments": {
            "type": "integer",
            "description": "取得する最大コメント数（デフォルト: 1000）",
            "default": 1000,
        }
    },
    "required": ["videoUrl"],
    "additionalProperties": False,
}

EMOTION_TOOL_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "videoUrl": {
            "type": "string",
            "description": "YouTube動画のURL",
        }
    },
    "required": ["videoUrl"],
    "additionalProperties": False,
}


@mcp._mcp_server.list_tools()
async def _list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name="analyze-scenario",
            title="動画文字起こし",
            description="ユーザーがYouTube動画のURLを送信したときに呼び出します。Gemini 2.5 Flash-Liteを使用して動画の文字起こしを行い、文字起こしデータのみを返します。",
            inputSchema=SCENARIO_TOOL_SCHEMA,
            annotations={
                "destructiveHint": False,
                "openWorldHint": True,
                "readOnlyHint": True,
            },
        ),
        types.Tool(
            name="analyze-comments",
            title="コメント分析",
            description="ユーザーが「A」と入力したときに呼び出します。動画のコメントを取得してコメント分析を行います。シナリオ分析で使用した同じ動画URLを使用してください。",
            inputSchema=COMMENT_TOOL_SCHEMA,
            annotations={
                "destructiveHint": False,
                "openWorldHint": True,
                "readOnlyHint": True,
            },
        ),
        types.Tool(
            name="analyze-emotion",
            title="感情分析",
            description="ユーザーが「A」と入力したときに呼び出します（コメント分析完了後）。シナリオ分析とコメント分析の結果を統合して感情分析を行います。シナリオ分析で使用した同じ動画URLを使用してください。",
            inputSchema=EMOTION_TOOL_SCHEMA,
            annotations={
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        ),
    ]


def handle_scenario_analysis(arguments: dict) -> types.ServerResult:
    """シナリオ分析を処理する - Gemini 2.5 Flash-Liteで文字起こしを行い、文字起こしデータのみを返す"""
    try:
        payload = ScenarioAnalysisInput.model_validate(arguments)
    except ValidationError as exc:
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text=f"入力検証エラー: {exc.errors()}")],
                isError=True,
            )
        )
    
    video_id = extract_video_id(payload.video_url)
    if not video_id:
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text="有効なYouTube動画URLを指定してください。")],
                isError=True,
            )
        )
    
    try:
        # Gemini 2.5 Flash-Liteで文字起こしを実行
        transcript_text = get_video_transcript_with_gemini(payload.video_url)
        
        # 文字起こしデータのみを返す
        result_text = f"""# 📝 YouTube動画文字起こしデータ

## 📊 基本情報
- **動画URL**: {payload.video_url}
- **動画ID**: `{video_id}`
- **文字起こしエンジン**: Gemini 2.5 Flash-Lite

---

## 📝 文字起こし内容

{transcript_text}
"""
        
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text=result_text)],
                isError=False,
            )
        )
        
    except Exception as e:
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text=f"エラーが発生しました: {str(e)}")],
                isError=True,
            )
        )


def handle_comment_analysis(arguments: dict) -> types.ServerResult:
    """コメント分析を処理する"""
    try:
        payload = CommentAnalysisInput.model_validate(arguments)
    except ValidationError as exc:
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text=f"入力検証エラー: {exc.errors()}")],
                isError=True,
            )
        )
    
    video_id = extract_video_id(payload.video_url)
    if not video_id:
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text="有効なYouTube動画URLを指定してください。")],
                isError=True,
            )
        )
    
    try:
        comments = get_youtube_comments(video_id, payload.max_comments)
        
        if not comments:
            return types.ServerResult(
                types.CallToolResult(
                    content=[types.TextContent(type="text", text="この動画にはコメントがありません、またはコメントが無効になっています。")],
                    isError=False,
                )
            )
        
        comments_text = format_comments_for_analysis(comments)
        
        total_likes = sum(c['likes'] for c in comments)
        total_replies = sum(c['reply_count'] for c in comments)
        avg_likes = total_likes / len(comments) if comments else 0
        
        result_text = f"""# 💬 YouTube動画コメント分析（ステップ2/3）

## 📊 基本情報
- **動画URL**: {payload.video_url}
- **動画ID**: `{video_id}`
- **取得コメント数**: {len(comments)}件
- **合計いいね数**: {total_likes}
- **合計返信数**: {total_replies}
- **平均いいね数**: {avg_likes:.1f}

---

## 📝 コメント一覧（いいね数順）

{comments_text}

---

## 📋 コメント分析指示

{COMMENT_ANALYSIS_PROMPT}
"""
        
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text=result_text)],
                isError=False,
            )
        )
        
    except Exception as e:
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text=f"エラーが発生しました: {str(e)}")],
                isError=True,
            )
        )


def handle_emotion_analysis(arguments: dict) -> types.ServerResult:
    """感情分析を処理する"""
    try:
        payload = EmotionAnalysisInput.model_validate(arguments)
    except ValidationError as exc:
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text=f"入力検証エラー: {exc.errors()}")],
                isError=True,
            )
        )
    
    video_id = extract_video_id(payload.video_url)
    if not video_id:
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text="有効なYouTube動画URLを指定してください。")],
                isError=True,
            )
        )
    
    result_text = f"""# ❤️ YouTube動画感情分析（ステップ3/3）

## 📊 基本情報
- **動画URL**: {payload.video_url}
- **動画ID**: `{video_id}`

---

## 📋 感情分析指示

これまでに行った以下の分析結果を参照してください：

1. **シナリオ分析**：動画の文字起こしデータから視聴者の感情的な反応を予測した結果
2. **コメント分析**：実際の視聴者のコメントから得られた感情と反応のデータ

これら2つの分析結果を統合して、以下の質問に答えてください：

{EMOTION_ANALYSIS_PROMPT}
"""
    
    return types.ServerResult(
        types.CallToolResult(
            content=[types.TextContent(type="text", text=result_text)],
            isError=False,
        )
    )


async def _call_tool_request(req: types.CallToolRequest) -> types.ServerResult:
    """ツール呼び出しを処理する"""
    tool_name = req.params.name
    arguments = req.params.arguments or {}
    
    if tool_name == "analyze-scenario":
        return handle_scenario_analysis(arguments)
    elif tool_name == "analyze-comments":
        return handle_comment_analysis(arguments)
    elif tool_name == "analyze-emotion":
        return handle_emotion_analysis(arguments)
    else:
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text=f"不明なツール: {tool_name}")],
                isError=True,
            )
        )


mcp._mcp_server.request_handlers[types.CallToolRequest] = _call_tool_request

app = mcp.streamable_http_app()

try:
    from starlette.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )
except Exception:
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8004)
