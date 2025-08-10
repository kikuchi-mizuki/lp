#!/bin/bash

# アプリケーション起動スクリプト
echo "🚀 AIコレクションズアプリケーション起動スクリプト"
echo "================================================"

# 正しいディレクトリに移動
cd /Users/kikuchimizuki/Desktop/aicollections/lp/lp

# 既存のプロセスを停止
echo "📋 既存のプロセスを停止中..."
pkill -f "python app.py" 2>/dev/null || true
sleep 2

# 依存関係を確認
echo "📦 依存関係を確認中..."
python -c "import flask, psycopg2, stripe, requests" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ 依存関係は正常です"
else
    echo "❌ 依存関係に問題があります。pip install -r requirements.txt を実行してください"
    exit 1
fi

# データベース接続をテスト
echo "🗄️ データベース接続をテスト中..."
python -c "from utils.db import get_db_connection; conn = get_db_connection(); print('✅ データベース接続成功'); conn.close()" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ データベース接続は正常です"
else
    echo "❌ データベース接続に問題があります"
    exit 1
fi

# アプリケーションを起動
echo "🚀 アプリケーションを起動中..."
echo "📡 ポート 5001 で起動します"
echo "🌐 アクセスURL: http://localhost:5001"
echo "📊 ヘルスチェック: http://localhost:5001/health"
echo ""
echo "停止するには Ctrl+C を押してください"
echo "================================================"

python app.py 