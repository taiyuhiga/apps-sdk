"""Video Comment Analyzer MCP server implemented with the Python FastMCP helper.

This server provides tools to analyze YouTube video comments using ChatGPT.
It fetches comments from YouTube videos and performs detailed analysis based on
predefined criteria including engagement metrics, viewer sentiment, and improvement suggestions.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

import mcp.types as types
from googleapiclient.discovery import build
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class VideoAnalysisInput(BaseModel):
    """Schema for video comment analysis tool."""

    video_url: str = Field(
        ...,
        alias="videoUrl",
        description="YouTube動画のURL（例: https://www.youtube.com/watch?v=VIDEO_ID）",
    )
    max_comments: int = Field(
        1000,
        alias="maxComments",
        description="取得する最大コメント数（デフォルト: 1000、可能な限り多く取得）",
    )

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


mcp = FastMCP(
    name="video-comment-analyzer",
    stateless_http=True,
)


ANALYSIS_PROMPT = """⚠️ **必ず日本語で回答してください** ⚠️

以下のルールに則ってコメントを分析して下さい。

## 分析項目(1): エンゲージメント分析
・共感性の高いコメントの抽出（いいねの数が多いコメント）
・返信の数が多いコメントの抽出
・具体的なコメント内容を引用して紹介

## 分析項目(2): 視聴者の意見
・動画への要望
・視聴者の不満
・動画への指摘
・改善を希望する声
・批判的な意見

## 分析項目(3): 総合評価
・肯定的な意見をまとめる
・否定的な意見をまとめる
・今後質の高い動画作りをする上で維持するポイントをまとめる

## 分析項目(4): 改善提案
分析項目1〜3を総合的に分析し、仮にこの動画を作り直すことを前提として、
ミスをなくし、修正すべきポイントと改善すべきポイントを具体的にまとめること

**重要**: 全ての分析結果は必ず日本語で記載してください。
"""


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


def get_youtube_comments(video_id: str, max_results: int = 100) -> List[Dict[str, Any]]:
    """YouTube Data APIを使用してコメントを取得する"""
    api_key = os.environ.get('YOUTUBE_API_KEY')
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY環境変数が設定されていません")
    
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


TOOL_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "videoUrl": {
            "type": "string",
            "description": "YouTube動画のURL（例: https://www.youtube.com/watch?v=VIDEO_ID）",
        },
        "maxComments": {
            "type": "integer",
            "description": "取得する最大コメント数（デフォルト: 1000、可能な限り多く取得）",
            "default": 1000,
        }
    },
    "required": ["videoUrl"],
    "additionalProperties": False,
}


@mcp._mcp_server.list_tools()
async def _list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name="analyze-video-comments",
            title="動画コメント分析",
            description="YouTube動画のコメントを取得して、エンゲージメント、視聴者の意見、改善点などを詳細に分析します。",
            inputSchema=TOOL_INPUT_SCHEMA,
            annotations={
                "destructiveHint": False,
                "openWorldHint": True,  # インターネットアクセスが必要
                "readOnlyHint": True,
            },
        )
    ]


async def _call_tool_request(req: types.CallToolRequest) -> types.ServerResult:
    """ツール呼び出しを処理する"""
    if req.params.name != "analyze-video-comments":
        return types.ServerResult(
            types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"不明なツール: {req.params.name}",
                    )
                ],
                isError=True,
            )
        )
    
    arguments = req.params.arguments or {}
    try:
        payload = VideoAnalysisInput.model_validate(arguments)
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
    
    # 動画IDを抽出
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
        
        # コメントをフォーマット（いいね数でソート済み）
        comments_text = format_comments_for_analysis(comments)
        
        # 統計情報を計算
        total_likes = sum(c['likes'] for c in comments)
        total_replies = sum(c['reply_count'] for c in comments)
        avg_likes = total_likes / len(comments) if comments else 0
        
        # ChatGPTに分析を依頼するためのプロンプトとデータを返す
        result_text = f"""# YouTube動画コメントデータ

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

## 📋 分析指示

{ANALYSIS_PROMPT}
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

    uvicorn.run("main:app", host="0.0.0.0", port=8003)

