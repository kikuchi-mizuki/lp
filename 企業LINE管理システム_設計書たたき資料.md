# 企業ごとの公式LINEアカウント管理システム 設計書たたき資料

## 1. プロジェクト概要

### 1.1 プロジェクト名
企業ごとの公式LINEアカウント管理システム（Enterprise LINE Account Management System）

### 1.2 目的
- 企業ごとに専用の公式LINEアカウントを自動作成・管理
- Stripe決済情報と企業情報の統合管理
- 企業ごとのコンテンツ利用状況の一元管理
- 解約時の自動データ削除と制限機能
- 企業向け通知・アラート機能の提供

### 1.3 背景
- AIコレクションズの企業向けサービス拡張
- 企業ごとの専用LINEアカウント需要の増加
- 決済・コンテンツ管理の効率化
- 運用コスト削減と自動化の実現

### 1.4 対象ユーザー
- 企業顧客（B2B）
- システム管理者
- カスタマーサポート

## 2. システム要件

### 2.1 機能要件

#### 2.1.1 企業管理機能
**機能名：** 企業情報管理
**概要：** 企業の基本情報、LINEアカウント情報、決済情報を統合管理

**詳細仕様：**
- 企業基本情報の登録・編集・削除
- 企業ごとのLINE公式アカウント情報管理
- Stripe顧客情報との紐付け
- 企業ステータス管理（アクティブ、停止、解約等）

#### 2.1.2 LINEアカウント自動作成機能
**機能名：** 自動LINEアカウント作成
**概要：** 企業登録時に専用のLINE公式アカウントを自動作成

**詳細仕様：**
- LINE Developers Console APIを使用した自動チャンネル作成
- チャンネル設定の自動化（Webhook URL、メッセージ設定等）
- 企業IDとLINEチャンネルIDの自動紐付け
- チャンネル情報のデータベース保存

#### 2.1.3 決済管理機能
**機能名：** 企業決済統合管理
**概要：** 企業ごとのStripe決済情報を統合管理

**詳細仕様：**
- 企業ごとのサブスクリプション管理
- 複数コンテンツの統合課金
- 決済履歴の自動記録
- 支払い失敗時の自動通知

#### 2.1.4 コンテンツ管理機能
**機能名：** 企業コンテンツ利用管理
**概要：** 企業が利用するコンテンツの状況を一元管理

**詳細仕様：**
- 企業ごとのコンテンツ利用状況追跡
- コンテンツ追加・削除の自動処理
- 利用制限の自動適用
- コンテンツ別の利用統計

#### 2.1.5 解約・データ削除機能
**機能名：** 自動解約処理・データ削除
**概要：** 企業解約時の自動処理とデータ削除

**詳細仕様：**
- Stripe Webhookによる解約検知
- 企業データの自動削除
- LINEアカウントの自動停止
- 解約通知の自動送信

#### 2.1.6 通知・アラート機能
**機能名：** 企業向け通知システム
**概要：** 企業向けの自動通知・アラート機能

**詳細仕様：**
- 決済関連通知（支払い完了、失敗、更新等）
- コンテンツ利用状況通知
- 解約・制限通知
- カスタマイズ可能な通知設定

### 2.2 非機能要件

#### 2.2.1 性能要件
- 企業登録処理：30秒以内
- LINEアカウント作成：60秒以内
- 決済処理：5秒以内
- 通知送信：10秒以内
- 同時処理：100企業まで対応

#### 2.2.2 可用性要件
- システム稼働率：99.9%以上
- データベース接続：99.95%以上
- 自動復旧機能
- バックアップ自動化

#### 2.2.3 セキュリティ要件
- 企業データの完全分離
- API認証（JWT、API Key）
- データ暗号化
- アクセスログ記録
- 監査証跡の保持

#### 2.2.4 保守性要件
- モジュール化された設計
- 詳細なログ出力
- 監視・アラート機能
- 設定変更の容易性

## 3. システム構成

### 3.1 アーキテクチャ
```
企業管理システム
    ↓
LINE API連携
    ↓
Stripe決済システム
    ↓
PostgreSQLデータベース
    ↓
通知システム
```

