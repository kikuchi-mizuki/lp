# Railway 複数サービス共有デプロイガイド

## 概要

このガイドでは、Railwayで複数のサービス（AI予定秘書、AI経理秘書、AIタスクコンシェルジュ）を同じPostgreSQLデータベースで共有する方法を説明します。

## プロジェクト構造

```
lp/
├── railway.json                    # Railway設定ファイル
├── lp/                            # メインアプリ（AIコレクションズ）
├── schedule-service/              # AI予定秘書アプリ
│   ├── app.py
│   ├── requirements.txt
│   └── templates/
│       └── index.html
├── accounting-service/            # AI経理秘書アプリ
│   ├── app.py
│   ├── requirements.txt
│   └── templates/
│       └── index.html
└── task-service/                  # AIタスクコンシェルジュアプリ
    ├── app.py
    ├── requirements.txt
    └── templates/
        └── index.html
```

## デプロイ手順

### 1. Railway CLIのインストール

```bash
# npmを使用
npm install -g @railway/cli

# または yarnを使用
yarn global add @railway/cli
```

### 2. Railwayにログイン

```bash
railway login
```

### 3. プロジェクトの初期化

```bash
# プロジェクトディレクトリで実行
railway init
```

### 4. データベースの作成

```bash
# PostgreSQLデータベースを作成
railway add postgresql
```

### 5. 環境変数の設定

```bash
# 共有データベースの接続情報を取得
railway variables

# 各サービスで同じDATABASE_URLを使用
railway variables set DATABASE_URL="postgresql://..."
```

### 6. サービスのデプロイ

#### メインアプリ（AIコレクションズ）
```bash
# メインアプリをデプロイ
railway up
```

#### AI予定秘書アプリ
```bash
# schedule-serviceディレクトリに移動
cd schedule-service

# サービスをデプロイ
railway up --service ai-schedule-secretary
```

#### AI経理秘書アプリ
```bash
# accounting-serviceディレクトリに移動
cd ../accounting-service

# サービスをデプロイ
railway up --service ai-accounting-secretary
```

#### AIタスクコンシェルジュアプリ
```bash
# task-serviceディレクトリに移動
cd ../task-service

# サービスをデプロイ
railway up --service ai-task-concierge
```

### 7. ドメインの設定

各サービスにカスタムドメインを設定：

```bash
# AI予定秘書
railway domain --service ai-schedule-secretary

# AI経理秘書
railway domain --service ai-accounting-secretary

# AIタスクコンシェルジュ
railway domain --service ai-task-concierge
```

## 設定ファイルの詳細

### railway.json

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  },
  "services": [
    {
      "name": "ai-collections-main",
      "source": ".",
      "domains": [
        {
          "name": "ai-collections.herokuapp.com"
        }
      ]
    },
    {
      "name": "ai-schedule-secretary",
      "source": "./schedule-service",
      "domains": [
        {
          "name": "ai-schedule-secretary.railway.app"
        }
      ]
    },
    {
      "name": "ai-accounting-secretary",
      "source": "./accounting-service",
      "domains": [
        {
          "name": "ai-accounting-secretary.railway.app"
        }
      ]
    },
    {
      "name": "ai-task-concierge",
      "source": "./task-service",
      "domains": [
        {
          "name": "ai-task-concierge.railway.app"
        }
      ]
    }
  ]
}
```

## データベース共有の仕組み

### 1. 共有PostgreSQLデータベース

- 全サービスが同じ`DATABASE_URL`を使用
- `users`テーブルと`cancellation_history`テーブルを共有
- 解約履歴がリアルタイムで同期

### 2. 利用制限チェック

各サービスは以下のテーブルを参照：

```sql
-- ユーザー情報
SELECT id FROM users WHERE line_user_id = 'U1234567890abcdef';

-- 解約履歴
SELECT COUNT(*) FROM cancellation_history 
WHERE user_id = 1 AND content_type = 'AI予定秘書';
```

### 3. API エンドポイント

各サービスが提供するAPI：

- `POST /check_restriction` - 利用制限チェック
- `POST /restriction_message` - 制限メッセージ取得
- `GET /health` - ヘルスチェック

## テスト方法

### 1. ヘルスチェック

```bash
# 各サービスのヘルスチェック
curl https://ai-schedule-secretary.railway.app/health
curl https://ai-accounting-secretary.railway.app/health
curl https://ai-task-concierge.railway.app/health
```

### 2. 利用制限チェック

```bash
# 利用制限チェック
curl -X POST https://ai-schedule-secretary.railway.app/check_restriction \
  -H "Content-Type: application/json" \
  -d '{"line_user_id": "U1234567890abcdef"}'
```

### 3. ブラウザでのテスト

各サービスのURLにアクセスしてテスト画面を使用：

- https://ai-schedule-secretary.railway.app
- https://ai-accounting-secretary.railway.app
- https://ai-task-concierge.railway.app

## トラブルシューティング

### 1. データベース接続エラー

```bash
# データベース接続を確認
railway connect

# 環境変数を確認
railway variables
```

### 2. サービスが起動しない

```bash
# ログを確認
railway logs --service ai-schedule-secretary

# サービスを再起動
railway restart --service ai-schedule-secretary
```

### 3. 環境変数が設定されていない

```bash
# 環境変数を設定
railway variables set DATABASE_URL="postgresql://..."

# 設定を確認
railway variables
```

## セキュリティ考慮事項

### 1. データベースアクセス制限

- 各サービスは必要最小限のテーブルにのみアクセス
- 読み取り専用の権限を設定することを推奨

### 2. API認証

```python
# APIキーによる認証を追加
def verify_api_key(request):
    api_key = request.headers.get('X-API-Key')
    valid_keys = os.getenv('VALID_API_KEYS', '').split(',')
    return api_key in valid_keys
```

### 3. CORS設定

```python
# 許可するドメインを制限
from flask_cors import CORS

CORS(app, origins=[
    'https://ai-schedule-secretary.railway.app',
    'https://ai-accounting-secretary.railway.app',
    'https://ai-task-concierge.railway.app'
])
```

## 監視とログ

### 1. Railwayダッシュボード

- Railwayダッシュボードで各サービスの状態を監視
- ログ、メトリクス、エラーを確認

### 2. カスタム監視

```python
# ヘルスチェックエンドポイント
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'ai-schedule-secretary',
        'database_connected': bool(DATABASE_URL),
        'timestamp': datetime.now().isoformat()
    })
```

## コスト最適化

### 1. リソース使用量の監視

- RailwayダッシュボードでCPU・メモリ使用量を確認
- 必要に応じてリソースを調整

### 2. 自動スケーリング

```json
{
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

## 今後の拡張

### 1. マイクロサービス化

- 各サービスを独立したリポジトリに分離
- CI/CDパイプラインの構築

### 2. キャッシュ層の追加

- Redisを使用したキャッシュ機能
- データベース負荷の軽減

### 3. 監視・アラート

- Prometheus + Grafanaでの監視
- Slack/Discordへのアラート通知 