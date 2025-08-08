# 軽量なPython 3.11イメージを使用
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# 環境変数を設定してメモリ使用量を削減
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# システムパッケージの更新と必要最小限のパッケージをインストール
# メモリ使用量を最小限に抑えるため、一度にインストールしてクリーンアップ
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/* \
    && rm -rf /var/cache/apt/*

# Python依存関係をコピーしてインストール
COPY lp/requirements.txt .
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

# アプリケーションファイルをコピー
COPY lp/ .

# ポートを公開（参考値）。実際にはRailwayが割り当てる$PORTで起動します
EXPOSE 3000

# 環境変数を設定
ENV PYTHONPATH=/app

# Flaskの最小アプリを起動
CMD ["python", "app_simple.py"]