### 3.2 データベース構成

#### 3.2.1 企業管理テーブル
```sql
-- 企業基本情報テーブル
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    company_code VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    address TEXT,
    industry VARCHAR(100),
    employee_count INTEGER,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 企業LINEアカウントテーブル
CREATE TABLE company_line_accounts (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    line_channel_id VARCHAR(255) UNIQUE NOT NULL,
    line_channel_access_token VARCHAR(255) NOT NULL,
    line_channel_secret VARCHAR(255) NOT NULL,
    line_basic_id VARCHAR(255),
    line_qr_code_url VARCHAR(500),
    webhook_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- 企業決済情報テーブル
CREATE TABLE company_payments (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    stripe_customer_id VARCHAR(255) UNIQUE NOT NULL,
    stripe_subscription_id VARCHAR(255),
    subscription_status VARCHAR(50),
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    trial_start TIMESTAMP,
    trial_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- 企業コンテンツ管理テーブル
CREATE TABLE company_contents (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    content_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    line_bot_url VARCHAR(500),
    api_endpoint VARCHAR(500),
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- 企業通知設定テーブル
CREATE TABLE company_notifications (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    notification_type VARCHAR(100) NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    recipients JSONB,
    schedule VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- 企業解約履歴テーブル
CREATE TABLE company_cancellations (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    cancellation_reason VARCHAR(255),
    cancelled_by VARCHAR(100),
    data_deletion_status VARCHAR(50) DEFAULT 'pending',
    line_account_status VARCHAR(50) DEFAULT 'active',
    cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);
```

## 4. 機能詳細設計

### 4.1 企業登録フロー

#### 4.1.1 企業登録処理
```python
def register_company(company_data):
    """
    企業登録処理
    """
    # 1. 企業基本情報の登録
    company_id = create_company_profile(company_data)
    
    # 2. LINE公式アカウントの自動作成
    line_account = create_line_account(company_id, company_data)
    
    # 3. Stripe顧客の作成
    stripe_customer = create_stripe_customer(company_id, company_data)
    
    # 4. 初期コンテンツの設定
    setup_initial_contents(company_id)
    
    # 5. 通知設定の初期化
    initialize_notifications(company_id)
    
    return {
        'company_id': company_id,
        'line_account': line_account,
        'stripe_customer': stripe_customer
    }
```

#### 4.1.2 LINEアカウント作成処理
```python
def create_line_account(company_id, company_data):
    """
    LINE公式アカウント自動作成
    """
    # 1. LINE Developers Console APIでチャンネル作成
    channel_data = {
        'name': f"{company_data['company_name']} - AIコレクションズ",
        'description': f"{company_data['company_name']}専用のAIコレクションズ公式アカウント",
        'category': 'business'
    }
    
    # 2. チャンネル作成API呼び出し
    line_channel = line_api.create_channel(channel_data)
    
    # 3. Webhook URL設定
    webhook_url = f"https://api.example.com/webhook/company/{company_id}"
    line_api.set_webhook_url(line_channel['channelId'], webhook_url)
    
    # 4. データベースに保存
    save_line_account(company_id, line_channel)
    
    return line_channel
```

### 4.2 決済管理フロー

#### 4.2.1 Stripe Webhook処理
```python
def handle_stripe_webhook(event):
    """
    Stripe Webhook処理（企業対応版）
    """
    event_type = event['type']
    
    if event_type == 'customer.subscription.created':
        handle_subscription_created(event)
    elif event_type == 'customer.subscription.updated':
        handle_subscription_updated(event)
    elif event_type == 'customer.subscription.deleted':
        handle_subscription_cancelled(event)
    elif event_type == 'invoice.payment_succeeded':
        handle_payment_succeeded(event)
    elif event_type == 'invoice.payment_failed':
        handle_payment_failed(event)
```

