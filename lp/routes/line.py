from flask import Blueprint, request, jsonify
import os, json, hmac, hashlib, base64
from services.line_service import (
    send_line_message, get_db_connection, handle_add_content, handle_content_selection,
    handle_content_confirmation, handle_status_check, handle_cancel_request,
    handle_cancel_selection, get_welcome_message, get_not_registered_message
)
from utils.message_templates import get_menu_message, get_help_message, get_default_message

line_bp = Blueprint('line', __name__)

user_states = {}

@line_bp.route('/line/webhook', methods=['POST'])
def line_webhook():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.data.decode('utf-8')
    LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
    if LINE_CHANNEL_SECRET:
        try:
            hash = hmac.new(LINE_CHANNEL_SECRET.encode('utf-8'), body.encode('utf-8'), hashlib.sha256).digest()
            expected_signature = base64.b64encode(hash).decode('utf-8')
            if not hmac.compare_digest(signature, expected_signature):
                return 'Invalid signature', 400
        except Exception:
            return 'Signature verification error', 400
    try:
        events = json.loads(body).get('events', [])
        for event in events:
            if event.get('type') == 'message' and event['message'].get('type') == 'text':
                user_id = event['source']['userId']
                text = event['message']['text']
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('SELECT id, stripe_subscription_id, line_user_id FROM users WHERE line_user_id = ?', (user_id,))
                user = c.fetchone()
                if not user:
                    c.execute('SELECT id, stripe_subscription_id FROM users WHERE line_user_id IS NULL ORDER BY created_at DESC LIMIT 1')
                    user = c.fetchone()
                    if user:
                        c.execute('UPDATE users SET line_user_id = ? WHERE id = ?', (user_id, user[0]))
                        conn.commit()
                        send_line_message(event['replyToken'], get_welcome_message())
                    else:
                        send_line_message(event['replyToken'], get_not_registered_message())
                    conn.close()
                    continue
                user_id_db = user[0]
                stripe_subscription_id = user[1]
                state = user_states.get(user_id, None)
                if text == '追加':
                    user_states[user_id] = 'add_select'
                    handle_add_content(event['replyToken'], user_id_db, stripe_subscription_id)
                elif text == 'メニュー':
                    send_line_message(event['replyToken'], get_menu_message())
                elif text == 'ヘルプ':
                    send_line_message(event['replyToken'], get_help_message())
                elif text == '状態':
                    handle_status_check(event['replyToken'], user_id_db)
                elif text == '解約':
                    user_states[user_id] = 'cancel_select'
                    handle_cancel_request(event['replyToken'], user_id_db, stripe_subscription_id)
                elif state == 'add_select' and text in ['1', '2', '3', '4']:
                    handle_content_selection(event['replyToken'], user_id_db, stripe_subscription_id, text)
                    user_states[user_id] = None
                elif state == 'cancel_select' and all(x.strip().isdigit() for x in text.split(',')):
                    handle_cancel_selection(event['replyToken'], user_id_db, stripe_subscription_id, text)
                    user_states[user_id] = None
                elif text.lower() in ['はい', 'yes', 'y']:
                    handle_content_confirmation(event['replyToken'], user_id_db, stripe_subscription_id, '1', True)
                elif text.lower() in ['いいえ', 'no', 'n']:
                    handle_content_confirmation(event['replyToken'], user_id_db, stripe_subscription_id, '1', False)
                elif '@' in text and '.' in text and len(text) < 100:
                    # メールアドレスっぽい文字列が来た場合
                    import time
                    found = False
                    for _ in range(3):
                        c.execute('SELECT id, line_user_id FROM users WHERE email = ?', (text.strip(),))
                        user = c.fetchone()
                        if user:
                            found = True
                            break
                        time.sleep(2)
                    if found:
                        if user[1] is None:
                            c.execute('UPDATE users SET line_user_id = ? WHERE id = ?', (user_id, user[0]))
                            conn.commit()
                            send_line_message(event['replyToken'], 'LINE連携が完了しました。メニューや追加コマンドが利用できます。')
                        else:
                            send_line_message(event['replyToken'], 'このメールアドレスは既にLINE連携済みです。')
                    else:
                        send_line_message(event['replyToken'], 'ご登録メールアドレスが見つかりません。LPでご登録済みかご確認ください。')
                    conn.close()
                    continue
                else:
                    send_line_message(event['replyToken'], get_default_message())
                conn.close()
            # postbackイベントも同様に移動（省略）
    except Exception as e:
        import traceback
        traceback.print_exc()
    return jsonify({'status': 'ok'}) 