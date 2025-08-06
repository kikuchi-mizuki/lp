# AIコレクションズアプリケーション

## 🚀 起動方法

### 方法1: 起動スクリプトを使用（推奨）
```bash
cd /Users/kikuchimizuki/Desktop/aicollections/lp/lp
./start_app.sh
```

### 方法2: 手動起動
```bash
# 1. 正しいディレクトリに移動
cd /Users/kikuchimizuki/Desktop/aicollections/lp/lp

# 2. 依存関係をインストール
pip install -r requirements.txt

# 3. アプリケーションを起動
python app.py
```

## 📍 重要な注意事項

### ディレクトリ構造
- **正しいディレクトリ**: `/Users/kikuchimizuki/Desktop/aicollections/lp/lp/`
- **間違ったディレクトリ**: `/Users/kikuchimizuki/Desktop/aicollections/lp/`

### ポート設定
- デフォルトポート: 5001
- 環境変数で変更可能: `PORT=5002 python app.py`

## 🔧 トラブルシューティング

### エラー1: "No such file or directory"
**原因**: 間違ったディレクトリで実行している
**解決策**: 
```bash
cd /Users/kikuchimizuki/Desktop/aicollections/lp/lp
```

### エラー2: "Address already in use"
**原因**: ポート5001が既に使用されている
**解決策**: 
```bash
# 既存のプロセスを停止
pkill -f "python app.py"

# 別のポートで起動
PORT=5002 python app.py
```

### エラー3: "cursor already closed"
**原因**: データベース接続の問題
**解決策**: 
```bash
# データベース接続をテスト
python -c "from utils.db import get_db_connection; conn = get_db_connection(); print('成功'); conn.close()"
```

## 🌐 アクセス確認

アプリケーションが正常に起動したら、以下のURLでアクセスできます：

- **メインページ**: http://localhost:5001
- **ヘルスチェック**: http://localhost:5001/health
- **企業登録**: http://localhost:5001/company-registration
- **ダッシュボード**: http://localhost:5001/company-dashboard

## 📊 動作確認

```bash
# ヘルスチェック
curl http://localhost:5001/health

# 期待されるレスポンス
{"message":"Application is running","status":"ok","timestamp":"..."}
```

## 🛠️ 開発用コマンド

```bash
# プロセス確認
ps aux | grep python

# プロセス停止
pkill -f "python app.py"

# ポート確認
lsof -i :5001

# ログ確認
tail -f app.log
```

## 📁 ディレクトリ構造

```
lp/
├── app.py                    # メインアプリケーション
├── start_app.sh             # 起動スクリプト
├── requirements.txt          # 依存関係
├── README.md               # このファイル
├── routes/                 # ルート定義
├── services/               # サービス層
├── models/                 # データモデル
├── utils/                  # ユーティリティ
├── templates/              # HTMLテンプレート
└── static/                 # 静的ファイル
```

## 🔄 更新履歴

- 2025-08-06: 起動スクリプト追加、README更新
- 2025-08-06: データベース接続エラー修正
- 2025-08-06: ポート設定を5001に変更
