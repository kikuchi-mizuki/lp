# 汎用解約制限システム 要件定義書

## 1. プロジェクト概要

### 1.1 プロジェクト名
汎用解約制限システム（Universal Subscription Restriction System）

### 1.2 目的
AIコレクションズの各コンテンツ（AI経理秘書、AI予定秘書、AIタスクコンシェルジュ等）において、解約済みユーザーがサービスを利用できないように制限し、AIコレクションズ公式LINEとWEBサイトへの誘導を行う汎用的なシステムを構築する。

### 1.3 背景
- AIコレクションズは複数のAIコンテンツを提供している
- 各コンテンツは独立したサービスとして運営されている
- ユーザーが解約しても、個別のコンテンツでサービスを利用できてしまう
- 解約情報を共有データベースで管理し、全コンテンツでリアルタイム制限をかける必要がある

### 1.4 対象ユーザー
- AIコレクションズの全コンテンツ利用者
- 解約済みユーザー
- アクティブユーザー

### 1.5 対象コンテンツ
- AI経理秘書
- AI予定秘書
- AIタスクコンシェルジュ
- その他AIコレクションズで提供する全コンテンツ

## 2. システム要件

### 2.1 機能要件

#### 2.1.1 汎用解約制限チェック機能
**機能名：** 汎用リアルタイム解約制限チェック
**概要：** 任意のコンテンツでユーザーアクセス時に、`subscription_periods`テーブルで解約履歴をチェックする

**詳細仕様：**
- 入力：LINEユーザーID、コンテンツタイプ（オプション）
- 処理：
  1. `users`テーブルでLINEユーザーIDからユーザーIDを取得
  2. `subscription_periods`テーブルでサブスクリプション状態を確認
  3. 解約されているかどうかを判定
- 出力：利用可能/不可の判定結果
- 実行タイミング：コンテンツアクセス時

**判定ロジック：**
```sql
-- 1. ユーザーIDを取得
SELECT id FROM users WHERE line_user_id = ?

-- 2. subscription_periodsテーブルでサブスクリプション状態をチェック
SELECT subscription_status FROM subscription_periods 
WHERE user_id = ? AND stripe_subscription_id IS NOT NULL
ORDER BY created_at DESC
LIMIT 1

-- 3. 解約されているかどうかを判定
if subscription_status in ['canceled', 'incomplete', 'incomplete_expired', 'unpaid', 'past_due']:
    return True  # 解約済み（利用不可）
elif subscription_status in ['active', 'trialing']:
    return False  # 利用可能
else:
    return True  # レコードが存在しない場合は解約済みとみなす
```

**解約制限の判定基準：**
- **利用不可（制限対象）**：
  - `canceled` - 解約済み（期間終了後）
  - `incomplete` - 支払い未完了
  - `incomplete_expired` - 支払い期限切れ
  - `unpaid` - 未払い
  - `past_due` - 支払い遅延
  - レコードが存在しない場合

- **利用可能**：
  - `active` - アクティブ（解約後も期限内であれば利用可能）
  - `trialing` - トライアル期間中

#### 2.1.2 汎用制限メッセージ生成機能
**機能名：** 汎用解約制限メッセージ生成
**概要：** 利用できないユーザーに制限メッセージを生成する

**詳細仕様：**
- メッセージ形式：LINE Button Template（LINE Bot用）、HTML（Web用）、JSON（API用）
- 内容：
  - タイトル：「AIコレクションズの利用制限」
  - 本文：「AIコレクションズは解約されているため利用できません。公式LINEまたはWEBサイトで再度ご登録いただき、サービスをご利用ください。」
  - ボタン1：「AIコレクションズ公式LINE」（URL: https://line.me/R/ti/p/@ai_collections）
  - ボタン2：「WEBサイト」（URL: https://ai-collections.herokuapp.com/）

#### 2.1.3 コンテンツ別制限機能
**機能名：** コンテンツ別アクセス制御
**概要：** 特定のコンテンツのみ制限する場合の機能

**詳細仕様：**
- コンテンツタイプによる制限の有無を設定可能
- 全コンテンツ制限とコンテンツ別制限の切り替え
- 制限対象コンテンツの設定管理

### 2.2 非機能要件

#### 2.2.1 性能要件
- 解約制限チェック応答時間：1秒以内
- データベース接続タイムアウト：3秒
- 同時接続数：1000ユーザーまで対応
- API応答時間：500ms以内

#### 2.2.2 可用性要件
- システム稼働率：99.9%以上
- データベース接続エラー時は制限しない（サービス継続）
- メンテナンス時間：月1回、1時間以内
- 自動フェイルオーバー機能