#### 4.2.2 企業決済処理
```python
def handle_company_payment(company_id, payment_data):
    """
    企業決済処理
    """
    # 1. 決済情報の更新
    update_payment_info(company_id, payment_data)
    
    # 2. コンテンツ利用状況の更新
    update_content_usage(company_id)
    
    # 3. 通知の送信
    send_payment_notification(company_id, payment_data)
    
    # 4. 利用制限の更新
    update_usage_restrictions(company_id)
```

### 4.3 コンテンツ管理フロー

#### 4.3.1 コンテンツ追加処理
```python
def add_company_content(company_id, content_type):
    """
    企業コンテンツ追加処理
    """
    # 1. コンテンツ情報の登録
    content_id = register_content(company_id, content_type)
    
    # 2. LINE Bot連携の設定
    setup_line_bot_integration(company_id, content_type)
    
    # 3. API連携の設定
    setup_api_integration(company_id, content_type)
    
    # 4. 利用制限の設定
    setup_usage_restrictions(company_id, content_type)
    
    # 5. 通知設定の更新
    update_notification_settings(company_id, content_type)
    
    return content_id
```

#### 4.3.2 コンテンツ削除処理
```python
def remove_company_content(company_id, content_type):
    """
    企業コンテンツ削除処理
    """
    # 1. コンテンツ利用状況の確認
    usage_status = check_content_usage(company_id, content_type)
    
    # 2. LINE Bot連携の停止
    disable_line_bot_integration(company_id, content_type)
    
    # 3. API連携の停止
    disable_api_integration(company_id, content_type)
    
    # 4. 利用制限の解除
    remove_usage_restrictions(company_id, content_type)
    
    # 5. コンテンツ情報の削除
    delete_content_info(company_id, content_type)
    
    # 6. 通知設定の更新
    update_notification_settings(company_id, content_type)
```

### 4.4 解約・データ削除フロー

#### 4.4.1 解約処理
```python
def handle_company_cancellation(company_id, reason):
    """
    企業解約処理
    """
    # 1. 解約情報の記録
    record_cancellation(company_id, reason)
    
    # 2. 全コンテンツの停止
    disable_all_contents(company_id)
    
    # 3. LINEアカウントの停止
    disable_line_account(company_id)
    
    # 4. 決済の停止
    cancel_payments(company_id)
    
    # 5. 解約通知の送信
    send_cancellation_notification(company_id, reason)
    
    # 6. データ削除スケジュール設定
    schedule_data_deletion(company_id)
```

#### 4.4.2 データ削除処理
```python
def delete_company_data(company_id):
    """
    企業データ削除処理
    """
    # 1. 削除対象データの確認
    deletion_targets = identify_deletion_targets(company_id)
    
    # 2. バックアップの作成
    create_backup(company_id)
    
    # 3. 段階的データ削除
    delete_user_data(company_id)
    delete_content_data(company_id)
    delete_payment_data(company_id)
    delete_line_account_data(company_id)
    delete_company_profile(company_id)
    
    # 4. 削除完了通知
    notify_data_deletion_complete(company_id)
```

### 4.5 通知・アラートフロー

#### 4.5.1 通知送信処理
```python
def send_company_notification(company_id, notification_type, data):
    """
    企業向け通知送信処理
    """
    # 1. 通知設定の取得
    notification_settings = get_notification_settings(company_id, notification_type)
    
    # 2. 通知メッセージの生成
    message = generate_notification_message(notification_type, data)
    
    # 3. 通知チャンネルの選択
    channels = select_notification_channels(notification_settings)
    
    # 4. 各チャンネルへの送信
    for channel in channels:
        if channel == 'line':
            send_line_notification(company_id, message)
        elif channel == 'email':
            send_email_notification(company_id, message)
        elif channel == 'webhook':
            send_webhook_notification(company_id, message)
    
    # 5. 送信履歴の記録
    record_notification_history(company_id, notification_type, channels)
```

#### 4.5.2 アラート処理
```python
def handle_company_alert(company_id, alert_type, data):
    """
    企業向けアラート処理
    """
    # 1. アラート重要度の判定
    severity = determine_alert_severity(alert_type, data)
    
    # 2. アラート設定の確認
    alert_settings = get_alert_settings(company_id, alert_type)
    
    # 3. アラート条件のチェック
    if should_send_alert(alert_settings, severity):
        # 4. アラートメッセージの生成
        alert_message = generate_alert_message(alert_type, data, severity)
        
        # 5. 緊急通知の送信
        send_urgent_notification(company_id, alert_message, severity)
        
        # 6. 管理者への通知
        notify_administrators(company_id, alert_type, severity)
```

