# 既存LINE公式アカウント連携ガイド

## 概要

既存の3つのLINE公式アカウントに、PostgreSQLデータベースと連携した利用制限機能を組み込む方法を説明します。

## 既存LINE公式アカウント

- **AI予定秘書**: https://lin.ee/Lwc7NyB
- **AI経理秘書**: https://lin.ee/kqslZNS
- **AIタスクコンシェルジュ**: https://lin.ee/9K33efP

## 実装方法

### 方法A: 既存LINE BotにAPI連携機能を追加（推奨）

#### 1. 既存LINE Botのコードを確認

各LINE公式アカウントのBotシステムで、以下の機能を追加します：

```python
# 既存のLINE Botコードに追加
import requests
import json

class LineRestrictionChecker:
    def __init__(self, content_type):
        self.content_type = content_type
        self.api_base_url = "https://ai-collections.herokuapp.com"  # メインアプリのURL
        
    def check_user_restriction(self, line_user_id):
        """ユーザーの利用制限をチェック"""
        try:
            response = requests.post(
                f"{self.api_base_url}/line/check_restriction/{self.content_type}",
                json={"line_user_id": line_user_id},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[ERROR] API呼び出しエラー: {response.status_code}")
                return {"restricted": False, "error": "api_error"}
                
        except Exception as e:
            print(f"[ERROR] 利用制限チェックエラー: {e}")
            return {"restricted": False, "error": str(e)}
    
    def get_restriction_message(self, line_user_id):
        """制限メッセージを取得"""
        try:
            response = requests.post(
                f"{self.api_base_url}/line/restriction_message/{self.content_type}",
                json={"line_user_id": line_user_id},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            print(f"[ERROR] 制限メッセージ取得エラー: {e}")
            return None
```

#### 2. LINE Botのメッセージ処理に組み込み

```python
# 既存のLINE Botのメッセージ処理部分
def handle_message(event, line_bot_api):
    user_id = event.source.user_id
    message_text = event.message.text
    
    # 利用制限チェック
    restriction_checker = LineRestrictionChecker("AI予定秘書")  # 各サービスに応じて変更
    restriction_result = restriction_checker.check_user_restriction(user_id)
    
    if restriction_result.get("restricted"):
        # 制限されている場合、制限メッセージを送信
        restriction_data = restriction_checker.get_restriction_message(user_id)
        if restriction_data and restriction_data.get("message"):
            line_bot_api.reply_message(
                event.reply_token,
                restriction_data["message"]
            )
        return  # 以降の処理を停止
    
    # 通常のメッセージ処理を続行
    # ... 既存のコード ...
```

#### 3. 各サービス用の設定

**AI予定秘書用**
```python
restriction_checker = LineRestrictionChecker("AI予定秘書")
```

**AI経理秘書用**
```python
restriction_checker = LineRestrictionChecker("AI経理秘書")
```

**AIタスクコンシェルジュ用**
```python
restriction_checker = LineRestrictionChecker("AIタスクコンシェルジュ")
```

### 方法B: Webhook方式での連携

#### 1. 既存LINE BotにWebhookエンドポイントを追加

```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/webhook/restriction_check', methods=['POST'])
def restriction_check_webhook():
    """利用制限チェック用Webhook"""
    try:
        data = request.get_json()
        line_user_id = data.get('line_user_id')
        content_type = data.get('content_type')
        
        # メインアプリのAPIを呼び出し
        response = requests.post(
            f"https://ai-collections.herokuapp.com/line/check_restriction/{content_type}",
            json={"line_user_id": line_user_id},
            headers={"Content-Type": "application/json"}
        )
        
        return jsonify(response.json())
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

#### 2. 既存LINE BotからWebhookを呼び出し

```python
def check_restriction_via_webhook(line_user_id, content_type):
    """Webhook経由で利用制限をチェック"""
    try:
        response = requests.post(
            "https://your-line-bot-domain.com/webhook/restriction_check",
            json={
                "line_user_id": line_user_id,
                "content_type": content_type
            },
            headers={"Content-Type": "application/json"}
        )
        
        return response.json()
        
    except Exception as e:
        print(f"[ERROR] Webhook呼び出しエラー: {e}")
        return {"restricted": False, "error": str(e)}
```

## 実装手順

### ステップ1: 既存LINE Botのコードを取得

各LINE公式アカウントのBotシステムのコードを確認し、メッセージ処理部分を特定します。

### ステップ2: 利用制限チェック機能を追加

上記の`LineRestrictionChecker`クラスを既存のコードに追加します。

### ステップ3: メッセージ処理に組み込み

既存のメッセージ処理関数の最初に、利用制限チェックを追加します。

### ステップ4: テスト

各LINE公式アカウントで、解約済みユーザーとアクティブユーザーでテストを実行します。

## 設定例

### AI予定秘書の設定例

```python
# AI予定秘書用の設定
CONTENT_TYPE = "AI予定秘書"
API_BASE_URL = "https://ai-collections.herokuapp.com"