#### 2.2.3 セキュリティ要件
- データベース接続情報の暗号化
- API認証（JWT、API Key）
- ログの適切な管理
- レート制限機能
- CORS設定

#### 2.2.4 保守性要件
- ログ出力による動作監視
- エラーハンドリングの実装
- 設定変更の容易性
- モニタリング・アラート機能
- 自動デプロイメント

## 3. システム構成

### 3.1 アーキテクチャ
```
各コンテンツ（AI経理秘書、AI予定秘書、AIタスクコンシェルジュ等）
    ↓
汎用解約制限チェックAPI
    ↓
共有PostgreSQLデータベース
    ↓
usersテーブル + subscription_periodsテーブル
```

### 3.2 データベース構成
**共有PostgreSQLデータベース**
- テーブル：`users`
  - カラム：
    - `id`: 主キー
    - `email`: メールアドレス
    - `line_user_id`: LINEユーザーID
    - `stripe_customer_id`: Stripe顧客ID
    - `stripe_subscription_id`: StripeサブスクリプションID
    - `created_at`: 作成日時
    - `updated_at`: 更新日時

- テーブル：`subscription_periods`
  - カラム：
    - `id`: 主キー
    - `user_id`: ユーザーID（usersテーブルへの外部キー）
    - `stripe_subscription_id`: StripeサブスクリプションID
    - `subscription_status`: サブスクリプション状態
    - `current_period_start`: 現在の期間開始日
    - `current_period_end`: 現在の期間終了日
    - `trial_start`: トライアル開始日
    - `trial_end`: トライアル終了日
    - `created_at`: 作成日時
    - `updated_at`: 更新日時

### 3.3 外部連携
- **AIコレクションズメインアプリ**: ユーザー管理・コンテンツ管理
- **共有PostgreSQLデータベース**: ユーザー情報・解約履歴の参照
- **各コンテンツサービス**: 制限チェックAPIの呼び出し
- **AIコレクションズ公式LINE**: https://line.me/R/ti/p/@ai_collections
- **AIコレクションズWEBサイト**: https://ai-collections.herokuapp.com/

## 4. 実装仕様

### 4.1 技術スタック
- **プログラミング言語**: Python
- **フレームワーク**: Flask/FastAPI
- **データベース**: PostgreSQL
- **外部API**: RESTful API
- **ライブラリ**: requests, psycopg2-binary, sqlalchemy
- **認証**: JWT, API Key
- **デプロイ**: Docker, Railway

### 4.2 ファイル構成
```
universal-restriction-system/
├── app.py                    # メインアプリケーション
├── requirements.txt          # 依存関係
├── .env                      # 環境変数
├── Dockerfile               # Docker設定
├── api/
│   ├── __init__.py
│   ├── routes.py            # APIルート
│   └── middleware.py        # 認証・制限チェック
├── services/
│   ├── __init__.py
│   ├── restriction_service.py  # 制限チェックサービス
│   ├── user_service.py         # ユーザーサービス
│   └── message_service.py      # メッセージ生成サービス
├── models/
│   ├── __init__.py
│   ├── user.py              # ユーザーモデル
│   └── subscription.py      # サブスクリプションモデル
├── utils/
│   ├── __init__.py
│   ├── database.py          # データベース接続
│   └── logger.py            # ログ機能
└── tests/
    ├── __init__.py
    ├── test_restriction.py  # 制限チェックテスト
    └── test_api.py          # APIテスト
```

### 4.3 主要関数

#### 4.3.1 汎用解約制限チェック関数
```python
def check_user_restriction(line_user_id, content_type=None):
    """ユーザーの利用制限をチェック"""
    # 1. ユーザーIDを取得
    # 2. 解約履歴をチェック
    # 3. コンテンツ別制限チェック（オプション）
    # 4. 制限判定を返す
```

#### 4.3.2 制限メッセージ生成関数
```python
def generate_restriction_message(format_type="line"):
    """制限メッセージを生成"""
    # format_type: "line", "web", "json"
    # フォーマット別にメッセージを生成
```

#### 4.3.3 API認証関数
```python
def authenticate_api_request(request):
    """APIリクエストの認証"""
    # JWTまたはAPI Keyによる認証
```

### 4.4 環境変数
```bash
DATABASE_URL=postgresql://postgres:password@host:port/database
AI_COLLECTIONS_LINE_URL=https://line.me/R/ti/p/@ai_collections
AI_COLLECTIONS_WEB_URL=https://ai-collections.herokuapp.com/
API_SECRET_KEY=your_api_secret_key
JWT_SECRET_KEY=your_jwt_secret_key
LOG_LEVEL=INFO
ENVIRONMENT=production
```

## 5. API仕様

