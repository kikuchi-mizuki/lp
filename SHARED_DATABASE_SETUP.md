# 異なるプロジェクト間でのPostgreSQLデータベース共有

## 概要

異なるRailwayプロジェクト間でPostgreSQLデータベースを共有する方法を説明します。

## 方法1: 共有データベース専用プロジェクトの作成

### ステップ1: 共有データベースプロジェクトの作成

```bash
# 新しいディレクトリを作成
mkdir shared-database-project
cd shared-database-project

# Railwayプロジェクトを初期化
railway init --name shared-database

# PostgreSQLデータベースを追加
railway add postgresql

# データベース接続情報を取得
railway variables
```

### ステップ2: データベース接続情報の記録

```bash
# 接続情報を確認
railway variables

# 出力例：
# DATABASE_URL=postgresql://postgres:password@containers-us-west-1.railway.app:5432/railway
# PGPASSWORD=password
# PGHOST=containers-us-west-1.railway.app
# PGPORT=5432
# PGUSER=postgres
# PGDATABASE=railway
```

**重要：** この接続情報を安全に保存してください。各プロジェクトで使用します。

### ステップ3: データベーススキーマの初期化

```bash
# データベースに接続
railway connect

# PostgreSQLに接続
psql $DATABASE_URL

# 必要なテーブルを作成
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    stripe_customer_id VARCHAR(255) UNIQUE NOT NULL,
    stripe_subscription_id VARCHAR(255) UNIQUE NOT NULL,
    line_user_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS usage_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    usage_quantity INTEGER DEFAULT 1,
    stripe_usage_record_id VARCHAR(255),
    is_free BOOLEAN DEFAULT FALSE,
    content_type VARCHAR(255),
    pending_charge BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS cancellation_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    content_type VARCHAR(255) NOT NULL,
    cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS user_states (
    id SERIAL PRIMARY KEY,
    line_user_id VARCHAR(255) UNIQUE NOT NULL,
    state VARCHAR(255),
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

# 接続を終了
\q
```

## 方法2: 各サービスプロジェクトの設定

### ステップ1: AIコレクションズメインプロジェクト

```bash
# AIコレクションズプロジェクトディレクトリに移動
cd /path/to/ai-collections-main

# Railwayプロジェクトを初期化
railway init --name ai-collections-main

# 共有データベースの接続情報を設定
railway variables set DATABASE_URL="postgresql://postgres:password@containers-us-west-1.railway.app:5432/railway"

# デプロイ
railway up
```

### ステップ2: AI予定秘書プロジェクト

```bash
# AI予定秘書プロジェクトディレクトリに移動
cd /path/to/ai-schedule-secretary

# Railwayプロジェクトを初期化
railway init --name ai-schedule-secretary

# 共有データベースの接続情報を設定
railway variables set DATABASE_URL="postgresql://postgres:password@containers-us-west-1.railway.app:5432/railway"

# デプロイ
railway up
```

### ステップ3: AI経理秘書プロジェクト

```bash
# AI経理秘書プロジェクトディレクトリに移動
cd /path/to/ai-accounting-secretary

# Railwayプロジェクトを初期化
railway init --name ai-accounting-secretary

# 共有データベースの接続情報を設定
railway variables set DATABASE_URL="postgresql://postgres:password@containers-us-west-1.railway.app:5432/railway"

# デプロイ
railway up
```

### ステップ4: AIタスクコンシェルジュプロジェクト

```bash
# AIタスクコンシェルジュプロジェクトディレクトリに移動
cd /path/to/ai-task-concierge

# Railwayプロジェクトを初期化
railway init --name ai-task-concierge

# 共有データベースの接続情報を設定
railway variables set DATABASE_URL="postgresql://postgres:password@containers-us-west-1.railway.app:5432/railway"

# デプロイ
railway up
```

## 方法3: Railwayダッシュボードでの設定

### ステップ1: 共有データベースプロジェクトの作成

