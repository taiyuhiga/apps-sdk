# Video Comment Analyzer - Renderへのデプロイ方法

## 📋 準備するもの

1. **GitHubアカウント**
2. **Renderアカウント**（無料）
3. **YouTube Data API v3 キー**

## 🚀 デプロイ手順

### 1. GitHubリポジトリの作成

このディレクトリは既にGitで初期化されています。

次のステップ：

1. GitHubで新しいリポジトリを作成
   👉 https://github.com/new

2. 設定：
   - **Repository name**: `video-comment-analyzer`
   - **Description**: `YouTube Video Comment Analyzer MCP Server`
   - **Public/Private**: お好みで選択
   - ⚠️ **重要**: "Add a README file" などは**全てチェックを外す**

3. リモートリポジトリを追加してプッシュ：
   ```bash
   cd /Users/higataiyu/apps-sdk/video_comment_analyzer_server_python
   git remote add origin https://github.com/YOUR_USERNAME/video-comment-analyzer.git
   git push -u origin main
   ```

### 2. Renderでのセットアップ

1. [Render](https://render.com)にアクセスしてログイン

2. **New +** → **Web Service** をクリック

3. GitHubアカウントを接続してリポジトリを選択

4. 設定を入力：
   - **Name**: `video-comment-analyzer`
   - **Region**: Oregon (US West)
   - **Branch**: main
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

5. **Free** プランを選択

6. 環境変数を設定：
   - **Key**: `YOUTUBE_API_KEY`
   - **Value**: あなたのYouTube API Key

7. **Create Web Service** をクリック

### 3. デプロイ完了

デプロイ後、以下のようなURLが生成されます：

```
https://video-comment-analyzer-xxxx.onrender.com
```

MCPエンドポイント：
```
https://video-comment-analyzer-xxxx.onrender.com/mcp
```

### 4. ChatGPTでの設定

1. ChatGPTの設定から「Apps」または「Connectors」に移動
2. 「Add MCP Server」を選択
3. 上記のMCPエンドポイントURLを入力
4. 保存

## 🔧 トラブルシューティング

### ビルドエラー
- Renderのログを確認
- `requirements.txt`のパッケージバージョンを確認

### 環境変数エラー
- YouTube API キーが正しく設定されているか確認
- APIキーが有効か確認

### ポート関連のエラー
- `$PORT`環境変数を使用していることを確認

## 📝 メンテナンス

### コードの更新

GitHubにプッシュすると自動的に再デプロイされます：

```bash
git add .
git commit -m "Update feature"
git push origin main
```

### ログの確認

Renderダッシュボードの「Logs」タブでリアルタイムログを確認できます。

## 🆓 無料プランの制限

- **ビルド時間**: 月400分まで
- **帯域幅**: 月100GBまで
- **スリープ**: 15分間アクティビティがないとスリープ（初回アクセス時に起動）

## 機能

- YouTube動画のコメントを取得（最大1000件）
- いいね数順でソート
- 統計情報の計算
- 日本語での分析プロンプト提供
- ChatGPTが自動的に分析を実行

## 🔒 セキュリティ

- APIキーは必ず環境変数として設定
- `.env`ファイルはGitにコミットしない
- HTTPSが自動的に有効化されます