### 5.1 制限チェックAPI
```
POST /api/v1/restriction/check
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>

Request:
{
    "line_user_id": "U1234567890abcdef",
    "content_type": "accounting" // オプション
}

Response:
{
    "is_restricted": true,
    "subscription_status": "canceled",
    "message": "解約済みのため利用できません",
    "redirect_url": "https://line.me/R/ti/p/@ai_collections"
}
```

### 5.2 制限メッセージ取得API
```
GET /api/v1/restriction/message?format=line
Authorization: Bearer <JWT_TOKEN>

Response:
{
    "message": {
        "type": "template",
        "altText": "AIコレクションズの利用制限",
        "template": {
            "type": "buttons",
            "title": "AIコレクションズ",
            "text": "決済済みユーザーのみご利用いただけます...",
            "actions": [...]
        }
    }
}
```

### 5.3 ユーザー情報取得API
```
GET /api/v1/users/{line_user_id}
Authorization: Bearer <JWT_TOKEN>

Response:
{
    "user_id": 123,
    "email": "user@example.com",
    "subscription_status": "active",
    "is_restricted": false
}
```

### 5.4 ヘルスチェックAPI
```
GET /api/v1/health

Response:
{
    "status": "healthy",
    "database": "connected",
    "timestamp": "2024-12-19T10:00:00Z"
}
```

## 6. コンテンツ側での実装例

### 6.1 LINE Botでの実装例
```python
from universal_restriction import check_user_restriction, generate_restriction_message

def handle_message(event):
    line_user_id = event['source']['userId']
    
    # 制限チェック
    restriction_result = check_user_restriction(line_user_id, "accounting")
    
    if restriction_result['is_restricted']:
        # 制限メッセージを送信
        restriction_message = generate_restriction_message("line")
        send_line_message(event['replyToken'], [restriction_message])
        return
    
    # 通常のサービス処理
    process_normal_service(event)
```

### 6.2 Webアプリケーションでの実装例
```python
from universal_restriction import check_user_restriction, generate_restriction_message

@app.route('/accounting')
def accounting_page():
    line_user_id = session.get('line_user_id')
    
    if not line_user_id:
        return redirect('/login')
    
    # 制限チェック
    restriction_result = check_user_restriction(line_user_id, "accounting")
    
    if restriction_result['is_restricted']:
        # 制限ページを表示
        restriction_message = generate_restriction_message("web")
        return render_template('restriction.html', message=restriction_message)
    
    # 通常のページを表示
    return render_template('accounting.html')
```

### 6.3 APIでの実装例
```python
import requests

def check_restriction_api(line_user_id, content_type):
    response = requests.post(
        'https://restriction-api.railway.app/api/v1/restriction/check',
        json={
            'line_user_id': line_user_id,
            'content_type': content_type
        },
        headers={
            'Authorization': f'Bearer {API_TOKEN}',
            'Content-Type': 'application/json'
        }
    )
    
    return response.json()
```

## 7. 実装状況

### 7.1 完了済み機能
✅ **データベース構造**
- `subscription_periods`テーブルの作成
- インデックスの作成
- Railway PostgreSQLでの動作確認

✅ **解約制限チェック機能**
- `check_user_restriction`関数の実装
- サブスクリプション状態の確認ロジック
- エラーハンドリング

✅ **制限メッセージ機能**
- 制限メッセージの生成
- 複数フォーマット対応（LINE、Web、JSON）
- AIコレクションズへの誘導リンク

✅ **統合システム**
- AIコレクションズメインアプリとの連携
- 解約処理時のサブスクリプション状態更新
- 複数サービス対応

### 7.2 実装済みAPI
✅ **利用制限チェックAPI**
```
POST /api/v1/restriction/check
```

✅ **制限メッセージ取得API**
```
GET /api/v1/restriction/message
```

✅ **ユーザー情報取得API**
```
GET /api/v1/users/{line_user_id}
```

✅ **ヘルスチェックAPI**
```
GET /api/v1/health
```

### 7.3 実装済みサービス
✅ **restriction_service.py**
- サブスクリプション状態のチェック
- 解約状態の判定
- コンテンツ別制限チェック

✅ **user_service.py**
- ユーザー情報の取得
- LINEユーザーIDの管理
- 認証機能

✅ **message_service.py**
- 制限メッセージの生成
- 複数フォーマット対応
- 多言語対応（将来拡張）

## 8. テスト仕様

### 8.1 単体テスト
- 解約制限チェック機能のテスト
- 制限メッセージ生成機能のテスト
- データベース接続機能のテスト
- API認証機能のテスト

### 8.2 統合テスト
- 解約済みユーザーでの制限動作確認
- アクティブユーザーでの通常動作確認
- エラー時のフォールバック動作確認
- API連携テスト

