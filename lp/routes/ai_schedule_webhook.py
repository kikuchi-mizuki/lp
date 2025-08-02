from flask import Blueprint, request, jsonify
import os
import hmac
import hashlib
import base64
import json
from utils.db import get_db_connection
from services.line_service import send_line_message
from services.user_service import is_paid_user, get_restricted_message
from models.user_state import get_user_state, set_user_state

ai_schedule_webhook_bp = Blueprint('ai_schedule_webhook', __name__)

@ai_schedule_webhook_bp.route('/webhook/<int:company_id>', methods=['POST'])
def ai_schedule_webhook(company_id):
    """AI予定秘書用のWebhookエンドポイント（企業IDベース）"""
    print(f'[AI Schedule Webhook] 企業ID {company_id} からのWebhook受信: {request.method}')
    print(f'[AI Schedule Webhook] ヘッダー: {dict(request.headers)}')
    print(f'[AI Schedule Webhook] ボディ: {request.data.decode("utf-8")}')
    
    # LINE署名の検証
    signature = request.headers.get('X-Line-Signature', '')
    body = request.data.decode('utf-8')
    
    # 企業固有のLINEチャネルシークレットを取得
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT cla.line_channel_secret, cla.line_channel_access_token
        FROM company_line_accounts cla
        WHERE cla.company_id = %s
    ''', (company_id,))
    
    line_account = c.fetchone()
    if not line_account:
        print(f'[AI Schedule Webhook] 企業ID {company_id} のLINEアカウントが見つかりません')
        return 'Company not found', 404
    
    line_channel_secret, line_channel_access_token = line_account
    
    # 署名検証
    if line_channel_secret:
        try:
            hash = hmac.new(line_channel_secret.encode('utf-8'), body.encode('utf-8'), hashlib.sha256).digest()
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
                
                # 決済状況をチェック
                payment_check = is_paid_user(user_id)
                if not payment_check['is_paid']:
                    print(f'[AI Schedule Webhook] 未決済ユーザーの友達追加: user_id={user_id}, status={payment_check["subscription_status"]}')
                    # 制限メッセージを送信
                    restricted_message = get_restricted_message()
                    send_line_message(event['replyToken'], [restricted_message])
                    continue
                
                # 既に案内文が送信されているかチェック
                if get_user_state(user_id) == 'welcome_sent':
                    print(f'[AI Schedule Webhook] 既に案内文送信済み、スキップ: user_id={user_id}')
                    continue
                
                # 既存のLINEユーザーIDで検索
                c.execute('SELECT id, stripe_subscription_id, line_user_id FROM users WHERE line_user_id = %s', (user_id,))
                existing_user = c.fetchone()
                print(f'[AI Schedule Webhook] 友達追加時の既存ユーザー検索結果: {existing_user}')
                
                if existing_user:
                    # 既に紐付け済みの場合
                    print(f'[AI Schedule Webhook] 既に紐付け済み: user_id={user_id}, db_user_id={existing_user[0]}')
                    
                    # AI予定秘書用のウェルカムメッセージを送信
                    welcome_message = {
                        "type": "text",
                        "text": f"AI予定秘書へようこそ！\n\n企業ID: {company_id} の予定管理をお手伝いします。\n\n以下の機能をご利用いただけます：\n• 予定の登録・管理\n• リマインダー設定\n• スケジュール確認\n\n何かご質問がございましたら、お気軽にお声かけください。"
                    }
                    
                    try:
                        send_line_message(event['replyToken'], [welcome_message])
                        print(f'[AI Schedule Webhook] AI予定秘書ウェルカムメッセージ送信完了: user_id={user_id}')
                        set_user_state(user_id, 'welcome_sent')
                    except Exception as e:
                        print(f'[AI Schedule Webhook] ウェルカムメッセージ送信エラー: {e}')
                        set_user_state(user_id, 'welcome_sent')
                else:
                    # 未紐付けユーザーを検索
                    c.execute('SELECT id, stripe_subscription_id FROM users WHERE line_user_id IS NULL ORDER BY created_at DESC LIMIT 1')
                    unlinked_user = c.fetchone()
                    print(f'[AI Schedule Webhook] 友達追加時の未紐付けユーザー検索結果: {unlinked_user}')
                    
                    if unlinked_user:
                        # 新しい紐付けを作成
                        c.execute('UPDATE users SET line_user_id = %s WHERE id = %s', (user_id, unlinked_user[0]))
                        conn.commit()
                        print(f'[AI Schedule Webhook] ユーザー紐付け完了: user_id={user_id}, db_user_id={unlinked_user[0]}')
                        
                        # AI予定秘書用のウェルカムメッセージを送信
                        welcome_message = {
                            "type": "text",
                            "text": f"AI予定秘書へようこそ！\n\n企業ID: {company_id} の予定管理をお手伝いします。\n\n以下の機能をご利用いただけます：\n• 予定の登録・管理\n• リマインダー設定\n• スケジュール確認\n\n何かご質問がございましたら、お気軽にお声かけください。"
                        }
                        
                        try:
                            send_line_message(event['replyToken'], [welcome_message])
                            print(f'[AI Schedule Webhook] AI予定秘書ウェルカムメッセージ送信完了: user_id={user_id}')
                            set_user_state(user_id, 'welcome_sent')
                        except Exception as e:
                            print(f'[AI Schedule Webhook] ウェルカムメッセージ送信エラー: {e}')
                            set_user_state(user_id, 'welcome_sent')
                    else:
                        print(f'[AI Schedule Webhook] 未紐付けユーザーが見つかりません: user_id={user_id}')
            
            # メッセージイベントの処理
            elif event.get('type') == 'message':
                user_id = event['source']['userId']
                message_text = event['message'].get('text', '')
                print(f'[AI Schedule Webhook] メッセージ受信: user_id={user_id}, text={message_text}')
                
                # 決済状況をチェック
                payment_check = is_paid_user(user_id)
                if not payment_check['is_paid']:
                    print(f'[AI Schedule Webhook] 未決済ユーザーのメッセージ: user_id={user_id}')
                    restricted_message = get_restricted_message()
                    send_line_message(event['replyToken'], [restricted_message])
                    continue
                
                # AI予定秘書の基本的な応答
                if '予定' in message_text or 'スケジュール' in message_text:
                    response_message = {
                        "type": "text",
                        "text": "予定管理についてお手伝いします。\n\n予定を登録する場合は「予定を登録」とお送りください。\nスケジュールを確認する場合は「予定を確認」とお送りください。"
                    }
                    send_line_message(event['replyToken'], [response_message])
                elif '登録' in message_text:
                    response_message = {
                        "type": "text",
                        "text": "予定の登録機能は現在開発中です。\n\n近日中にリリース予定ですので、しばらくお待ちください。"
                    }
                    send_line_message(event['replyToken'], [response_message])
                elif '確認' in message_text:
                    response_message = {
                        "type": "text",
                        "text": "予定の確認機能は現在開発中です。\n\n近日中にリリース予定ですので、しばらくお待ちください。"
                    }
                    send_line_message(event['replyToken'], [response_message])
                else:
                    response_message = {
                        "type": "text",
                        "text": "AI予定秘書です。\n\n予定管理についてお手伝いします。\n「予定」や「スケジュール」についてお聞かせください。"
                    }
                    send_line_message(event['replyToken'], [response_message])
        
        conn.close()
        return 'OK', 200
        
    except Exception as e:
        print(f'[AI Schedule Webhook] エラー: {e}')
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.close()
        return 'Internal Server Error', 500

@ai_schedule_webhook_bp.route('/webhook/<company_code>', methods=['POST'])
def ai_schedule_webhook_by_code(company_code):
    """AI予定秘書用のWebhookエンドポイント（企業コードベース）"""
    print(f'[AI Schedule Webhook] 企業コード {company_code} からのWebhook受信')
    
    # 企業コードから企業IDを取得
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id FROM companies WHERE company_code = %s', (company_code,))
    company = c.fetchone()
    
    if not company:
        print(f'[AI Schedule Webhook] 企業コード {company_code} が見つかりません')
        return 'Company not found', 404
    
    company_id = company[0]
    conn.close()
    
    # 企業IDベースのWebhook処理を呼び出し
    return ai_schedule_webhook(company_id)

@ai_schedule_webhook_bp.route('/webhook/line/<line_channel_id>', methods=['POST'])
def ai_schedule_webhook_by_line_channel(line_channel_id):
    """AI予定秘書用のWebhookエンドポイント（LINEチャネルIDベース）"""
    print(f'[AI Schedule Webhook] LINEチャネルID {line_channel_id} からのWebhook受信')
    
    # LINEチャネルIDから企業IDを取得
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT company_id FROM company_line_accounts WHERE line_channel_id = %s', (line_channel_id,))
    line_account = c.fetchone()
    
    if not line_account:
        print(f'[AI Schedule Webhook] LINEチャネルID {line_channel_id} が見つかりません')
        return 'Line channel not found', 404
    
    company_id = line_account[0]
    conn.close()
    
    # 企業IDベースのWebhook処理を呼び出し
    return ai_schedule_webhook(company_id) 