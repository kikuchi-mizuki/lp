# スプレッドシート連携コンテンツ管理システム セットアップガイド

## 概要

このシステムにより、Google Sheetsでコンテンツ情報を管理し、動的にコンテンツの追加・解約が可能になります。

## セットアップ手順

### 1. Google Sheets API設定

#### 1.1 Google Cloud Consoleでプロジェクト作成
1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成
3. Google Sheets APIを有効化

#### 1.2 サービスアカウント作成
1. 「IAMと管理」→「サービスアカウント」を選択
2. 「サービスアカウントを作成」をクリック
3. アカウント名を入力（例：`content-management-service`）
4. 「キーを作成」→「JSON」を選択
5. ダウンロードしたJSONファイルを`credentials.json`として保存

#### 1.3 スプレッドシート作成
1. [Google Sheets](https://sheets.google.com/)で新しいスプレッドシートを作成
2. 以下のヘッダー行を追加：

| コンテンツID | コンテンツ名 | 説明 | 追加後のURL | 料金 | ステータス | 作成日 | 機能 |
|-------------|-------------|------|------------|------|----------|--------|------|
| ai_accounting | AI経理秘書 | 経理作業をAIが効率化 | https://lp-production-9e2c.up.railway.app/accounting | 2980 | active | 2024-01-01 | 自動仕訳,帳簿作成,税務申告,経営分析 |
| ai_schedule | AI予定秘書 | スケジュール管理をAIがサポート | https://lp-production-9e2c.up.railway.app/schedule | 1980 | active | 2024-01-01 | スケジュール管理,会議調整,リマインダー,タスク管理 |
| ai_task | AIタスクコンシェルジュ | タスク管理をAIが最適化 | https://lp-production-9e2c.up.railway.app/task | 2480 | active | 2024-01-01 | タスク管理,プロジェクト管理,進捗追跡,チーム連携 |

#### 1.4 スプレッドシートの共有設定
1. スプレッドシートの「共有」ボタンをクリック
2. サービスアカウントのメールアドレスを追加
3. 「編集者」権限を付与

### 2. 環境変数設定

#### 2.1 Railway環境変数設定
```bash
# スプレッドシートID（URLから取得）
CONTENT_SPREADSHEET_ID=your_spreadsheet_id_here

# Google認証情報（JSONファイルの内容をそのまま設定）
GOOGLE_CREDENTIALS_JSON={"type":"service_account","project_id":"your-project-id",...}
```

#### 2.2 ローカル開発環境
```bash
# .envファイルに追加
CONTENT_SPREADSHEET_ID=your_spreadsheet_id_here
GOOGLE_CREDENTIALS_FILE=credentials.json
```

### 3. 依存関係インストール

```bash
pip install gspread google-auth google-auth-oauthlib google-auth-httplib2
```

### 4. アプリケーション設定

#### 4.1 新しいルートを追加
`app.py`に以下を追加：

```python
from routes.content_admin import content_admin_bp
app.register_blueprint(content_admin_bp)
```

#### 4.2 サービスインポート更新
既存のサービスファイルでスプレッドシートサービスを使用：

```python
from services.spreadsheet_content_service import spreadsheet_content_service
```

### 5. テスト実行

```bash
python test_spreadsheet_content_system.py
```

## 使用方法

### 1. コンテンツ追加

#### 1.1 スプレッドシートで直接追加
1. スプレッドシートに新しい行を追加
2. 必要な情報を入力
3. ステータスを`active`に設定

#### 1.2 API経由で追加
```bash
curl -X POST http://your-domain.com/api/v1/content/add \
  -H "Content-Type: application/json" \
  -d '{
    "id": "ai_marketing",
    "name": "AIマーケティングアシスタント",
    "description": "マーケティング戦略をAIが最適化",
    "url": "https://example.com/marketing",
    "price": 3980,
    "features": ["SNS分析", "競合分析", "キャンペーン最適化"]
  }'
```

### 2. コンテンツ無効化

#### 2.1 スプレッドシートで直接変更
1. 対象コンテンツの「ステータス」列を`inactive`に変更

#### 2.2 API経由で変更
```bash
curl -X PUT http://your-domain.com/api/v1/content/ai_marketing/status \
  -H "Content-Type: application/json" \
  -d '{"status": "inactive"}'
```

### 3. キャッシュ更新

```bash
curl -X POST http://your-domain.com/api/v1/content/refresh
```

## API エンドポイント

### コンテンツ一覧取得
```
GET /api/v1/content/list
```

### 特定コンテンツ情報取得
```
GET /api/v1/content/{content_id}
```

### 新規コンテンツ追加
```
POST /api/v1/content/add
```

### コンテンツステータス更新
```
PUT /api/v1/content/{content_id}/status
```

### キャッシュ更新
```
POST /api/v1/content/refresh
```

### 健全性チェック
```
GET /api/v1/content/health
```

### データベース同期
```
POST /api/v1/content/sync
```

## トラブルシューティング

### 1. スプレッドシート接続エラー
- サービスアカウントの権限を確認
- スプレッドシートIDが正しいか確認
- 認証情報JSONが正しく設定されているか確認

### 2. キャッシュ問題
- `/api/v1/content/refresh`でキャッシュを強制更新
- アプリケーションを再起動

### 3. フォールバックモード
- スプレッドシートが利用できない場合、デフォルトコンテンツが使用される
- ログでフォールバックモードの確認が可能

## 監視とログ

### 1. 健全性チェック
```bash
curl http://your-domain.com/api/v1/content/health
```

### 2. ログ確認
```bash
# Railwayログ
railway logs

# アプリケーションログ
tail -f app.log
```

## セキュリティ考慮事項

1. **認証情報の管理**
   - サービスアカウントキーは環境変数で管理
   - 本番環境では適切な権限設定

2. **アクセス制御**
   - APIエンドポイントに認証を追加することを推奨
   - 管理者専用エンドポイントの保護

3. **データ検証**
   - 入力データの検証
   - SQLインジェクション対策

## 今後の拡張

1. **Webhook連携**
   - スプレッドシート変更時の自動通知
   - リアルタイム同期

2. **バージョン管理**
   - コンテンツ変更履歴
   - ロールバック機能

3. **多言語対応**
   - コンテンツ説明の多言語化
   - 地域別料金設定

4. **分析機能**
   - コンテンツ利用統計
   - 人気コンテンツ分析
