# AIコレクションズ - AI秘書サブスクリプション

AI秘書サービスを提供するFlaskアプリケーションです。

## 機能

- AI予定秘書（Googleカレンダー連携）
- AI経理秘書（見積書・請求書作成）
- AIタスクコンシェルジュ（タスク最適配置）
- Stripe連携による月額課金
- LINE Bot連携

## Railwayでのデプロイ手順

### 1. Railwayアカウント作成
- [Railway](https://railway.app/) にアクセスしてアカウントを作成

### 2. GitHubリポジトリとの連携
- GitHubリポジトリをRailwayに接続
- 自動デプロイを有効化

### 3. 環境変数の設定
Railwayのダッシュボードで以下の環境変数を設定：

```
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_MONTHLY_PRICE_ID=price_your_monthly_price_id
STRIPE_USAGE_PRICE_ID=price_your_usage_price_id
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret
```

### 4. データベースの設定
- RailwayでPostgreSQLアドオンを追加
- `DATABASE_URL`は自動的に設定されます

### 5. ドメインの設定
- Railwayでカスタムドメインを設定（オプション）

## ローカル開発

```bash
# 依存関係のインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# .envファイルを編集して実際の値を設定

# アプリケーションの起動
python app.py
```

## ファイル構成

```
lp/
├── app.py              # メインアプリケーション
├── requirements.txt    # Python依存関係
├── Procfile           # Railway用プロセス設定
├── runtime.txt        # Pythonバージョン指定
├── templates/         # HTMLテンプレート
├── static/           # 静的ファイル（CSS、画像）
└── README.md         # このファイル
```