## 5. API設計

### 5.1 企業管理API

#### 5.1.1 企業登録API
```
POST /api/v1/companies
Content-Type: application/json

Request Body:
{
    "company_name": "株式会社サンプル",
    "email": "contact@sample.co.jp",
    "phone": "03-1234-5678",
    "address": "東京都渋谷区...",
    "industry": "IT",
    "employee_count": 100,
    "initial_contents": ["AI予定秘書", "AI経理秘書"]
}

Response:
{
    "status": "success",
    "company_id": 123,
    "line_account": {
        "channel_id": "U1234567890abcdef",
        "qr_code_url": "https://...",
        "webhook_url": "https://..."
    },
    "stripe_customer": {
        "customer_id": "cus_1234567890",
        "subscription_id": "sub_1234567890"
    }
}
```

#### 5.1.2 企業情報取得API
```
GET /api/v1/companies/{company_id}

Response:
{
    "status": "success",
    "company": {
        "id": 123,
        "company_name": "株式会社サンプル",
        "email": "contact@sample.co.jp",
        "status": "active",
        "line_account": {...},
        "payment_info": {...},
        "contents": [...],
        "created_at": "2024-01-01T00:00:00Z"
    }
}
```

### 5.2 LINE管理API

#### 5.2.1 LINEアカウント作成API
```
POST /api/v1/companies/{company_id}/line-accounts
Content-Type: application/json

Request Body:
{
    "channel_name": "サンプル企業 - AIコレクションズ",
    "description": "専用のAIコレクションズ公式アカウント"
}

Response:
{
    "status": "success",
    "line_account": {
        "channel_id": "U1234567890abcdef",
        "channel_access_token": "token_1234567890",
        "qr_code_url": "https://...",
        "webhook_url": "https://..."
    }
}
```

### 5.3 決済管理API

#### 5.3.1 決済状況取得API
```
GET /api/v1/companies/{company_id}/payments

Response:
{
    "status": "success",
    "payments": {
        "customer_id": "cus_1234567890",
        "subscription_id": "sub_1234567890",
        "status": "active",
        "current_period_start": "2024-01-01T00:00:00Z",
        "current_period_end": "2024-02-01T00:00:00Z",
        "trial_end": null
    }
}
```

### 5.4 コンテンツ管理API

#### 5.4.1 コンテンツ追加API
```
POST /api/v1/companies/{company_id}/contents
Content-Type: application/json

Request Body:
{
    "content_type": "AI予定秘書",
    "line_bot_url": "https://line.me/R/ti/p/@ai_schedule_secretary"
}

Response:
{
    "status": "success",
    "content": {
        "id": 456,
        "content_type": "AI予定秘書",
        "status": "active",
        "line_bot_url": "https://...",
        "created_at": "2024-01-01T00:00:00Z"
    }
}
```

## 6. セキュリティ設計

### 6.1 認証・認可

#### 6.1.1 API認証
- JWT（JSON Web Token）による認証
- API Key認証（企業別）
- ロールベースアクセス制御（RBAC）

#### 6.1.2 データアクセス制御
- 企業データの完全分離
- データベースレベルでのアクセス制御
- 暗号化されたデータ保存

### 6.2 データ保護

#### 6.2.1 暗号化
- データベース暗号化（AES-256）
- 通信暗号化（TLS 1.3）
- API Key暗号化

#### 6.2.2 監査・ログ
- 全操作のログ記録
- 監査証跡の保持（7年間）
- セキュリティイベントの監視

## 7. 運用設計

### 7.1 監視・アラート

#### 7.1.1 システム監視
- サーバーリソース監視
- データベース性能監視
- API応答時間監視

#### 7.1.2 ビジネス監視
- 企業登録数監視
- 決済成功率監視
- 解約率監視