### 8.3 ユーザーシナリオテスト
**シナリオ1: 未登録ユーザー**
1. 未登録ユーザーが任意のコンテンツにアクセス
2. 制限メッセージが表示される
3. AIコレクションズ公式LINEとWEBサイトへの誘導が正常に動作

**シナリオ2: 解約済みユーザー（期間終了後）**
1. 解約済みユーザーが任意のコンテンツにアクセス
2. `subscription_periods`テーブルでサブスクリプション状態が`canceled`であることを確認
3. 制限メッセージが表示される
4. AIコレクションズ公式LINEとWEBサイトへの誘導が正常に動作

**シナリオ3: アクティブユーザー**
1. アクティブユーザーが任意のコンテンツにアクセス
2. `subscription_periods`テーブルでサブスクリプション状態が`active`であることを確認
3. 通常のサービスが提供される
4. 制限メッセージは表示されない

**シナリオ4: 解約後も期限内のユーザー**
1. 解約後も期限内のユーザーが任意のコンテンツにアクセス
2. `subscription_periods`テーブルでサブスクリプション状態が`active`であることを確認
3. 通常のサービスが提供される（期限内のため利用可能）
4. 制限メッセージは表示されない

**シナリオ5: データベース接続エラー**
1. データベース接続エラーが発生
2. 制限チェックをスキップして通常サービスを提供
3. エラーログが記録される

**シナリオ6: API認証エラー**
1. 無効なAPI認証情報でリクエスト
2. 401エラーが返される
3. セキュリティログが記録される

## 9. 運用・保守

### 9.1 監視項目
- データベース接続状況
- 解約制限チェックの実行回数
- API応答時間
- エラー発生率
- 認証失敗率

### 9.2 ログ管理
- アプリケーションログ
- 制限チェックログ
- APIアクセスログ
- エラーログ
- セキュリティログ
- データベース接続ログ

### 9.3 バックアップ
- データベースの定期バックアップ
- 設定ファイルのバックアップ
- ログファイルのアーカイブ
- コードのバージョン管理

### 9.4 アラート設定
- データベース接続エラー
- API応答時間超過
- エラー率の閾値超過
- 認証失敗の異常増加

## 10. リスク・対策

### 10.1 技術リスク
**リスク**: データベース接続エラー
**対策**: エラー時のフォールバック処理を実装済み

**リスク**: API応答遅延
**対策**: タイムアウト設定とリトライ機能を実装済み

**リスク**: サブスクリプション状態の同期遅延
**対策**: リアルタイムでのサブスクリプション状態更新を実装済み

**リスク**: API認証の漏洩
**対策**: JWTトークンの有効期限設定、API Keyの定期更新

### 10.2 運用リスク
**リスク**: 誤ってアクティブユーザーを制限
**対策**: ログ監視とアラート機能を実装済み

**リスク**: ユーザー情報の同期遅延
**対策**: 定期的なデータ整合性チェックを実装済み

**リスク**: 大量アクセスによる負荷
**対策**: レート制限機能とスケーリング機能を実装済み

## 11. 成功指標

### 11.1 定量的指標
- 解約制限チェック成功率: 99.9%以上
- 平均応答時間: 1秒以内
- API応答時間: 500ms以内
- エラー発生率: 0.1%以下
- システム稼働率: 99.9%以上

### 11.2 定性的指標
- 解約済みユーザーの適切な制限
- アクティブユーザーのサービス継続
- ユーザー体験の向上
- セキュリティの向上
- 運用効率の向上

## 12. 今後の拡張

### 12.1 短期拡張（3ヶ月以内）
- 詳細な利用統計の実装
- 自動復旧機能の強化
- 管理者ダッシュボードの実装
- 多言語対応

### 12.2 中期拡張（6ヶ月以内）
- リアルタイム通知機能
- 高度な分析機能
- マルチリージョン対応
- 機械学習による異常検知

### 12.3 長期拡張（1年以内）
- 自動スケーリング機能
- 高度なセキュリティ機能
- マイクロサービス化
- クラウドネイティブ対応

## 13. 承認・承認者

### 13.1 承認者
- プロジェクトマネージャー: [承認者名]
- 技術責任者: [承認者名]
- 運用責任者: [承認者名]

### 13.2 承認日
- 要件定義書承認日: [日付]
- 実装開始日: 2024年12月19日
- 本番リリース日: 2024年12月19日

---

**文書作成日**: 2024年12月19日  
**文書バージョン**: 5.0  
**作成者**: AI Assistant  
**最終更新日**: 2024年12月19日  
**更新内容**: 汎用解約制限システムとして、AI経理秘書以外のコンテンツにも対応し、コンテンツ側に組み込むための要件定義書に完全改訂 