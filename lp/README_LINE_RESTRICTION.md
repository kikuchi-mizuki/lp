# 公式LINE利用制限機能

## 概要

この機能により、ユーザーがコンテンツを解約した場合、対応する公式LINEアカウントを利用できなくし、AIコレクションズの公式LINEに誘導します。

## 機能

### 1. 解約履歴の記録
- ユーザーがコンテンツを解約すると、`cancellation_history`テーブルに記録
- 解約されたコンテンツの公式LINEを利用できなくする

### 2. 利用制限のチェック
- 各公式LINEアカウントで利用制限をチェック
- 制限されている場合は専用のUIを表示

### 3. AIコレクションズへの誘導
- 制限されたユーザーをAIコレクションズの公式LINEに誘導
- 再度登録してサービスを利用できるようにする

## データベース構造

### cancellation_history テーブル
```sql
CREATE TABLE cancellation_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    content_type VARCHAR(255) NOT NULL,
    cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## API エンドポイント

### 1. 利用制限チェック
```
POST /line/check_restriction/{content_type}
```

**Request Body:**
```json
{
    "line_user_id": "U1234567890abcdef"
}
```

**Response:**
```json
{
    "line_user_id": "U1234567890abcdef",
    "user_id": 1,
    "content_type": "AI予定秘書",
    "restricted": true,
    "message": "AI予定秘書は解約されているため利用できません。"
}
```

### 2. 制限メッセージ取得
```
POST /line/restriction_message/{content_type}
```

**Request Body:**
```json
{
    "line_user_id": "U1234567890abcdef"
}
```

**Response:**
```json
{
    "line_user_id": "U1234567890abcdef",
    "user_id": 1,
    "content_type": "AI予定秘書",
    "restricted": true,
    "message": {
        "type": "template",
        "altText": "AI予定秘書の利用制限",
        "template": {
            "type": "buttons",
            "title": "AI予定秘書の利用制限",
            "text": "AI予定秘書は解約されているため、公式LINEを利用できません。\n\nAIコレクションズの公式LINEで再度ご登録いただき、サービスをご利用ください。",
            "actions": [
                {
                    "type": "uri",
                    "label": "AIコレクションズ公式LINE",
                    "uri": "https://line.me/R/ti/p/@ai_collections"
                },
                {
                    "type": "uri",
                    "label": "サービス詳細",
                    "uri": "https://ai-collections.herokuapp.com"
                }
            ]
        }
    }
}
```

### 3. デバッグ用：解約履歴確認
```
GET /line/debug/cancellation_history/{user_id}
```

**Response:**
```json
{
    "user_id": 1,
    "cancelled_contents": ["AI予定秘書", "AI経理秘書"],
    "count": 2
}
```

## 各公式LINEアカウントでの実装

### 1. JavaScriptファイルの組み込み
各公式LINEアカウントのWebページに以下のスクリプトを追加：

```html
<script src="https://ai-collections.herokuapp.com/static/js/line_restriction_checker.js"></script>
```

### 2. 自動初期化
スクリプトは自動的に初期化され、ページ読み込み時に利用制限をチェックします。

### 3. 手動初期化（オプション）
```javascript
const checker = new LineRestrictionChecker('https://ai-collections.herokuapp.com');
checker.init();
```

## 対応コンテンツ

| コンテンツ | 公式LINE URL | 制限チェック対象 |
|-----------|-------------|----------------|
| AI予定秘書 | https://line.me/R/ti/p/@ai_schedule_secretary | AI予定秘書 |
| AI経理秘書 | https://line.me/R/ti/p/@ai_accounting_secretary | AI経理秘書 |
| AIタスクコンシェルジュ | https://line.me/R/ti/p/@ai_task_concierge | AIタスクコンシェルジュ |

## 動作フロー

### 1. コンテンツ追加時
1. ユーザーがコンテンツを追加
2. 対応する公式LINEのURLを送信
3. ユーザーが公式LINEに登録

### 2. コンテンツ解約時
1. ユーザーがコンテンツを解約
2. `cancellation_history`テーブルに記録
3. 解約完了メッセージを送信
4. 公式LINEの利用制限を通知

### 3. 公式LINEアクセス時
1. ユーザーが公式LINEにアクセス
2. JavaScriptが利用制限をチェック
3. 制限されている場合は専用UIを表示
4. AIコレクションズの公式LINEに誘導

## デバッグ

### 解約履歴の確認
```
GET https://ai-collections.herokuapp.com/line/debug/cancellation_history/{user_id}
```

### 利用制限のテスト
```javascript
// ブラウザのコンソールで実行
const checker = new LineRestrictionChecker();
checker.checkRestriction().then(result => console.log(result));
```

## 注意事項

1. **LINEユーザーIDの取得**: 実際の実装では、LINE Login APIを使用してユーザーIDを取得する必要があります
2. **CORS設定**: 各公式LINEアカウントのドメインからのAPIアクセスを許可する必要があります
3. **セキュリティ**: APIエンドポイントは適切な認証・認可を実装してください
4. **エラーハンドリング**: ネットワークエラーやAPIエラーの適切な処理が必要です

## 今後の拡張

1. **LINE Login統合**: LINE Login APIを使用した正式なユーザー認証
2. **リアルタイム通知**: WebSocketを使用したリアルタイムな制限通知
3. **統計機能**: 解約・制限の統計情報の提供
4. **管理画面**: 解約履歴の管理・操作画面 