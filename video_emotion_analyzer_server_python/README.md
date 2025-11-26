# Video Emotion Analyzer MCP Server

YouTube動画の感情分析を3つのステップで行うMCPサーバーです。

## 機能

このサーバーは、YouTube動画を3段階で分析します：

1. **シナリオ分析（ステップ1）**: `youtube-transcript-api`を使用して動画の文字起こしを取得し、視聴者の感情を引き出すシナリオ要素を分析
2. **コメント分析（ステップ2）**: YouTube Data APIを使用してコメントを取得し、視聴者の実際の反応を分析
3. **感情分析（ステップ3）**: シナリオ分析とコメント分析の結果を統合して、視聴者の感情を深く理解

## セットアップ

### 1. 依存関係のインストール

```bash
cd video_emotion_analyzer_server_python
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. YouTube API Keyの設定

環境変数を設定します：

```bash
export YOUTUBE_API_KEY="AIzaSyDp1LoSRBU8-xMoPDqbYNjG6p4NfID5VXs"
```

または、`.env`ファイルを作成：

```
YOUTUBE_API_KEY=AIzaSyDp1LoSRBU8-xMoPDqbYNjG6p4NfID5VXs
```

### 3. サーバーの起動

```bash
uvicorn main:app --host 0.0.0.0 --port 8004
```

## ChatGPTでの使用方法

### 1. ngrokでローカルサーバーを公開

```bash
ngrok http 8004
```

ngrokから取得したURLをメモします（例: `https://xxxx.ngrok-free.app`）

### 2. ChatGPTにコネクターを追加

1. ChatGPTの設定を開く
2. **Connectors** > **Add Connector**
3. MCP URL: `https://xxxx.ngrok-free.app/mcp`
4. 保存

### 3. 会話で使用

ChatGPTとの会話で、以下のように使用します：

```
YouTube動画を分析したいです。
動画URL: https://www.youtube.com/watch?v=VIDEO_ID
```

サーバーは自動的に3つのツールを提供します：

1. **analyze-scenario**: シナリオ分析を開始
2. **analyze-comments**: コメント分析を開始（シナリオ分析完了後）
3. **analyze-emotion**: 感情分析を開始（コメント分析完了後）

## 分析フロー

1. **ユーザー**: YouTube動画のURLを送信
2. **AI**: `analyze-scenario`ツールを呼び出してシナリオ分析を実行
3. **AI**: 結果を分析して共有
4. **AI**: `analyze-comments`ツールを自動的に呼び出してコメント分析を実行
5. **AI**: 結果を分析して共有
6. **AI**: `analyze-emotion`ツールを自動的に呼び出して最終的な感情分析を実行
7. **AI**: 統合された分析結果を共有

## MCP URL

サーバーが起動すると、以下のエンドポイントが利用可能になります：

- **ローカル**: `http://localhost:8004/mcp`
- **ngrok経由**: `https://your-ngrok-url.ngrok-free.app/mcp`

## トラブルシューティング

### YouTube API エラー

- API Keyが正しく設定されているか確認してください
- YouTube Data API v3が有効になっているか確認してください
- APIの使用制限に達していないか確認してください

### 文字起こしエラー

- 動画に字幕が有効になっているか確認してください
- 自動生成字幕がオフになっている場合、文字起こしは取得できません

### コメントが取得できない

- 動画のコメントが無効になっていないか確認してください
- プライベート動画の場合、コメントを取得できません

## ライセンス

MIT License



