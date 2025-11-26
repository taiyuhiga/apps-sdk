"""Video Emotion Analyzer MCP server.

This server provides tools to analyze YouTube videos through three sequential steps:
1. Scenario Analysis - Transcribe video and analyze the content
2. Comment Analysis - Fetch and analyze viewer comments
3. Emotion Analysis - Synthesize insights from both analyses
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

import mcp.types as types
import requests
from googleapiclient.discovery import build
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from youtube_transcript_api import YouTubeTranscriptApi

from prompts import (
    SCENARIO_ANALYSIS_PROMPT,
    COMMENT_ANALYSIS_PROMPT,
    EMOTION_ANALYSIS_PROMPT,
)

# API Key from environment variable (set in Render dashboard or .env file)
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "AIzaSyDp1LoSRBU8-xMoPDqbYNjG6p4NfID5VXs")


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


def get_video_transcript(video_id: str) -> List[Dict[str, Any]]:
    """youtube-transcript-apiを使用して動画の文字起こしを取得する"""
    try:
        # YouTubeTranscriptApiをインスタンス化
        ytt_api = YouTubeTranscriptApi()

        # まず日本語の字幕を試す
        transcript_list = ytt_api.list(video_id)

        try:
            # 手動で作成された日本語字幕を優先
            transcript = transcript_list.find_manually_created_transcript(['ja'])
        except Exception:
            try:
                # 自動生成された日本語字幕
                transcript = transcript_list.find_generated_transcript(['ja'])
            except Exception:
                # 日本語がない場合は英語を取得して翻訳
                try:
                    transcript = transcript_list.find_transcript(['en'])
                    transcript = transcript.translate('ja')
                except Exception:
                    # 最初に見つかった字幕を取得
                    try:
                        transcript = transcript_list.find_generated_transcript(['en'])
                    except Exception:
                        # どの字幕でも取得
                        for t in transcript_list:
                            transcript = t
                            break

        return list(transcript.fetch())

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Transcript error: {error_details}")
        raise Exception(f"文字起こしの取得中にエラーが発生しました: {str(e)}")


def format_transcript(transcript: List[Any]) -> str:
    """文字起こしを読みやすい形式にフォーマットする"""
    formatted_lines = []

    for i, entry in enumerate(transcript, 1):
        # 新しいAPIではオブジェクトのプロパティとしてアクセス
        start_time = entry.start if hasattr(entry, 'start') else entry.get('start', 0)
        text = entry.text if hasattr(entry, 'text') else entry.get('text', '')

        minutes = int(start_time // 60)
        seconds = int(start_time % 60)

        formatted_lines.append(f"[{minutes:02d}:{seconds:02d}] {text}")

    return "\n".join(formatted_lines)


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

    # いいね数でソート（降順）
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


# ツールのスキーマ定義
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
            title="シナリオ分析",
            description="ユーザーがYouTube動画のURLを送信したときに呼び出します。動画の文字起こしを取得してシナリオ分析を行います。",
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
            description="ユーザーが「コメント分析して」と言ったときに呼び出します。動画のコメントを取得してコメント分析を行います。シナリオ分析で使用した同じ動画URLを使用してください。",
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
            description="ユーザーが「感情分析して」と言ったときに呼び出します。シナリオ分析とコメント分析の結果を統合して感情分析を行います。シナリオ分析で使用した同じ動画URLを使用してください。",
            inputSchema=EMOTION_TOOL_SCHEMA,
            annotations={
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        ),
    ]


async def _call_tool_request(req: types.CallToolRequest) -> types.ServerResult:
    """ツール呼び出しを処理する"""
    tool_name = req.params.name
    arguments = req.params.arguments or {}

    # ステップ1: シナリオ分析
    if tool_name == "analyze-scenario":
        try:
            payload = ScenarioAnalysisInput.model_validate(arguments)
        except ValidationError as exc:
            return types.ServerResult(
                types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"入力検証エラー: {exc.errors()}",
                        )
                    ],
                    isError=True,
                )
            )

        video_id = extract_video_id(payload.video_url)
        if not video_id:
            return types.ServerResult(
                types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text="有効なYouTube動画URLを指定してください。",
                        )
                    ],
                    isError=True,
                )
            )

        try:
            # 文字起こしを取得
            transcript = get_video_transcript(video_id)
            formatted_transcript = format_transcript(transcript)

            # 動画の長さを計算
            if transcript:
                last_entry = transcript[-1]
                last_start = last_entry.start if hasattr(last_entry, 'start') else last_entry.get('start', 0)
                last_duration = last_entry.duration if hasattr(last_entry, 'duration') else last_entry.get('duration', 0)
                total_duration = last_start + last_duration
            else:
                total_duration = 0
            minutes = int(total_duration // 60)
            seconds = int(total_duration % 60)

            result_text = f"""# 🎬 YouTube動画シナリオ分析（ステップ1/3）

## 📊 基本情報
- **動画URL**: {payload.video_url}
- **動画ID**: `{video_id}`
- **動画の長さ**: {minutes}分{seconds}秒
- **文字起こし行数**: {len(transcript)}行

---

## 📝 文字起こしデータ

{formatted_transcript}

---

## 📋 シナリオ分析指示

{SCENARIO_ANALYSIS_PROMPT}
"""

            return types.ServerResult(
                types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text=result_text,
                        )
                    ],
                    isError=False,
                )
            )
        except Exception as e:
            return types.ServerResult(
                types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"エラーが発生しました: {str(e)}",
                        )
                    ],
                    isError=True,
                )
            )

    # ステップ2: コメント分析
    elif tool_name == "analyze-comments":
        try:
            payload = CommentAnalysisInput.model_validate(arguments)
        except ValidationError as exc:
            return types.ServerResult(
                types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"入力検証エラー: {exc.errors()}",
                        )
                    ],
                    isError=True,
                )
            )

        video_id = extract_video_id(payload.video_url)
        if not video_id:
            return types.ServerResult(
                types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text="有効なYouTube動画URLを指定してください。",
                        )
                    ],
                    isError=True,
                )
            )

        try:
            # コメントを取得
            comments = get_youtube_comments(video_id, payload.max_comments)

            if not comments:
                return types.ServerResult(
                    types.CallToolResult(
                        content=[
                            types.TextContent(
                                type="text",
                                text="この動画にはコメントがありません、またはコメントが無効になっています。",
                            )
                        ],
                        isError=False,
                    )
                )

            # コメントをフォーマット
            comments_text = format_comments_for_analysis(comments)

            # 統計情報を計算
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
                    content=[
                        types.TextContent(
                            type="text",
                            text=result_text,
                        )
                    ],
                    isError=False,
                )
            )
        except Exception as e:
            return types.ServerResult(
                types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"エラーが発生しました: {str(e)}",
                        )
                    ],
                    isError=True,
                )
            )

    # ステップ3: 感情分析
    elif tool_name == "analyze-emotion":
        try:
            payload = EmotionAnalysisInput.model_validate(arguments)
        except ValidationError as exc:
            return types.ServerResult(
                types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"入力検証エラー: {exc.errors()}",
                        )
                    ],
                    isError=True,
                )
            )

        video_id = extract_video_id(payload.video_url)
        if not video_id:
            return types.ServerResult(
                types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text="有効なYouTube動画URLを指定してください。",
                        )
                    ],
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
                content=[
                    types.TextContent(
                        type="text",
                        text=result_text,
                    )
                ],
                isError=False,
            )
        )

    else:
        return types.ServerResult(
            types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"不明なツール: {tool_name}",
                    )
                ],
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
