# クイックスタートガイド

## 1. 必要なAPIキーの取得

### YouTube Data API v3 キー

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成（または既存のプロジェクトを選択）
3. 左側メニューから「APIとサービス」→「ライブラリ」を選択
4. 「YouTube Data API v3」を検索して有効化
5. 「APIとサービス」→「認証情報」から「認証情報を作成」→「APIキー」を選択
6. 作成されたAPIキーをコピー

**Note**: OpenAI APIキーは不要です！分析はChatGPT自身が会話の中で行います。

## 2. 環境変数の設定

ターミナルで以下のコマンドを実行してAPIキーを設定します：

```bash
export YOUTUBE_API_KEY="YOUR_YOUTUBE_API_KEY_HERE"
```

**永続的に設定する場合** は、`~/.zshrc` または `~/.bashrc` に追加：

```bash
echo 'export YOUTUBE_API_KEY="YOUR_YOUTUBE_API_KEY_HERE"' >> ~/.zshrc
source ~/.zshrc
```

## 3. サーバーの起動

```bash
cd video_comment_analyzer_server_python
source ../.venv/bin/activate
python main.py
```

サーバーが起動すると、以下のメッセージが表示されます：

```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8003
```

## 4. ChatGPTでの使用

### 開発モードの有効化

1. [ChatGPT](https://chatgpt.com/) にアクセス
2. 設定（Settings）→「Developer mode」を有効化

### ローカルサーバーの公開（ngrokを使用）

別のターミナルウィンドウで：

```bash
# ngrokをインストール（初回のみ）
brew install ngrok

# ngrokでサーバーを公開
ngrok http 8003
```

ngrokから表示されるURLをコピー（例: `https://abcd1234.ngrok-free.app`）

### ChatGPTにアプリを追加

1. ChatGPTの設定から「Apps」または「Connectors」セクションに移動
2. 「Add MCP Server」または「Add Connector」を選択
3. サーバーURL: `https://YOUR_NGROK_URL.ngrok-free.app/mcp` を入力
4. 保存してアプリを有効化

## 5. 使用例

ChatGPTで以下のように質問してください：

```
この動画のコメントを分析してください：
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

または：

```
この動画のコメントを最大50件取得して分析して：
https://www.youtube.com/watch?v=VIDEO_ID
最大コメント数：50
```

## 6. 分析結果の例

分析結果には以下の項目が含まれます：

### 分析項目(1)
- **共感性の高いコメント**: いいね数が多いコメントのリスト
- **返信の多いコメント**: ディスカッションが活発なコメント

### 分析項目(2)
- 動画への要望
- 視聴者の不満
- 動画への指摘
- 改善を希望する声
- 批判的な意見

### 分析項目(3)
- 肯定的な意見のまとめ
- 否定的な意見のまとめ
- 維持すべきポイント

### 分析項目(4)
- 総合的な改善提案
- 修正すべきポイント
- 次回作に向けた具体的なアドバイス

## トラブルシューティング

### エラー: "YOUTUBE_API_KEY環境変数が設定されていません"

環境変数が正しく設定されているか確認：

```bash
echo $YOUTUBE_API_KEY
```

空白が返される場合は、手順2を再度実行してください。

### エラー: "コメントの取得中にエラーが発生しました"

- YouTube APIキーが有効か確認
- APIの使用制限（クォータ）を超えていないか確認
- 動画のコメントが有効になっているか確認（コメント無効の動画は取得不可）

### サーバーに接続できない

- ファイアウォールでポート8003がブロックされていないか確認
- サーバーが正常に起動しているか確認
- ngrokが正しく動作しているか確認

## 料金について

### YouTube Data API
- 無料枠：1日あたり10,000ユニット
- コメント取得：1回あたり約1ユニット
- 通常の使用では無料枠内で十分利用可能

### ChatGPT
- 分析はChatGPTの通常の会話として行われます
- 追加のAPI料金は発生しません
- ChatGPTの利用プラン（Plus, Team, Enterpriseなど）に応じた料金のみ

## 次のステップ

- より詳細な分析パラメータの追加
- 分析結果のエクスポート機能
- 複数動画の一括分析
- 時系列でのコメント傾向分析

質問や問題がある場合は、GitHubのIssuesセクションで報告してください。

