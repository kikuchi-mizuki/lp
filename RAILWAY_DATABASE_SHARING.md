# Railway PostgreSQLデータベース共有ガイド

## 概要

RailwayでPostgreSQLデータベースを複数のサービスで共有する方法を説明します。

## 方法1: 同じプロジェクト内での共有（推奨）

### ステップ1: Railway CLIのインストール

```bash
# npmを使用
npm install -g @railway/cli

# または yarnを使用
yarn global add @railway/cli
```

### ステップ2: Railwayにログイン

```bash
railway login
```

### ステップ3: プロジェクトの初期化

```bash
# プロジェクトディレクトリで実行
railway init
```

### ステップ4: PostgreSQLデータベースの作成

```bash
# PostgreSQLデータベースを作成
railway add postgresql

# データベース情報を確認
railway variables
```

### ステップ5: データベース接続情報の取得

```bash
# データベース接続情報を表示
railway variables

# 出力例：
# DATABASE_URL=postgresql://postgres:password@containers-us-west-1.railway.app:5432/railway
# PGPASSWORD=password
# PGHOST=containers-us-west-1.railway.app
# PGPORT=5432
# PGUSER=postgres
# PGDATABASE=railway
```

### ステップ6: 複数サービスの作成

#### 6-1. メインアプリ（AIコレクションズ）

```bash
# メインアプリをデプロイ
railway up
```

#### 6-2. AI予定秘書アプリ

```bash
# schedule-serviceディレクトリに移動
cd schedule-service

# 新しいサービスを作成
railway service create ai-schedule-secretary

# 同じプロジェクトに追加
railway link --project your-project-id

# 同じデータベースを使用するように設定
railway variables set DATABASE_URL="postgresql://postgres:password@containers-us-west-1.railway.app:5432/railway"

# デプロイ
railway up
```

#### 6-3. AI経理秘書アプリ

```bash
# accounting-serviceディレクトリに移動
cd ../accounting-service

# 新しいサービスを作成
railway service create ai-accounting-secretary

# 同じプロジェクトに追加
railway link --project your-project-id

# 同じデータベースを使用するように設定
railway variables set DATABASE_URL="postgresql://postgres:password@containers-us-west-1.railway.app:5432/railway"

# デプロイ
railway up
```

#### 6-4. AIタスクコンシェルジュアプリ

```bash
# task-serviceディレクトリに移動
cd ../task-service

# 新しいサービスを作成
railway service create ai-task-concierge

# 同じプロジェクトに追加
railway link --project your-project-id

# 同じデータベースを使用するように設定
railway variables set DATABASE_URL="postgresql://postgres:password@containers-us-west-1.railway.app:5432/railway"

# デプロイ
railway up
```

## 方法2: 異なるプロジェクト間での共有

### ステップ1: 共有データベースプロジェクトの作成

```bash
# 新しいプロジェクトを作成
railway init --name shared-database

# PostgreSQLデータベースを追加
railway add postgresql

# データベース接続情報を取得
railway variables
```

### ステップ2: 各サービスプロジェクトの作成

#### 2-1. AIコレクションズメインプロジェクト

```bash
# 新しいプロジェクトを作成
railway init --name ai-collections-main

# 共有データベースの接続情報を設定
railway variables set DATABASE_URL="postgresql://postgres:password@containers-us-west-1.railway.app:5432/railway"

# デプロイ
railway up
```

#### 2-2. AI予定秘書プロジェクト

```bash
# 新しいプロジェクトを作成
railway init --name ai-schedule-secretary

# 共有データベースの接続情報を設定
railway variables set DATABASE_URL="postgresql://postgres:password@containers-us-west-1.railway.app:5432/railway"

# デプロイ
railway up
```

#### 2-3. AI経理秘書プロジェクト

```bash
# 新しいプロジェクトを作成
railway init --name ai-accounting-secretary

# 共有データベースの接続情報を設定
railway variables set DATABASE_URL="postgresql://postgres:password@containers-us-west-1.railway.app:5432/railway"

# デプロイ
railway up
```

#### 2-4. AIタスクコンシェルジュプロジェクト

