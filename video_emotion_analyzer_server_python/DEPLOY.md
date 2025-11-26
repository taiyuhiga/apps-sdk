# Renderへのデプロイ手順

## 📋 前提条件

- GitHubアカウント
- Renderアカウント（https://render.com で無料登録）
- YouTube Data API Key

---

## 🚀 デプロイ手順

### 1. GitHubにプッシュ

```bash
cd video_emotion_analyzer_server_python
git add .
git commit -m "Add Render deployment config"
git push origin main
```

### 2. Renderでサービスを作成

1. [Render Dashboard](https://dashboard.render.com) にログイン
2. **New +** → **Web Service** をクリック
3. **Connect a repository** でGitHubリポジトリを選択
4. 以下の設定を行う：

| 設定項目 | 値 |
|---------|-----|
| **Name** | `video-emotion-analyzer` |
| **Region** | `Oregon (US West)` または `Singapore` |
| **Branch** | `main` |
| **Root Directory** | `video_emotion_analyzer_server_python` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

### 3. 環境変数を設定

**Environment** セクションで以下を追加：

| Key | Value |
|-----|-------|
| `YOUTUBE_API_KEY` | `AIzaSyDp1LoSRBU8-xMoPDqbYNjG6p4NfID5VXs` |
| `PYTHON_VERSION` | `3.12` |

### 4. デプロイ設定

- **Auto-Deploy**: `No`（手動デプロイ推奨）
- **Instance Type**: `Free`（無料枠）

### 5. デプロイ実行

**Create Web Service** をクリックしてデプロイ開始

---

## 📡 MCP URL

デプロイ完了後、以下の形式でMCP URLが発行されます：

```
https://video-emotion-analyzer.onrender.com/mcp
```

このURLをChatGPTのConnectorに登録してください。

---

## 🔄 手動デプロイ（更新時）

1. ローカルでコードを修正
2. GitHubにプッシュ
3. Renderダッシュボード → サービス選択 → **Manual Deploy** → **Deploy latest commit**

---

## ⚠️ 注意事項

### 無料枠の制限

- **スリープ**: 15分間アクセスがないとスリープ（初回アクセスに30秒かかる）
- **稼働時間**: 750時間/月
- **帯域幅**: 100GB/月

### スリープ対策

無料枠でもスリープを防ぐには、外部サービス（UptimeRobot等）で定期的にアクセスする方法があります。

---

## 🛠️ トラブルシューティング

### デプロイが失敗する

1. **Logs** タブでエラーを確認
2. `requirements.txt` の依存関係を確認
3. Python バージョンを確認（3.12推奨）

### MCP URLにアクセスできない

1. サービスが **Live** 状態か確認
2. 正しいURL形式か確認（`/mcp` が必要）
3. CORSエラーの場合はブラウザのコンソールを確認

### YouTube APIエラー

1. 環境変数 `YOUTUBE_API_KEY` が設定されているか確認
2. APIキーが有効か確認
3. YouTube Data API v3 が有効になっているか確認

---

## 📊 使い方

ChatGPTでConnectorを追加後：

1. **YouTube動画のURLを送信** → シナリオ分析
2. **「コメント分析して」** → コメント分析
3. **「感情分析して」** → 感情分析

---

## 🔗 関連リンク

- [Render Documentation](https://render.com/docs)
- [YouTube Data API](https://developers.google.com/youtube/v3)
- [MCP Protocol](https://modelcontextprotocol.io/)

