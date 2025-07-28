# 既存LINE公式アカウント実装手順

## 概要

既存の3つのLINE公式アカウントに利用制限機能を組み込む手順を説明します。

## 対象LINE公式アカウント

- **AI予定秘書**: https://lin.ee/Lwc7NyB
- **AI経理秘書**: https://lin.ee/kqslZNS
- **AIタスクコンシェルジュ**: https://lin.ee/9K33efP

## 実装手順

### ステップ1: 既存LINE Botのコードを確認

各LINE公式アカウントのBotシステムのコードを確認し、以下の情報を把握してください：

1. **メッセージ処理部分の場所**
   - Webhookエンドポイント（通常は `/callback`）
   - メッセージイベント処理関数

2. **使用しているフレームワーク**
   - Flask
   - FastAPI
   - Django
   - その他

3. **既存の機能**
   - 現在のメッセージ処理ロジック
   - エラーハンドリング方法

### ステップ2: 統合コードの追加

#### 2-1. 依存関係の追加

既存のLINE Botプロジェクトに以下の依存関係を追加：

```bash
pip install requests urllib3
```

#### 2-2. 統合コードファイルの追加

`line_integration_code.py` ファイルを既存のLINE Botプロジェクトに追加してください。

#### 2-3. 環境変数の設定

`env_example.txt` を参考に、既存のLINE Botプロジェクトの環境変数ファイル（`.env`）に以下を追加：

```bash
# AIコレクションズメインアプリのURL
AI_COLLECTIONS_BASE_URL=https://ai-collections.herokuapp.com

# API認証キー（必要に応じて設定）
AI_COLLECTIONS_API_KEY=your_api_key_here
```

### ステップ3: 既存コードの修正

#### 3-1. インポート文の追加

既存のLINE Botコードの先頭に以下を追加：

```python
from line_integration_code import handle_schedule_message, handle_accounting_message, handle_task_message
```

#### 3-2. メッセージ処理部分の修正

既存のメッセージ処理部分を以下のように修正：

**AI予定秘書の場合：**
```python
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    for event in events:
        if isinstance(event, MessageEvent):
            # 利用制限チェックを最初に実行
            is_restricted = handle_schedule_message(event, line_bot_api)
            
            # 制限されていない場合のみ通常の処理を実行
            if not is_restricted:
                # 既存のスケジュール機能を実行
                handle_schedule_functionality(event, line_bot_api)
    
    return 'OK'
```

**AI経理秘書の場合：**
```python
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    for event in events:
        if isinstance(event, MessageEvent):
            # 利用制限チェックを最初に実行
            is_restricted = handle_accounting_message(event, line_bot_api)
            
            # 制限されていない場合のみ通常の処理を実行
            if not is_restricted:
                # 既存の経理機能を実行
                handle_accounting_functionality(event, line_bot_api)
    
    return 'OK'
```

**AIタスクコンシェルジュの場合：**
```python
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    for event in events:
        if isinstance(event, MessageEvent):
            # 利用制限チェックを最初に実行
            is_restricted = handle_task_message(event, line_bot_api)
            
            # 制限されていない場合のみ通常の処理を実行
            if not is_restricted:
                # 既存のタスク機能を実行
                handle_task_functionality(event, line_bot_api)
    
    return 'OK'
```

### ステップ4: テスト

#### 4-1. ローカルテスト

```bash
# 統合コードのテスト
python line_integration_code.py
```

#### 4-2. 既存LINE Botのテスト

1. **アクティブユーザーでのテスト**
   - 正常にサービスが利用できることを確認

2. **解約済みユーザーでのテスト**
   - 制限メッセージが表示されることを確認
   - AIコレクションズ公式LINEへの誘導が正常に動作することを確認

### ステップ5: デプロイ

#### 5-1. テスト環境でのデプロイ

1. 既存のLINE Botをテスト環境にデプロイ
2. テストユーザーで動作確認
3. ログを確認してエラーがないことを確認

#### 5-2. 本番環境でのデプロイ

1. 既存のLINE Botを本番環境にデプロイ
2. 段階的にユーザーに展開
3. 監視とログで動作確認

## 動作フロー

### 1. ユーザーがLINE公式アカウントにメッセージを送信

### 2. 利用制限チェック

1. LINE Botがメッセージを受信
2. `handle_*_message` 関数が呼び出される
3. AIコレクションズメインアプリのAPIを呼び出し
4. PostgreSQLデータベースで解約履歴をチェック

### 3. 制限判定

**制限されている場合：**
- 制限メッセージを送信
- AIコレクションズ公式LINEへの誘導
- 通常の処理を停止

**制限されていない場合：**
- 通常のサービス機能を実行

## トラブルシューティング

### 1. API接続エラー

**症状：** 利用制限チェックでエラーが発生
**対処法：**
- ネットワーク接続を確認
- `AI_COLLECTIONS_BASE_URL` の設定を確認
- ファイアウォール設定を確認

### 2. データベース接続エラー

**症状：** 解約履歴の取得でエラーが発生
**対処法：**
- PostgreSQLデータベースの状態を確認
- 接続文字列を確認
- データベースの権限を確認

### 3. LINE Bot API エラー

**症状：** 制限メッセージの送信でエラーが発生
**対処法：**
- LINE Bot API の制限を確認
- アクセストークンの有効性を確認
- Webhook URLの設定を確認

## 監視とログ

### 1. ログの確認

```bash
# アプリケーションログを確認
tail -f app.log

# エラーログを確認
grep "ERROR" app.log
```

### 2. メトリクスの確認

- 利用制限チェックの成功率
- API応答時間
- エラー発生率

### 3. アラート設定

- API接続エラーのアラート
- データベース接続エラーのアラート
- LINE Bot API エラーのアラート

## セキュリティ考慮事項

### 1. API認証

必要に応じてAPI認証を追加：

```python
# 環境変数でAPIキーを設定
AI_COLLECTIONS_API_KEY=your_secure_api_key
```

### 2. レート制限

API呼び出しのレート制限を設定：

```python
# キャッシュ機能を使用してAPI呼び出しを制限
@lru_cache(maxsize=1000)
def cached_restriction_check(user_id, content_type):
    # 5分間キャッシュ
    pass
```

### 3. エラーハンドリング

エラー時のフォールバック処理：

```python
def safe_check_restriction(line_user_id, content_type):
    try:
        result = cached_restriction_check(line_user_id, content_type)
        return result
    except Exception as e:
        # エラーの場合は制限しない（サービスを継続）
        return {"restricted": False, "error": str(e)}
```

## 今後の拡張

### 1. リアルタイム通知

解約時にリアルタイムで利用制限を反映

### 2. 詳細な利用統計

利用制限チェックの詳細な統計情報

### 3. 自動復旧機能

一時的なエラー時の自動復旧機能 