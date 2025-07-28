"""
既存LINE公式アカウント用 利用制限チェック統合コード

このコードを既存のLINE Botシステムに組み込んでください。
"""

import requests
import json
import os
import logging
from functools import lru_cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LineRestrictionChecker:
    """LINE利用制限チェッカー"""
    
    def __init__(self, content_type):
        self.content_type = content_type
        self.api_base_url = os.getenv('AI_COLLECTIONS_BASE_URL', 'https://ai-collections.herokuapp.com')
        self.session = self._create_session_with_retry()
        
    def _create_session_with_retry(self):
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
    
    def _add_authentication(self, headers):
        """認証ヘッダーを追加"""
        api_key = os.getenv('AI_COLLECTIONS_API_KEY')
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        return headers
    
    def check_user_restriction(self, line_user_id):
        """ユーザーの利用制限をチェック"""
        try:
            headers = self._add_authentication({
                'Content-Type': 'application/json'
            })
            
            response = self.session.post(
                f"{self.api_base_url}/line/check_restriction/{self.content_type}",
                json={"line_user_id": line_user_id},
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"利用制限チェック: user_id={line_user_id}, content_type={self.content_type}, restricted={result.get('restricted')}")
                return result
            else:
                logger.error(f"API呼び出しエラー: {response.status_code}, {response.text}")
                return {"restricted": False, "error": "api_error"}
                
        except Exception as e:
            logger.error(f"利用制限チェックエラー: {e}")
            return {"restricted": False, "error": str(e)}
    
    def get_restriction_message(self, line_user_id):
        """制限メッセージを取得"""
        try:
            headers = self._add_authentication({
                'Content-Type': 'application/json'
            })
            
            response = self.session.post(
                f"{self.api_base_url}/line/restriction_message/{self.content_type}",
                json={"line_user_id": line_user_id},
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"制限メッセージ取得エラー: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"制限メッセージ取得エラー: {e}")
            return None

@lru_cache(maxsize=1000)
def cached_restriction_check(user_id, content_type):
    """キャッシュ付き利用制限チェック（5分間キャッシュ）"""
    checker = LineRestrictionChecker(content_type)
    return checker.check_user_restriction(user_id)

def safe_check_restriction(line_user_id, content_type):
    """安全な利用制限チェック（エラー時は制限しない）"""
    try:
        result = cached_restriction_check(line_user_id, content_type)
        return result
    except Exception as e:
        logger.error(f"安全な利用制限チェックエラー: {e}")
        # エラーの場合は制限しない（サービスを継続）
        return {"restricted": False, "error": str(e)}

# 各サービス用の設定
SCHEDULE_CONTENT_TYPE = "AI予定秘書"
ACCOUNTING_CONTENT_TYPE = "AI経理秘書"
TASK_CONTENT_TYPE = "AIタスクコンシェルジュ"

# 既存LINE Botのメッセージ処理に組み込む関数
def handle_message_with_restriction(event, line_bot_api, content_type):
    """
    利用制限チェック付きメッセージ処理
    
    Args:
        event: LINE Botイベント
        line_bot_api: LINE Bot APIインスタンス
        content_type: コンテンツタイプ（"AI予定秘書", "AI経理秘書", "AIタスクコンシェルジュ"）
    """
    user_id = event.source.user_id
    message_text = event.message.text if hasattr(event.message, 'text') else ""
    
    logger.info(f"メッセージ受信: user_id={user_id}, content_type={content_type}, text={message_text[:50]}...")
    
    # 利用制限チェック
    restriction_result = safe_check_restriction(user_id, content_type)
    
    if restriction_result.get("restricted"):
        logger.info(f"利用制限: user_id={user_id}, content_type={content_type}")
        
        # 制限されている場合、制限メッセージを送信
        checker = LineRestrictionChecker(content_type)
        restriction_data = checker.get_restriction_message(user_id)
        
        if restriction_data and restriction_data.get("message"):
            try:
                line_bot_api.reply_message(
                    event.reply_token,
                    restriction_data["message"]
                )
                logger.info(f"制限メッセージ送信完了: user_id={user_id}")
            except Exception as e:
                logger.error(f"制限メッセージ送信エラー: {e}")
        else:
            # 制限メッセージが取得できない場合のフォールバック
            fallback_message = {
                "type": "text",
                "text": f"{content_type}は解約されているため利用できません。\n\nAIコレクションズの公式LINEで再度ご登録いただき、サービスをご利用ください。\n\nhttps://line.me/R/ti/p/@ai_collections"
            }
            try:
                line_bot_api.reply_message(event.reply_token, fallback_message)
            except Exception as e:
                logger.error(f"フォールバックメッセージ送信エラー: {e}")
        
        return True  # 制限された場合はTrueを返す
    
    # 制限されていない場合はFalseを返す（通常の処理を続行）
    logger.info(f"利用可能: user_id={user_id}, content_type={content_type}")
    return False

# 各サービス用の専用関数
def handle_schedule_message(event, line_bot_api):
    """AI予定秘書用メッセージ処理"""
    return handle_message_with_restriction(event, line_bot_api, SCHEDULE_CONTENT_TYPE)

def handle_accounting_message(event, line_bot_api):
    """AI経理秘書用メッセージ処理"""
    return handle_message_with_restriction(event, line_bot_api, ACCOUNTING_CONTENT_TYPE)

def handle_task_message(event, line_bot_api):
    """AIタスクコンシェルジュ用メッセージ処理"""
    return handle_message_with_restriction(event, line_bot_api, TASK_CONTENT_TYPE)

# 既存LINE Botのメイン処理部分に組み込む例
def example_integration():
    """
    既存LINE Botへの組み込み例
    
    既存のLINE Botコードのメッセージ処理部分を以下のように修正してください：
    """
    
    # 例：AI予定秘書の場合
    """
    from line_integration_code import handle_schedule_message
    
    # 既存のLINE Botコード
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
    """
    
    # 例：AI経理秘書の場合
    """
    from line_integration_code import handle_accounting_message
    
    # 既存のLINE Botコード
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
    """
    
    # 例：AIタスクコンシェルジュの場合
    """
    from line_integration_code import handle_task_message
    
    # 既存のLINE Botコード
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
    """

# テスト用関数
def test_restriction_check():
    """利用制限チェックのテスト"""
    test_user_id = "U1234567890abcdef"  # テスト用ユーザーID
    
    # AI予定秘書のテスト
    print("=== AI予定秘書 テスト ===")
    checker = LineRestrictionChecker(SCHEDULE_CONTENT_TYPE)
    result = checker.check_user_restriction(test_user_id)
    print(f"結果: {result}")
    
    # AI経理秘書のテスト
    print("\n=== AI経理秘書 テスト ===")
    checker = LineRestrictionChecker(ACCOUNTING_CONTENT_TYPE)
    result = checker.check_user_restriction(test_user_id)
    print(f"結果: {result}")
    
    # AIタスクコンシェルジュのテスト
    print("\n=== AIタスクコンシェルジュ テスト ===")
    checker = LineRestrictionChecker(TASK_CONTENT_TYPE)
    result = checker.check_user_restriction(test_user_id)
    print(f"結果: {result}")

if __name__ == "__main__":
    # テスト実行
    test_restriction_check() 