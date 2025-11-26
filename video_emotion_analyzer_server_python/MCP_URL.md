# MCP URL情報

## 📡 サーバーの起動

```bash
cd video_emotion_analyzer_server_python
export YOUTUBE_API_KEY="AIzaSyDp1LoSRBU8-xMoPDqbYNjG6p4NfID5VXs"
venv/bin/uvicorn main:app --host 0.0.0.0 --port 8004
```

## 🌐 MCP URL

### ローカル（開発用）
```
http://localhost:8004/mcp
```

### ngrok経由（ChatGPT用）

1. 新しいターミナルでngrokを起動：
```bash
ngrok http 8004
```

2. 表示されるURLをコピー（例：`https://xxxx.ngrok-free.app`）

3. ChatGPTに登録するMCP URL：
```
https://xxxx.ngrok-free.app/mcp
```

## 🎯 利用可能なツール

1. **analyze-scenario** - シナリオ分析（文字起こし取得 + 分析）
2. **analyze-comments** - コメント分析（コメント取得 + 分析）
3. **analyze-emotion** - 感情分析（統合分析）

## 💡 ChatGPTでの使い方

```
この動画を分析してください：
https://www.youtube.com/watch?v=VIDEO_ID
```

AIが自動的に3ステップの分析を実行します！

## ✅ 動作確認

```bash
curl -X POST http://localhost:8004/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/list"}'
```

3つのツールが表示されればOK！

---

**注意**: ngrok URLは起動する度に変わるため、ChatGPTのConnector設定を更新する必要があります。