### 7.2 バックアップ・復旧

#### 7.2.1 バックアップ戦略
- 日次フルバックアップ
- 1時間ごとの差分バックアップ
- リアルタイムレプリケーション

#### 7.2.2 災害復旧
- RTO（Recovery Time Objective）：4時間
- RPO（Recovery Point Objective）：1時間
- 自動復旧機能

### 7.3 パフォーマンス最適化

#### 7.3.1 データベース最適化
- インデックス設計
- クエリ最適化
- 接続プール設定

#### 7.3.2 キャッシュ戦略
- Redisキャッシュ
- CDN活用
- ブラウザキャッシュ

## 8. 開発・テスト計画

### 8.1 開発フェーズ

#### Phase 1: 基盤構築（2週間）
- データベース設計・構築
- 基本API開発
- 認証システム実装

#### Phase 2: 企業管理機能（3週間）
- 企業登録・管理機能
- LINE API連携
- Stripe決済連携

#### Phase 3: コンテンツ管理（2週間）
- コンテンツ管理機能
- 利用制限機能
- 通知システム

#### Phase 4: 解約・削除機能（2週間）
- 解約処理機能
- データ削除機能
- 監査機能

#### Phase 5: テスト・運用準備（2週間）
- 総合テスト
- パフォーマンステスト
- セキュリティテスト

### 8.2 テスト戦略

#### 8.2.1 単体テスト
- 各機能の単体テスト
- カバレッジ90%以上
- 自動テスト実行

#### 8.2.2 統合テスト
- API統合テスト
- 外部サービス連携テスト
- エンドツーエンドテスト

#### 8.2.3 負荷テスト
- 同時接続数テスト
- データベース負荷テスト
- レスポンス時間テスト

## 9. リスク・課題

### 9.1 技術的リスク

#### 9.1.1 LINE API制限
- **リスク**: LINE APIの利用制限
- **対策**: レート制限の実装、エラーハンドリング強化

#### 9.1.2 Stripe API制限
- **リスク**: Stripe APIの利用制限
- **対策**: Webhook処理の最適化、リトライ機能実装

### 9.2 運用リスク

#### 9.2.1 データ削除の影響
- **リスク**: 誤ったデータ削除
- **対策**: 削除前の確認機能、バックアップ保持

#### 9.2.2 通知配信失敗
- **リスク**: 重要な通知の配信失敗
- **対策**: 複数チャンネルでの配信、配信確認機能

### 9.3 ビジネスリスク

#### 9.3.1 企業データの漏洩
- **リスク**: 企業機密情報の漏洩
- **対策**: データ暗号化、アクセス制御強化

#### 9.3.2 サービス停止
- **リスク**: システム障害によるサービス停止
- **対策**: 冗長化、自動復旧機能

## 10. 今後の拡張予定

### 10.1 短期拡張（3ヶ月以内）
- 多言語対応
- モバイルアプリ開発
- 高度な分析機能

### 10.2 中期拡張（6ヶ月以内）
- AI機能の統合
- 自動化機能の強化
- サードパーティ連携

### 10.3 長期拡張（1年以内）
- グローバル展開
- エンタープライズ機能
- パートナーエコシステム

## 11. まとめ

この設計書たたき資料では、企業ごとの公式LINEアカウント管理システムの包括的な設計を提案しました。

### 11.1 主要な特徴
- **自動化**: LINEアカウント作成から解約処理まで自動化
- **統合管理**: 企業情報、決済、コンテンツを一元管理
- **セキュリティ**: 企業データの完全分離と暗号化
- **スケーラビリティ**: 大量企業対応の設計

### 11.2 実現可能性
- 既存の技術基盤を活用可能
- 段階的な実装が可能
- 運用コストの削減効果が期待

### 11.3 次のステップ
1. 詳細設計書の作成
2. プロトタイプの開発
3. ユーザーフィードバックの収集
4. 本格開発の開始

このシステムにより、企業向けサービスの運用効率が大幅に向上し、顧客満足度の向上と運用コストの削減が実現できます。 