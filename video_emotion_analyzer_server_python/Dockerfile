FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# ポートを公開（Renderは$PORT環境変数を使用）
EXPOSE 10000

# サーバーを起動（シェル形式でPORT環境変数を使用）
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}