1. https://railway.app にアクセス
2. "New Project" をクリック
3. "Start from scratch" を選択
4. プロジェクト名を "shared-database" に設定

### ステップ2: PostgreSQLデータベースの追加

1. プロジェクトページで "New" をクリック
2. "Database" → "PostgreSQL" を選択
3. データベースが作成される

### ステップ3: 接続情報の取得

1. PostgreSQLサービスをクリック
2. "Connect" タブを選択
3. 接続情報をコピー

### ステップ4: 各サービスプロジェクトの作成

#### 4-1. AIコレクションズメインプロジェクト

1. "New Project" をクリック
2. "Deploy from GitHub repo" を選択
3. AIコレクションズのリポジトリを選択
4. "Variables" タブで `DATABASE_URL` を設定

#### 4-2. AI予定秘書プロジェクト

1. "New Project" をクリック
2. "Deploy from GitHub repo" を選択
3. AI予定秘書のリポジトリを選択
4. "Variables" タブで `DATABASE_URL` を設定

#### 4-3. AI経理秘書プロジェクト

1. "New Project" をクリック
2. "Deploy from GitHub repo" を選択
3. AI経理秘書のリポジトリを選択
4. "Variables" タブで `DATABASE_URL` を設定

#### 4-4. AIタスクコンシェルジュプロジェクト

1. "New Project" をクリック
2. "Deploy from GitHub repo" を選択
3. AIタスクコンシェルジュのリポジトリを選択
4. "Variables" タブで `DATABASE_URL` を設定

## 接続テスト

### 1. 各プロジェクトでの接続確認

```bash
# 各プロジェクトで接続テストを実行
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
# 各プロジェクトで環境変数を確認
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

-- 書き込み権限を持つユーザーの作成
CREATE USER write_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE railway TO write_user;
GRANT USAGE ON SCHEMA public TO write_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO write_user;
```

### 2. 環境変数の暗号化

```bash
# 機密情報は暗号化して保存
railway variables set DATABASE_URL="postgresql://postgres:encrypted_password@host:port/database"
```

## 監視とログ

### 1. データベース監視

```bash
# 共有データベースプロジェクトでログを確認
railway logs --service postgresql

# 接続数を確認
railway connect
psql -c "SELECT count(*) FROM pg_stat_activity;"
```

### 2. 各サービスプロジェクトの監視

```bash
# 各プロジェクトでログを確認
railway logs --project ai-collections-main
railway logs --project ai-schedule-secretary
railway logs --project ai-accounting-secretary
railway logs --project ai-task-concierge
```

## トラブルシューティング

### 1. 接続エラー

**症状：** `connection refused` エラー
**対処法：**
```bash
# 共有データベースプロジェクトの状態を確認
railway logs --project shared-database

# 接続情報を再確認
railway variables --project shared-database
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

### 3. プロジェクト間の通信エラー

**症状：** 異なるプロジェクト間でデータが同期されない
**対処法：**
```bash
# 各プロジェクトの環境変数を確認
railway variables --project ai-collections-main
railway variables --project ai-schedule-secretary
railway variables --project ai-accounting-secretary
railway variables --project ai-task-concierge

# 接続情報が同じであることを確認
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
# 共有データベースプロジェクトでバックアップを作成
railway connect --project shared-database
pg_dump $DATABASE_URL > backup.sql

# 圧縮して保存
gzip backup.sql
```

### 2. データベースの復旧

```bash
# バックアップから復旧
railway connect --project shared-database
psql $DATABASE_URL < backup.sql
```

## 今後の拡張

### 1. レプリケーション

```bash
# 読み取り専用レプリカの作成
railway add postgresql --name postgresql-replica --project shared-database
```

### 2. 自動スケーリング

```bash
# データベースの自動スケーリング設定
railway variables set AUTO_SCALE=true --project shared-database
```

### 3. 監視アラート

```bash
# 監視アラートの設定
railway variables set ALERT_EMAIL=admin@example.com --project shared-database
``` 