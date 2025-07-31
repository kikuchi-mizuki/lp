# Railwayトークン設定ガイド

## 問題
企業登録後に「Railwayトークンが設定されていません」エラーが発生しています。

## 解決方法

### 1. Railwayトークンの取得

1. **Railwayダッシュボードにログイン**
   - https://railway.app/dashboard

2. **APIトークンの生成**
   - 右上のプロフィールアイコンをクリック
   - "Account Settings"を選択
   - "API"タブをクリック
   - "Generate Token"をクリック
   - トークン名を入力（例: "LINE Bot Deployment"）
   - "Generate"をクリック

3. **トークンをコピー**
   - 生成されたトークンを安全な場所に保存

### 2. Railway環境変数の設定

#### 方法A: Railwayダッシュボードから設定

1. **プロジェクトを開く**
   - https://railway.app/dashboard
   - `lp-production-9e2c`プロジェクトを選択

2. **環境変数を追加**
   - "Variables"タブをクリック
   - "New Variable"をクリック
   - 以下の変数を追加:

```
RAILWAY_TOKEN=your_railway_token_here
RAILWAY_PROJECT_ID=your_project_id_here
BASE_DOMAIN=lp-production-9e2c.up.railway.app
```

#### 方法B: Railway CLIから設定

```bash
# Railway CLIをインストール
npm install -g @railway/cli

# ログイン
railway login

# プロジェクトを選択
railway link

# 環境変数を設定
railway variables set RAILWAY_TOKEN=your_railway_token_here
railway variables set RAILWAY_PROJECT_ID=your_project_id_here
railway variables set BASE_DOMAIN=lp-production-9e2c.up.railway.app
```

### 3. プロジェクトIDの取得

1. **Railwayダッシュボードでプロジェクトを開く**
2. **URLからプロジェクトIDを確認**
   - 例: `https://railway.app/project/3e9475ce-ff6a-4443-ab6c-4eb21b7f4017`
   - プロジェクトID: `3e9475ce-ff6a-4443-ab6c-4eb21b7f4017`

### 4. 設定後の確認

環境変数設定後、以下のテストを実行:

```bash
python test_railway_clone_and_link.py
```

### 5. トラブルシューティング

**よくある問題:**

1. **トークンが無効**
   - トークンを再生成
   - 権限を確認

2. **プロジェクトIDが間違っている**
   - 正しいプロジェクトIDを確認
   - URLからIDを取得

3. **環境変数が反映されていない**
   - Railwayアプリを再デプロイ
   - 数分待ってから再試行

## 設定完了後の動作

1. **企業登録**
   - 企業情報を入力
   - LINE認証情報を設定

2. **自動デプロイ**
   - Railwayプロジェクトが自動複製
   - LINE環境変数が自動設定
   - デプロイが開始

3. **完了確認**
   - 企業専用のLINEボットが稼働
   - 設定情報が正しく表示

## セキュリティ注意事項

- Railwayトークンは機密情報です
- 公開リポジトリにコミットしない
- 定期的にトークンを更新
- 必要最小限の権限を付与 