```bash
# 新しいプロジェクトを作成
railway init --name ai-task-concierge

# 共有データベースの接続情報を設定
railway variables set DATABASE_URL="postgresql://postgres:password@containers-us-west-1.railway.app:5432/railway"

# デプロイ
railway up
```

## 方法3: Railwayダッシュボードでの設定

### ステップ1: Railwayダッシュボードにアクセス

1. https://railway.app にアクセス
2. アカウントにログイン

### ステップ2: プロジェクトの作成

1. "New Project" をクリック
2. "Deploy from GitHub repo" を選択
3. リポジトリを選択

### ステップ3: PostgreSQLデータベースの追加

1. プロジェクトページで "New" をクリック
2. "Database" → "PostgreSQL" を選択
3. データベースが作成される

### ステップ4: 複数サービスの追加

1. "New" → "Service" → "GitHub Repo" を選択
2. 各サービスのリポジトリを追加
3. 各サービスで同じデータベースの接続情報を設定

## データベース接続の確認

### 1. 接続テスト

```bash
# データベースに接続してテスト
railway connect

# PostgreSQLに接続
psql $DATABASE_URL

# テーブル一覧を確認
\dt

# 接続を終了
\q
```

### 2. 環境変数の確認

```bash
# 各サービスで環境変数を確認
railway variables

# 出力例：
# DATABASE_URL=postgresql://postgres:password@containers-us-west-1.railway.app:5432/railway
```

## セキュリティ設定

### 1. データベースアクセス制限

```sql
-- 読み取り専用ユーザーの作成（推奨）
CREATE USER readonly_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE railway TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
```

### 2. 環境変数の暗号化

```bash
# 機密情報は暗号化して保存
railway variables set DATABASE_URL="postgresql://postgres:encrypted_password@host:port/database"
```

## 監視とログ

### 1. データベース監視

```bash
# データベースの状態を確認
railway logs --service postgresql

# 接続数を確認
railway connect
psql -c "SELECT count(*) FROM pg_stat_activity;"
```

### 2. サービス監視

```bash
# 各サービスのログを確認
railway logs --service ai-schedule-secretary
railway logs --service ai-accounting-secretary
railway logs --service ai-task-concierge
```

## トラブルシューティング

### 1. 接続エラー

**症状：** `connection refused` エラー
**対処法：**
```bash
# データベースの状態を確認
railway logs --service postgresql

# 接続情報を再確認
railway variables
```

### 2. 権限エラー

**症状：** `permission denied` エラー
**対処法：**
```sql
-- データベースに接続して権限を確認
\du

-- 必要に応じて権限を付与
GRANT ALL PRIVILEGES ON DATABASE railway TO postgres;
```

### 3. 容量不足

**症状：** `disk full` エラー
**対処法：**
```bash
# データベースサイズを確認
railway connect
psql -c "SELECT pg_size_pretty(pg_database_size('railway'));"

# 不要なデータを削除
psql -c "VACUUM FULL;"
```

## コスト最適化

### 1. データベースサイズの監視

```sql
-- テーブルサイズを確認
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 2. 接続数の最適化

```python
# 接続プールの設定
import psycopg2
from psycopg2 import pool

# 接続プールを作成
connection_pool = psycopg2.pool.SimpleConnectionPool(
    1,  # 最小接続数
    10, # 最大接続数
    DATABASE_URL
)
```

## バックアップと復旧

### 1. データベースのバックアップ

```bash
# バックアップを作成
railway connect
pg_dump $DATABASE_URL > backup.sql

# 圧縮して保存
gzip backup.sql
```

### 2. データベースの復旧

```bash
# バックアップから復旧
railway connect
psql $DATABASE_URL < backup.sql
```

## 今後の拡張

### 1. レプリケーション

```bash
# 読み取り専用レプリカの作成
railway add postgresql --name postgresql-replica
```

### 2. 自動スケーリング

```bash
# データベースの自動スケーリング設定
railway variables set AUTO_SCALE=true
```

### 3. 監視アラート

```bash
# 監視アラートの設定
railway variables set ALERT_EMAIL=admin@example.com
``` 