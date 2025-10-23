# Video Comment Analyzer - MCP Server

YouTube動画のコメントを取得・分析するChatGPTアプリです。

## 機能

- YouTube動画のURLからコメントを自動取得
- コメントの詳細分析（エンゲージメント、視聴者の意見、改善点など）
- 以下の項目に沿った分析：
  - 共感性の高いコメント（いいね数が多い）
  - 返信の多いコメント
  - 動画への要望・不満・指摘
  - 肯定的/否定的意見のまとめ
  - 改善すべきポイント

## セットアップ

### 1. 依存関係のインストール

```bash
cd video_comment_analyzer_server_python
pip install -r requirements.txt
```

### 2. API キーの設定

YouTube Data APIキーのみ必要です：

```bash
export YOUTUBE_API_KEY="your_youtube_api_key"
```

**Note**: OpenAI APIキーは不要です。分析はChatGPT自身が行います。

#### YouTube API Keyの取得方法

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成
3. 「APIとサービス」→「ライブラリ」から「YouTube Data API v3」を有効化
4. 「認証情報」からAPIキーを作成

### 3. サーバーの起動

```bash
python main.py
```

サーバーはデフォルトで `http://localhost:8003` で起動します。

## ChatGPTでの使用方法

1. ChatGPTの設定から「Apps」セクションに移動
2. 「Add MCP Server」を選択
3. サーバーURL: `http://localhost:8003` を入力
4. 接続後、以下のように使用できます：

```
この動画のコメントを分析してください: https://www.youtube.com/watch?v=VIDEO_ID
```

## 使用例

```
ユーザー: この動画のコメントを分析して: https://www.youtube.com/watch?v=dQw4w9WgXcQ

ChatGPT: 動画コメント分析を実行します...

[分析結果が表示されます]
- 共感性の高いコメント
- 返信の多いコメント
- 視聴者の要望と不満
- 肯定的・否定的意見のまとめ
- 改善提案
```

## パラメータ

- `videoUrl` (必須): YouTube動画のURL
- `maxComments` (オプション): 取得する最大コメント数（デフォルト: 100）

## トラブルシューティング

### 「YOUTUBE_API_KEY環境変数が設定されていません」エラー

環境変数が正しく設定されているか確認してください：

```bash
echo $YOUTUBE_API_KEY
```

### 「コメントの取得中にエラーが発生しました」エラー

- YouTube API キーが有効か確認
- APIの利用制限を超えていないか確認
- 動画のコメントが有効になっているか確認

## ライセンス

このプロジェクトは MIT ライセンスの下でライセンスされています。

