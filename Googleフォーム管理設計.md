# Googleフォームでの企業アカウント情報管理設計

## 1. Googleフォームの設計

### 基本情報セクション
```
企業基本情報
├── 企業名（必須）
├── メールアドレス（必須）
├── 担当者名（必須）
└── 電話番号（任意）
```

### コンテンツ選択セクション
```
利用コンテンツ（複数選択可）
├── AI予定秘書
├── AI経理秘書
└── AIタスクコンシェルジュ
```

### プラットフォーム連携セクション
```
LINE連携
├── LINEチャンネルID（必須）
└── LINEアクセストークン（必須）

Slack連携（任意）
├── SlackワークスペースID
├── SlackチャンネルID
└── Slackボットトークン

Notion連携（任意）
├── NotionワークスペースID
└── Notionインテグレーショントークン
```

### サブスクリプション情報セクション
```
契約情報
├── 契約開始日
├── 契約終了日
├── 月額料金
└── 支払い方法
```

## 2. データベース設計の簡素化

### 現在の設計（複雑）
```sql
-- 企業基本情報
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 企業LINEアカウント
CREATE TABLE company_line_accounts (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    line_channel_id VARCHAR(255) NOT NULL,
    line_channel_access_token VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id),
    UNIQUE(company_id, content_type)
);

-- 企業サブスクリプション
CREATE TABLE company_subscriptions (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    subscription_status VARCHAR(50) DEFAULT 'active',
    current_period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id),
    UNIQUE(company_id, content_type)
);
```

### 簡素化された設計（Googleフォーム管理）
```sql
-- 企業基本情報のみ（Googleフォームで管理）
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    google_form_id VARCHAR(255) UNIQUE,  -- Googleフォームの回答ID
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 解約制限チェック用（最小限）
CREATE TABLE company_restrictions (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    platform_type VARCHAR(50) NOT NULL,
    is_restricted BOOLEAN DEFAULT FALSE,
    restriction_reason VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id),
    UNIQUE(company_id, content_type, platform_type)
);
```

## 3. Googleフォーム連携システム

### Google Sheets API連携
```python
import gspread
from google.oauth2.service_account import Credentials

def get_company_info_from_google_form(company_email):
    """
    Googleフォームの回答から企業情報を取得
    """
    # Google Sheets API認証
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
    client = gspread.authorize(creds)
    
    # スプレッドシートを開く
    sheet = client.open('企業アカウント管理').sheet1
    
    # 企業メールで検索
    try:
        cell = sheet.find(company_email)
        row = sheet.row_values(cell.row)
        
        return {
            'company_name': row[0],
            'email': row[1],
            'contact_person': row[2],
            'phone': row[3],
            'contents': row[4].split(','),  # 複数選択
            'line_channel_id': row[5],
            'line_access_token': row[6],
            'slack_workspace_id': row[7],
            'slack_channel_id': row[8],
            'slack_bot_token': row[9],
            'notion_workspace_id': row[10],
            'notion_token': row[11],
            'contract_start': row[12],
            'contract_end': row[13],
            'monthly_fee': row[14],
            'payment_method': row[15]
        }
    except:
        return None
```

### 解約制限チェック（Googleフォーム連携版）
```python
def check_company_restriction_google_form(company_email, content_type, platform_type):
    """
    Googleフォーム情報を使用した解約制限チェック
    """
    # 1. Googleフォームから企業情報を取得
    company_info = get_company_info_from_google_form(company_email)
    if not company_info:
        return {'is_restricted': True, 'reason': 'company_not_found'}
    
    # 2. コンテンツの利用権限をチェック
    if content_type not in company_info['contents']:
        return {'is_restricted': True, 'reason': 'content_not_subscribed'}
    
    # 3. プラットフォーム連携をチェック
    platform_config = {
        'line': {
            'channel_id': company_info.get('line_channel_id'),
            'access_token': company_info.get('line_access_token')
        },
        'slack': {
            'workspace_id': company_info.get('slack_workspace_id'),
            'channel_id': company_info.get('slack_channel_id'),
            'bot_token': company_info.get('slack_bot_token')
        },
        'notion': {
            'workspace_id': company_info.get('notion_workspace_id'),
            'token': company_info.get('notion_token')
        }
    }
    
    if platform_type not in platform_config:
        return {'is_restricted': True, 'reason': 'platform_not_supported'}
    
    platform_info = platform_config[platform_type]
    if not platform_info.get('channel_id') and not platform_info.get('workspace_id'):
        return {'is_restricted': True, 'reason': 'platform_not_configured'}
    
    # 4. 契約期限をチェック
    contract_end = company_info.get('contract_end')
    if contract_end and datetime.strptime(contract_end, '%Y-%m-%d') < datetime.now():
        return {'is_restricted': True, 'reason': 'contract_expired'}
    
    return {'is_restricted': False, 'reason': 'access_granted'}
```

## 4. API設計（Googleフォーム連携版）

### 解約制限チェックAPI
```python
@app.route('/api/v1/company/restriction/check', methods=['POST'])
def check_company_restriction_api():
    """企業解約制限チェックAPI（Googleフォーム連携版）"""
    try:
        data = request.get_json()
        company_email = data.get('company_email')
        content_type = data.get('content_type')
        platform_type = data.get('platform_type', 'line')
        
        if not company_email or not content_type:
            return jsonify({'error': 'company_email and content_type are required'}), 400
        
        result = check_company_restriction_google_form(company_email, content_type, platform_type)
        
        messages = {
            'access_granted': '利用可能です',
            'company_not_found': '企業情報が見つかりません',
            'content_not_subscribed': 'このコンテンツは契約されていません',
            'platform_not_supported': 'このプラットフォームはサポートされていません',
            'platform_not_configured': 'プラットフォームが設定されていません',
            'contract_expired': '契約期限が切れています'
        }
        
        return jsonify({
            'is_restricted': result['is_restricted'],
            'reason': result['reason'],
            'message': messages.get(result['reason'], '不明なエラー'),
            'content_type': content_type,
            'platform_type': platform_type
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## 5. メリット

### 管理面
- ✅ **簡単な管理**: Googleフォームで直感的に管理
- ✅ **リアルタイム更新**: フォーム回答が即座に反映
- ✅ **履歴管理**: Google Sheetsで変更履歴を保持
- ✅ **権限管理**: Googleアカウントでアクセス制御

### 技術面
- ✅ **データベース簡素化**: 複雑なテーブル構造が不要
- ✅ **スケーラビリティ**: 新しいフィールドを簡単に追加
- ✅ **バックアップ**: Google Driveで自動バックアップ
- ✅ **API連携**: Google Sheets APIで自動化可能

### 運用面
- ✅ **非技術者対応**: エンジニア以外でも管理可能
- ✅ **柔軟性**: フォームの変更が容易
- ✅ **コスト削減**: データベース管理コストの削減

## 6. 実装手順

### Phase 1: Googleフォーム作成
1. 企業基本情報フォームの作成
2. コンテンツ選択機能の追加
3. プラットフォーム連携情報の追加

### Phase 2: API連携
1. Google Sheets APIの設定
2. データ取得関数の実装
3. 解約制限チェック機能の実装

### Phase 3: データベース移行
1. 既存データのGoogleフォーム移行
2. データベース構造の簡素化
3. 新システムのテスト

この設計により、企業アカウント情報の管理が大幅に簡素化され、運用コストも削減できます。 