def handle_schedule_message(event, line_bot_api):
    user_id = event.source.user_id
    
    # 利用制限チェック
    checker = LineRestrictionChecker(CONTENT_TYPE)
    result = checker.check_user_restriction(user_id)
    
    if result.get("restricted"):
        restriction_data = checker.get_restriction_message(user_id)
        if restriction_data and restriction_data.get("message"):
            line_bot_api.reply_message(
                event.reply_token,
                restriction_data["message"]
            )
        return
    
    # 通常のスケジュール機能を実行
    # ... 既存のスケジュール処理コード ...
```

### AI経理秘書の設定例

```python
# AI経理秘書用の設定
CONTENT_TYPE = "AI経理秘書"
API_BASE_URL = "https://ai-collections.herokuapp.com"

def handle_accounting_message(event, line_bot_api):
    user_id = event.source.user_id
    
    # 利用制限チェック
    checker = LineRestrictionChecker(CONTENT_TYPE)
    result = checker.check_user_restriction(user_id)
    
    if result.get("restricted"):
        restriction_data = checker.get_restriction_message(user_id)
        if restriction_data and restriction_data.get("message"):
            line_bot_api.reply_message(
                event.reply_token,
                restriction_data["message"]
            )
        return
    
    # 通常の経理機能を実行
    # ... 既存の経理処理コード ...
```

### AIタスクコンシェルジュの設定例

```python
# AIタスクコンシェルジュ用の設定
CONTENT_TYPE = "AIタスクコンシェルジュ"
API_BASE_URL = "https://ai-collections.herokuapp.com"

def handle_task_message(event, line_bot_api):
    user_id = event.source.user_id
    
    # 利用制限チェック
    checker = LineRestrictionChecker(CONTENT_TYPE)
    result = checker.check_user_restriction(user_id)
    
    if result.get("restricted"):
        restriction_data = checker.get_restriction_message(user_id)
        if restriction_data and restriction_data.get("message"):
            line_bot_api.reply_message(
                event.reply_token,
                restriction_data["message"]
            )
        return
    
    # 通常のタスク機能を実行
    # ... 既存のタスク処理コード ...
```

## エラーハンドリング

### 1. API接続エラー

```python
def safe_check_restriction(line_user_id, content_type):
    """安全な利用制限チェック"""
    try:
        checker = LineRestrictionChecker(content_type)
        result = checker.check_user_restriction(line_user_id)
        return result
    except Exception as e:
        print(f"[ERROR] 利用制限チェックエラー: {e}")
        # エラーの場合は制限しない（サービスを継続）
        return {"restricted": False, "error": str(e)}
```

### 2. タイムアウト設定

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retry():
    """リトライ機能付きセッションを作成"""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.1,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# 使用例
session = create_session_with_retry()
response = session.post(url, json=data, timeout=5)
```

## 監視とログ

### 1. 利用制限チェックのログ

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_restriction_check(user_id, content_type, result):
    """利用制限チェックのログを記録"""
    logger.info(f"利用制限チェック: user_id={user_id}, content_type={content_type}, restricted={result.get('restricted')}")
    
    if result.get("error"):
        logger.error(f"利用制限チェックエラー: {result['error']}")
```

### 2. メトリクス収集

```python
def collect_metrics(user_id, content_type, restricted):
    """メトリクスを収集"""
    # ここでメトリクス収集サービス（Datadog、New Relic等）に送信
    pass
```

## セキュリティ考慮事項

### 1. API認証

```python
import os

def add_api_authentication(headers):
    """API認証ヘッダーを追加"""
    api_key = os.getenv('AI_COLLECTIONS_API_KEY')
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    return headers
```

### 2. レート制限

```python
from functools import lru_cache
import time

@lru_cache(maxsize=1000)
def cached_restriction_check(user_id, content_type):
    """キャッシュ付き利用制限チェック（5分間キャッシュ）"""
    # 実装例
    pass
```

## デプロイ手順

### 1. 既存LINE Botの更新

1. 既存のLINE Botコードに利用制限チェック機能を追加
2. テスト環境で動作確認
3. 本番環境にデプロイ

### 2. 環境変数の設定

```bash
# 各LINE Botの環境変数に追加
AI_COLLECTIONS_API_KEY=your_api_key
AI_COLLECTIONS_BASE_URL=https://ai-collections.herokuapp.com
```

### 3. 段階的デプロイ

1. 一部のユーザーでテスト
2. 問題がなければ全ユーザーに展開
3. 監視とログで動作確認

## トラブルシューティング

### 1. API接続エラー

- ネットワーク接続を確認
- APIエンドポイントのURLを確認
- ファイアウォール設定を確認

### 2. データベース接続エラー

- PostgreSQLデータベースの状態を確認
- 接続文字列を確認
- データベースの権限を確認

### 3. LINE Bot API エラー

- LINE Bot API の制限を確認
- アクセストークンの有効性を確認
- Webhook URLの設定を確認 