from flask import Blueprint, request, jsonify
import os
import hmac
import hashlib
import base64
import json
from lp.utils.db import get_db_connection

ai_schedule_webhook_simple_bp = Blueprint('ai_schedule_webhook_simple', __name__)

@ai_schedule_webhook_simple_bp.route('/ai-schedule/webhook', methods=['POST'])
def ai_schedule_webhook_simple():
    """AI予定秘書専用のシンプルなWebhookエンドポイント"""
    print(f'[AI Schedule Webhook] リクエスト受信: {request.method}')
    print(f'[AI Schedule Webhook] ヘッダー: {dict(request.headers)}')
    print(f'[AI Schedule Webhook] ボディ: {request.data.decode("utf-8")}')
    
    # LINE署名の検証
    signature = request.headers.get('X-Line-Signature', '')
    body = request.data.decode('utf-8')
    
    # 環境変数からLINEチャネルシークレットを取得
    LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
    
    if LINE_CHANNEL_SECRET:
        try:
            hash = hmac.new(LINE_CHANNEL_SECRET.encode('utf-8'), body.encode('utf-8'), hashlib.sha256).digest()
            expected_signature = base64.b64encode(hash).decode('utf-8')
            if not hmac.compare_digest(signature, expected_signature):
                print(f'[AI Schedule Webhook] 署名検証失敗: expected={expected_signature}, received={signature}')
                return 'Invalid signature', 400
            else:
                print(f'[AI Schedule Webhook] 署名検証成功')
        except Exception as e:
            print(f'[AI Schedule Webhook] 署名検証エラー: {e}')
            return 'Signature verification error', 400
    
    try:
        events = json.loads(body).get('events', [])
        print(f'[AI Schedule Webhook] イベント数: {len(events)}')
        
        for event in events:
            print(f'[AI Schedule Webhook] イベント処理開始: {event.get("type")}')
            
            # 友達追加イベントの処理
            if event.get('type') == 'follow':
                user_id = event['source']['userId']
                print(f'[AI Schedule Webhook] 友達追加イベント: user_id={user_id}')
                
                # AI予定秘書用のウェルカムメッセージを送信
                welcome_message = {
                    "type": "text",
                    "text": "AI予定秘書へようこそ！\n\n予定管理についてお手伝いします。\n\n以下の機能をご利用いただけます：\n• 予定の登録・管理\n• リマインダー設定\n• スケジュール確認\n\n何かご質問がございましたら、お気軽にお声かけください。"
                }
                
                try:
                    from lp.services.line_service import send_line_message
                    send_line_message(event['replyToken'], [welcome_message])
                    print(f'[AI Schedule Webhook] AI予定秘書ウェルカムメッセージ送信完了: user_id={user_id}')
                except Exception as e:
                    print(f'[AI Schedule Webhook] ウェルカムメッセージ送信エラー: {e}')
            
            # メッセージイベントの処理
            elif event.get('type') == 'message':
                user_id = event['source']['userId']
                message_text = event['message'].get('text', '')
                print(f'[AI Schedule Webhook] メッセージ受信: user_id={user_id}, text={message_text}')
                
                # AI予定秘書の基本的な応答
                if '予定' in message_text or 'スケジュール' in message_text:
                    response_message = {
                        "type": "text",
                        "text": "予定管理についてお手伝いします。\n\n予定を登録する場合は「予定を登録」とお送りください。\nスケジュールを確認する場合は「予定を確認」とお送りください。"
                    }
                elif '登録' in message_text:
                    response_message = {
                        "type": "text",
                        "text": "予定の登録機能は現在開発中です。\n\n近日中にリリース予定ですので、しばらくお待ちください。"
                    }
                elif '確認' in message_text:
                    response_message = {
                        "type": "text",
                        "text": "予定の確認機能は現在開発中です。\n\n近日中にリリース予定ですので、しばらくお待ちください。"
                    }
                else:
                    response_message = {
                        "type": "text",
                        "text": "AI予定秘書です。\n\n予定管理についてお手伝いします。\n「予定」や「スケジュール」についてお聞かせください。"
                    }
                
                try:
                    from lp.services.line_service import send_line_message
                    send_line_message(event['replyToken'], [response_message])
                    print(f'[AI Schedule Webhook] 応答メッセージ送信完了: user_id={user_id}')
                except Exception as e:
                    print(f'[AI Schedule Webhook] 応答メッセージ送信エラー: {e}')
        
        return 'OK', 200
        
    except Exception as e:
        print(f'[AI Schedule Webhook] エラー: {e}')
        import traceback
        traceback.print_exc()
        return 'Internal Server Error', 500 