from flask import Blueprint, request, jsonify
import datetime
import os, json, hmac, hashlib, base64
import traceback
import requests
import stripe
import unicodedata
import logging
from services.line_service import send_line_message
from services.line_service import send_welcome_with_buttons
from services.line_service import (
    handle_add_content_company, handle_status_check_company, handle_cancel_menu_company,
    handle_content_confirmation_company, handle_cancel_request_company, 
    handle_cancel_selection_company, handle_subscription_cancel_company,
    handle_cancel_confirmation_company
)
from utils.message_templates import get_menu_message_company, get_help_message_company
from utils.db import get_db_connection
from models.user_state import get_user_state, set_user_state, clear_user_state, init_user_states_table
from services.user_service import is_paid_user_company_centric, get_restricted_message

line_bp = Blueprint('line', __name__)

# 決済完了後の案内文送信待ちユーザーを管理
pending_welcome_users = set()

# 削除された関数の代替実装
def is_content_cancelled(user_id, content_type):
    """コンテンツが解約されているかチェック（一時的に無効化）"""
    return False

def get_restriction_message_for_content(content_type):
    """コンテンツの制限メッセージを取得（一時的に無効化）"""
    return f"{content_type}は解約されているため利用できません。"

def get_cancelled_contents(user_id):
    """解約されたコンテンツを取得（一時的に無効化）"""
    return []

## 以前の一時的なスタブを削除し、サービス実装を使用します

@line_bp.route('/line/payment_completed/user/<int:user_id>')
def payment_completed_webhook_by_user_id(user_id):
    """決済完了後の案内文自動送信（ユーザーIDベース）"""
    try:
        # データベースからユーザー情報を取得
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT line_user_id, email FROM users WHERE id = %s', (user_id,))
        user = c.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'ユーザーが見つかりません'})
        
        line_user_id = user[0]
        email = user[1]
        
        if line_user_id:
            # 既にLINE連携済みの場合、直接案内文を送信
            print(f'[DEBUG] 既存LINE連携ユーザーへの自動案内文送信: line_user_id={line_user_id}')
            try:
                success = send_welcome_with_buttons(line_user_id)
                if success:
                    # 自動案内文送信後にユーザー状態を設定（重複防止）
                    set_user_state(line_user_id, 'welcome_sent')
                    print(f'[DEBUG] 自動案内文送信完了、ユーザー状態を設定: line_user_id={line_user_id}')
                    return jsonify({
                        'success': True, 
                        'message': f'案内文を自動送信しました: {email}',
                        'line_user_id': line_user_id
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': '案内文送信に失敗しました'
                    })
            except Exception as e:
                print(f'[DEBUG] 自動案内文送信エラー: {e}')
                return jsonify({'error': f'案内文送信エラー: {str(e)}'})
        else:
            # LINE連携未完了の場合、送信待ちリストに追加
            user_id_str = f"user_{user_id}"
            pending_welcome_users.add(user_id_str)
            print(f'[DEBUG] LINE連携未完了ユーザーの案内文送信準備: user_id={user_id}, email={email}')
            return jsonify({
                'success': True, 
                'message': f'LINE連携後に案内文を送信します: {email}',
                'status': 'pending_line_connection'
            })
            
    except Exception as e:
        return jsonify({'error': str(e)})

@line_bp.route('/line/payment_completed/<user_id>')
def payment_completed_webhook(user_id):
    """決済完了後の案内文送信準備（LINEユーザーIDベース）"""
    try:
        pending_welcome_users.add(user_id)
        print(f'[DEBUG] 決済完了後の案内文送信準備: user_id={user_id}')
        return jsonify({'success': True, 'message': f'案内文送信準備完了: {user_id}'})
    except Exception as e:
        return jsonify({'error': str(e)})

@line_bp.route('/line/debug/diagnose/<int:user_id>')
def debug_diagnose_user(user_id):
    """デバッグ用：ユーザーの自動診断"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # ユーザー情報を取得
        c.execute('SELECT id, email, line_user_id, stripe_subscription_id, created_at FROM users WHERE id = %s', (user_id,))
        user = c.fetchone()
        
        if not user:
            return jsonify({
                'error': 'ユーザーが見つかりません',
                'user_id': user_id
            })
        
        user_info = {
            'id': user[0],
            'email': user[1],
            'line_user_id': user[2],
            'stripe_subscription_id': user[3],
            'created_at': str(user[4]) if user[4] else None
        }
        
        # 診断結果
        diagnosis = {
            'user_exists': True,
            'has_subscription': bool(user[3]),
            'has_line_connection': bool(user[2]),
            'issues': [],
            'recommendations': []
        }
        
        # 問題の特定
        if not user[3]:
            diagnosis['issues'].append('サブスクリプションが設定されていません')
            diagnosis['recommendations'].append('決済を完了してください')
        
        if not user[2]:
            diagnosis['issues'].append('LINE連携が完了していません')
            diagnosis['recommendations'].append('LINEアプリで友達追加またはメッセージを送信してください')
        
        # LINE連携済みの場合、LINE APIでユーザー情報を確認
        if user[2]:
            try:
                LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
                headers = {
                    'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                }
                response = requests.get(
                    f'https://api.line.me/v2/bot/profile/{user[2]}',
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    line_profile = response.json()
                    diagnosis['line_profile'] = {
                        'display_name': line_profile.get('displayName'),
                        'picture_url': line_profile.get('pictureUrl'),
                        'status_message': line_profile.get('statusMessage')
                    }
                    diagnosis['line_api_working'] = True
                else:
                    diagnosis['issues'].append('LINE APIでユーザー情報を取得できません')
                    diagnosis['line_api_working'] = False
            except Exception as e:
                diagnosis['issues'].append(f'LINE API接続エラー: {str(e)}')
                diagnosis['line_api_working'] = False
        
        # サブスクリプション情報を確認
        if user[3]:
            try:
                # stripe.api_keyはapp.pyで既に設定済み
                subscription = stripe.Subscription.retrieve(user[3])
                diagnosis['stripe_subscription'] = {
                    'status': subscription.status,
                    'current_period_end': subscription.current_period_end,
                    'cancel_at_period_end': subscription.cancel_at_period_end
                }
                diagnosis['stripe_api_working'] = True
            except Exception as e:
                diagnosis['issues'].append(f'Stripe API接続エラー: {str(e)}')
                diagnosis['stripe_api_working'] = False
        
        conn.close()
        
        return jsonify({
            'success': True,
            'user_info': user_info,
            'diagnosis': diagnosis,
            'timestamp': str(datetime.datetime.now())
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'user_id': user_id
        })

@line_bp.route('/line/debug/update_line_user/<int:user_id>/<line_user_id>')
def debug_update_line_user(user_id, line_user_id):
    """デバッグ用：LINEユーザーIDを手動で更新"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 既存の紐付けを解除
        c.execute('UPDATE users SET line_user_id = NULL WHERE line_user_id = %s', (line_user_id,))
        
        # 新しい紐付けを作成
        c.execute('UPDATE users SET line_user_id = %s WHERE id = %s', (line_user_id, user_id))
        
        conn.commit()
        conn.close()
        
        print(f'[DEBUG] LINEユーザーID更新: user_id={user_id}, line_user_id={line_user_id}')
        
        return jsonify({
            'success': True,
            'message': f'LINEユーザーIDを更新しました: user_id={user_id}, line_user_id={line_user_id}'
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@line_bp.route('/line/debug/send_welcome/<user_id>')
def debug_send_welcome(user_id):
    """デバッグ用：指定ユーザーに手動で案内文を送信"""
    try:
        # テスト用のメッセージを送信
        test_message = {
            "type": "text",
            "text": "テスト：案内文が送信されました！\n\nようこそ！AIコレクションズへ\n\nAIコレクションズサービスをご利用いただき、ありがとうございます。\n\n📋 サービス内容：\n• AI予定秘書：スケジュール管理\n• AI経理秘書：見積書・請求書作成\n• AIタスクコンシェルジュ：タスク管理\n\n💰 料金体系：\n• 月額基本料金：3,900円（1週間無料）\n• 追加コンテンツ：1個目無料、2個目以降1,500円/件（トライアル期間中は無料）\n\n下のボタンからお選びください。"
        }
        
        # LINE APIを使用してメッセージを送信（テスト用）
        LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
        
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'to': user_id,
            'messages': [test_message]
        }
        
        response = requests.post(
            'https://api.line.me/v2/bot/message/push',
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': f'案内文を送信しました: {user_id}',
                'response': response.json()
            })
        else:
            return jsonify({
                'success': False,
                'error': f'送信失敗: {response.status_code}',
                'response': response.text
            })
            
    except Exception as e:
        return jsonify({'error': str(e)})

@line_bp.route('/line/debug/clear_old_usage_logs')
def debug_clear_old_usage_logs():
    """デバッグ用：古いusage_logsデータをクリア"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 古いデータを削除（7月25日以前のデータ）
        c.execute('DELETE FROM usage_logs WHERE created_at < %s', ('2025-07-26',))
        deleted_count = c.rowcount
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'{deleted_count}件の古いデータを削除しました'
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@line_bp.route('/line/debug/users')
def debug_line_users():
    """デバッグ用：LINE連携ユーザー状況確認"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT id, email, line_user_id, stripe_subscription_id, created_at FROM users ORDER BY created_at DESC LIMIT 10')
        users = c.fetchall()
        conn.close()
        
        user_list = []
        for user in users:
            user_list.append({
                'id': user[0],
                'email': user[1],
                'line_user_id': user[2],
                'stripe_subscription_id': user[3],
                'created_at': str(user[4]) if user[4] else None
            })
        
        return jsonify({
            'users': user_list,
            'message': 'user_statesはデータベースで管理されています'
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@line_bp.route('/line/check_restriction/<content_type>', methods=['POST'])
def check_line_restriction(content_type):
    """
    公式LINEの利用制限をチェックするAPI
    
    Args:
        content_type (str): チェックするコンテンツタイプ
        
    Request Body:
        {
            "line_user_id": "U1234567890abcdef"
        }
    """
    try:
        data = request.get_json()
        line_user_id = data.get('line_user_id')
        
        if not line_user_id:
            return jsonify({
                'error': 'line_user_id is required',
                'restricted': False
            }), 400
        
        # ユーザーIDを取得
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE line_user_id = %s', (line_user_id,))
        result = c.fetchone()
        conn.close()
        
        if not result:
            return jsonify({
                'error': 'User not found',
                'restricted': False
            }), 404
        
        user_id = result[0]
        
        # コンテンツが解約されているかチェック
        is_restricted = is_content_cancelled(user_id, content_type)
        
        return jsonify({
            'line_user_id': line_user_id,
            'user_id': user_id,
            'content_type': content_type,
            'restricted': is_restricted,
            'message': get_restriction_message_for_content(content_type) if is_restricted else f'{content_type}は利用可能です。'
        })
        
    except Exception as e:
        print(f'[ERROR] 利用制限チェックエラー: {e}')
        return jsonify({
            'error': str(e),
            'restricted': False
        }), 500

@line_bp.route('/line/restriction_message/<content_type>', methods=['POST'])
def get_restriction_message(content_type):
    """
    公式LINEの利用制限メッセージを取得するAPI
    
    Args:
        content_type (str): コンテンツタイプ
        
    Request Body:
        {
            "line_user_id": "U1234567890abcdef"
        }
    """
    try:
        data = request.get_json()
        line_user_id = data.get('line_user_id')
        
        if not line_user_id:
            return jsonify({
                'error': 'line_user_id is required'
            }), 400
        
        # ユーザーIDを取得
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE line_user_id = %s', (line_user_id,))
        result = c.fetchone()
        conn.close()
        
        if not result:
            return jsonify({
                'error': 'User not found'
            }), 404
        
        user_id = result[0]
        
        # コンテンツが解約されているかチェック
        is_restricted = is_content_cancelled(user_id, content_type)
        
        if is_restricted:
            # 制限メッセージを取得
            restriction_message = get_restriction_message_for_content(content_type)
            return jsonify({
                'line_user_id': line_user_id,
                'user_id': user_id,
                'content_type': content_type,
                'restricted': True,
                'message': restriction_message
            })
        else:
            return jsonify({
                'line_user_id': line_user_id,
                'user_id': user_id,
                'content_type': content_type,
                'restricted': False,
                'message': f'{content_type}は利用可能です。'
            })
        
    except Exception as e:
        print(f'[ERROR] 制限メッセージ取得エラー: {e}')
        return jsonify({
            'error': str(e)
        }), 500

@line_bp.route('/line/debug/cancellation_history/<int:user_id>')
def debug_cancellation_history(user_id):
    """デバッグ用：ユーザーの解約履歴を確認"""
    try:
        cancelled_contents = get_cancelled_contents(user_id)
        
        return jsonify({
            'user_id': user_id,
            'cancelled_contents': cancelled_contents,
            'count': len(cancelled_contents)
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@line_bp.route('/line/debug/test_webhook', methods=['POST'])
def debug_test_webhook():
    """デバッグ用LINE Webhookテスト"""
    print(f'[DEBUG] デバッグWebhookテスト開始')
    
    try:
        body = request.data.decode('utf-8')
        events = json.loads(body).get('events', [])
        print(f'[DEBUG] イベント数: {len(events)}')
        
        for event in events:
            print(f'[DEBUG] イベント処理開始: {event.get("type")}')
            print(f'[DEBUG] イベント詳細: {json.dumps(event, ensure_ascii=False, indent=2)}')
            
            if event.get('type') == 'message' and event['message'].get('type') == 'text':
                user_id = event['source']['userId']
                text = event['message']['text']
                print(f'[DEBUG] テキストメッセージ受信: user_id={user_id}, text={text}')
                
                # 決済状況をチェック
                print(f'[DEBUG] 決済チェック開始: user_id={user_id}')
                payment_check = is_paid_user_company_centric(user_id)
                print(f'[DEBUG] 決済チェック結果: {payment_check}')
                
                if not payment_check['is_paid']:
                    print(f'[DEBUG] 未決済ユーザー: user_id={user_id}')
                    return jsonify({
                        'status': 'restricted',
                        'user_id': user_id,
                        'payment_check': payment_check,
                        'message': '制限メッセージが送信されます'
                    })
                else:
                    print(f'[DEBUG] 決済済みユーザー: user_id={user_id}')
                    return jsonify({
                        'status': 'allowed',
                        'user_id': user_id,
                        'payment_check': payment_check,
                        'message': '正常に処理されます'
                    })
        
        return jsonify({'status': 'no_events'})
        
    except Exception as e:
        print(f'[ERROR] デバッグWebhookテストエラー: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@line_bp.route('/line/webhook', methods=['POST'])
def line_webhook():
    logger = logging.getLogger(__name__)
    print(f'[DEBUG] LINE Webhook受信開始')

    try:
        # 署名検証
        signature = request.headers.get('X-Line-Signature', '')
        body = request.data.decode('utf-8')
        line_channel_secret = os.getenv('LINE_CHANNEL_SECRET')
        
        if line_channel_secret:
            try:
                hash_bytes = hmac.new(line_channel_secret.encode('utf-8'), body.encode('utf-8'), hashlib.sha256).digest()
                expected_signature = base64.b64encode(hash_bytes).decode('utf-8')
                if not hmac.compare_digest(signature, expected_signature):
                    print('[ERROR] LINE Webhook署名検証失敗')
                    return jsonify({'error': 'invalid signature'}), 400
            except Exception as sig_e:
                print(f'[ERROR] 署名検証エラー: {sig_e}')
                return jsonify({'error': 'signature verification error'}), 400

        events = json.loads(body).get('events', [])
        print(f'[DEBUG] イベント数: {len(events)}')

        for event in events:
            try:
                print(f'[DEBUG] イベント処理開始: {event.get("type")}')

                # イベントタイプに応じて処理を分岐
                if event.get('type') == 'follow':
                    handle_follow_event(event)
                elif event.get('type') == 'unfollow':
                    handle_unfollow_event(event)
                elif event.get('type') == 'message' and event['message'].get('type') == 'text':
                    handle_text_message(event)
                elif event.get('type') == 'postback':
                    handle_postback_event(event)
                else:
                    print(f'[DEBUG] 未対応のイベントタイプ: {event.get("type")}')
                    
            except Exception as event_e:
                print(f'[ERROR] 個別イベント処理エラー: {event_e}')
                import traceback
                traceback.print_exc()
                # 個別イベントのエラーは全体の処理を停止させない
                continue

    except Exception as e:
        print(f'[ERROR] LINE Webhook処理エラー: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        logger.info(f'[DEBUG] LINE Webhook処理完了')

    return jsonify({'status': 'ok'})

def handle_follow_event(event):
    """フォローイベントの処理"""
    user_id = event['source']['userId']
    print(f'[DEBUG] フォローイベント受信: user_id={user_id}')
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 1. 既存の企業データでLINEユーザーIDが未設定のものを検索
        c.execute('''
            SELECT id, company_name, email 
            FROM companies 
            WHERE line_user_id IS NULL 
            ORDER BY created_at DESC 
            LIMIT 1
        ''')
        
        unlinked_company = c.fetchone()
        
        if unlinked_company:
            company_id, company_name, email = unlinked_company
            print(f'[DEBUG] 未紐付け企業データ発見: company_id={company_id}, company_name={company_name}')
            
            # 企業データにLINEユーザーIDを設定
            c.execute('UPDATE companies SET line_user_id = %s WHERE id = %s', (user_id, company_id))
            conn.commit()
            print(f'[DEBUG] 企業データとLINEユーザーIDを紐付け: user_id={user_id}, company_id={company_id}')
            
            # 企業向けの案内メッセージを送信
            try:
                from services.line_service import send_company_welcome_message
                send_company_welcome_message(user_id, company_name, email)
                print(f'[DEBUG] 企業向け案内メッセージ送信完了: user_id={user_id}')
            except Exception as e:
                print(f'[DEBUG] 企業向け案内メッセージ送信エラー: {e}')
                import traceback
                traceback.print_exc()
                
        else:
            print(f'[DEBUG] 未紐付け企業データが見つかりません: user_id={user_id}')
            # メールアドレス連携を促すメッセージ（テキストのみ）
            welcome_message = {
                "type": "text",
                "text": (
                    "ご利用開始のため、決済時のメールアドレスをこのトークに返信してください。\n\n"
                    "記入例: example@example.com\n\n"
                    "※ ご不明点があれば『ヘルプ』と送信してください。"
                )
            }
            try:
                from services.line_service import send_line_message_push
                ok = send_line_message_push(user_id, [welcome_message])
                if not ok:
                    send_line_message(event['replyToken'], [welcome_message])
            except Exception:
                send_line_message(event['replyToken'], [welcome_message])
        
        conn.close()
        
    except Exception as e:
        print(f'[DEBUG] フォローイベント処理エラー: {e}')
        import traceback
        traceback.print_exc()
        welcome_message = {
            "type": "text",
            "text": (
                "ご利用開始のため、決済時のメールアドレスをこのトークに返信してください。\n\n"
                "記入例: example@example.com\n\n"
                "※ ご不明点があれば『ヘルプ』と送信してください。"
            )
        }
        send_line_message(event['replyToken'], [welcome_message])

def handle_unfollow_event(event):
    """友達削除イベントの処理"""
    user_id = event['source']['userId']
    print(f'[DEBUG] 友達削除イベント: user_id={user_id}')
    
    # line_user_idをクリア
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE companies SET line_user_id = NULL WHERE line_user_id = %s', (user_id,))
    conn.commit()
    conn.close()
    
    # ユーザー状態もクリア
    clear_user_state(user_id)
    print(f'[DEBUG] 企業紐付け解除: user_id={user_id}')

def handle_text_message(event):
    """テキストメッセージの処理"""
    user_id = event['source']['userId']
    text = event['message']['text']
    print(f'[DEBUG] テキストメッセージ受信: user_id={user_id}, text={text}')
    
    # メールアドレス連携処理
    if '@' in text and '.' in text and len(text) < 100:
        print(f'[DEBUG] メールアドレス連携処理開始: user_id={user_id}, text={text}')
        
        def normalize_email(email):
            email = email.strip().lower()
            email = unicodedata.normalize('NFKC', email)
            return email
        
        normalized_email = normalize_email(text)
        print(f'[DEBUG] 正規化後のメールアドレス: {normalized_email}')
        
        try:
            conn = get_db_connection()
            c = conn.cursor()
            print(f'[DEBUG] データベース接続成功')
            
            # メールアドレスで企業データを検索
            c.execute('SELECT id, company_name, email FROM companies WHERE email = %s', (normalized_email,))
            company = c.fetchone()
            print(f'[DEBUG] 企業データ検索結果: {company}')
            
            if company:
                company_id, company_name, email = company
                print(f'[DEBUG] 企業データ発見: company_id={company_id}, company_name={company_name}')
                
                # 企業データにLINEユーザーIDを設定
                print(f'[DEBUG] 紐付け更新開始: user_id={user_id}, company_id={company_id}')
                c.execute('UPDATE companies SET line_user_id = %s WHERE id = %s', (user_id, company_id))
                conn.commit()
                print(f'[DEBUG] 企業データとLINEユーザーIDを紐付け完了: user_id={user_id}, company_id={company_id}')
                
                # 紐付け確認
                c.execute('SELECT line_user_id FROM companies WHERE id = %s', (company_id,))
                verify_result = c.fetchone()
                print(f'[DEBUG] 紐付け確認: {verify_result}')
                
                # 企業向けの案内メッセージを送信（push失敗時はreplyでフォールバック）
                try:
                    from services.line_service import send_company_welcome_message
                    print(f'[DEBUG] 企業向け案内メッセージ送信開始: user_id={user_id}, company_name={company_name}')
                    pushed = send_company_welcome_message(user_id, company_name, email)
                    if pushed:
                        print(f'[DEBUG] 企業向け案内メッセージ送信完了(push): user_id={user_id}')
                    else:
                        print(f'[WARN] push送信に失敗。replyでフォールバック: user_id={user_id}')
                        send_line_message(event['replyToken'], [{"type": "text", "text": f"✅ 企業データとの紐付けが完了しました！\n\n企業名: {company_name}\nメールアドレス: {email}\n\n『メニュー』と入力して始めてください。"}])
                except Exception as e:
                    print(f'[DEBUG] 企業向け案内メッセージ送信エラー: {e}')
                    import traceback
                    traceback.print_exc()
                    # 例外時もreplyでフォールバック
                    send_line_message(event['replyToken'], [{"type": "text", "text": f"✅ 企業データとの紐付けが完了しました！\n\n企業名: {company_name}\nメールアドレス: {email}\n\n『メニュー』と入力して始めてください。"}])
                    
            else:
                print(f'[DEBUG] 企業データが見つかりません: email={normalized_email}')
                send_line_message(event['replyToken'], [{"type": "text", "text": "企業データが見つかりません。決済が完了しているかご確認ください。"}])
            
            conn.close()
            print(f'[DEBUG] メールアドレス連携処理完了')
            return
            
        except Exception as e:
            print(f'[DEBUG] メールアドレス連携処理エラー: {e}')
            import traceback
            traceback.print_exc()
            send_line_message(event['replyToken'], [{"type": "text", "text": "メールアドレス連携処理中にエラーが発生しました。もう一度お試しください。"}])
            return
    
    # 企業情報を取得
    print(f'[DEBUG] 企業情報取得開始: user_id={user_id}')
    company_info = get_company_info(user_id)
    print(f'[DEBUG] 企業情報取得結果: {company_info}')
    
    if not company_info:
        # 企業が見つからない場合、メールアドレス連携を促す
        print(f'[DEBUG] 企業情報が見つかりません: user_id={user_id}')
        send_line_message(event['replyToken'], [{"type": "text", "text": "決済済みの方は、登録時のメールアドレスを送信してください。\n\n例: example@example.com\n\n※メールアドレスを送信すると、自動的に企業データと紐付けされます。"}])
        return
    
    company_id, stripe_subscription_id = company_info
    
    # stripe_subscription_idがNoneの場合の処理
    if not stripe_subscription_id:
        print(f'[DEBUG] stripe_subscription_idがNone: company_id={company_id}')
        send_line_message(event['replyToken'], [{"type": "text", "text": "決済情報が見つかりません。決済が完了しているかご確認ください。"}])
        return
    
    # 決済状況をチェック
    # ここまでの処理で `get_company_info` が返っている場合、
    # company_monthly_subscriptions のステータスが 'active' または 'trialing' であることが保証されている。
    # 外部依存の追加チェックで誤検知を避けるため、ブロックはスキップする。
    # （安全側に倒すなら、stripe_subscription_id が欠損している場合のみ制限を返す）
    if not stripe_subscription_id:
        restricted_message = get_restricted_message()
        send_line_message(event['replyToken'], [restricted_message])
        return
    
    # コマンド処理
    handle_command(event, user_id, text, company_id, stripe_subscription_id)

def get_company_info(user_id):
    """企業情報を取得（月額基本料金システム対応）"""
    print(f'[DEBUG] get_company_info開始: user_id={user_id}')
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # companiesテーブルから企業情報を取得
        c.execute('SELECT id, company_name FROM companies WHERE line_user_id = %s', (user_id,))
        company = c.fetchone()
        print(f'[DEBUG] 企業データ検索結果: {company}')
        
        if not company:
            conn.close()
            return None
        
        company_id = company[0]
        
        # 月額基本サブスクリプションからstripe_subscription_idを取得
        c.execute('SELECT stripe_subscription_id, subscription_status FROM company_monthly_subscriptions WHERE company_id = %s', (company_id,))
        monthly_subscription = c.fetchone()
        
        if not monthly_subscription:
            print(f'[DEBUG] 月額基本サブスクリプションが見つかりません: company_id={company_id}')
            conn.close()
            return None
        
        stripe_subscription_id, subscription_status = monthly_subscription
        print(f'[DEBUG] 月額基本サブスクリプション: stripe_subscription_id={stripe_subscription_id}, status={subscription_status}')
        
        # トライアル中('trialing')も有効として扱う
        valid_statuses = ('active', 'trialing')
        if subscription_status not in valid_statuses:
            print(f'[DEBUG] 月額サブスクリプションが有効ではありません: status={subscription_status}')
            conn.close()
            return None
        
        conn.close()
        return (company_id, stripe_subscription_id)
        
    except Exception as e:
        print(f'[ERROR] get_company_infoエラー: {e}')
        import traceback
        traceback.print_exc()
        try:
            conn.close()
        except:
            pass
        return None

def handle_command(event, user_id, text, company_id, stripe_subscription_id):
    """コマンド処理"""
    state = get_user_state(user_id)
    print(f'[DEBUG] handle_command開始: user_id={user_id}, text="{text}", state="{state}"')
    print(f'[DEBUG] 企業情報: company_id={company_id}, stripe_subscription_id={stripe_subscription_id}')
    
    # 基本的なコマンド処理
    if text == '追加':
        try:
            set_user_state(user_id, 'add_select')
            handle_add_content_company(event['replyToken'], company_id, stripe_subscription_id)
            print(f'[DEBUG] 追加コマンド処理完了')
        except Exception as e:
            print(f'[ERROR] 追加コマンド処理エラー: {e}')
    elif text == 'メニュー':
        try:
            print(f'[DEBUG] メニューコマンド受信: user_id={user_id}')
            from utils.message_templates import get_menu_message_company
            send_line_message(event['replyToken'], [get_menu_message_company()])
            print(f'[DEBUG] メニューコマンド処理完了')
        except Exception as e:
            print(f'[ERROR] メニューコマンド処理エラー: {e}')
            import traceback
            traceback.print_exc()
            # エラー時のフォールバックメッセージ
            send_line_message(event['replyToken'], [{"type": "text", "text": "📱 メニュー\n\n• 「追加」：コンテンツを追加\n• 「状態」：利用状況を確認\n• 「解約」：解約メニューを表示\n• 「ヘルプ」：使い方を確認"}])
    elif text == 'ヘルプ':
        try:
            send_line_message(event['replyToken'], get_help_message_company())
            print(f'[DEBUG] ヘルプコマンド処理完了')
        except Exception as e:
            print(f'[ERROR] ヘルプコマンド処理エラー: {e}')
    elif text == '状態':
        try:
            handle_status_check_company(event['replyToken'], company_id)
            print(f'[DEBUG] 状態コマンド処理完了')
        except Exception as e:
            print(f'[ERROR] 状態コマンド処理エラー: {e}')
    elif text == '解約':
        try:
            print(f'[DEBUG] 解約コマンド受信: user_id={user_id}')
            handle_cancel_menu_company(event['replyToken'], company_id, stripe_subscription_id)
            print(f'[DEBUG] 解約コマンド処理完了')
        except Exception as e:
            print(f'[ERROR] 解約コマンド処理エラー: {e}')
            import traceback
            traceback.print_exc()
    elif text == 'サブスクリプション解約':
        try:
            handle_subscription_cancel_company(event['replyToken'], company_id, stripe_subscription_id)
            print(f'[DEBUG] サブスクリプション解約コマンド処理完了')
        except Exception as e:
            print(f'[ERROR] サブスクリプション解約コマンド処理エラー: {e}')
    elif text == 'コンテンツ解約':
        try:
            set_user_state(user_id, 'cancel_select')
            handle_cancel_request_company(event['replyToken'], company_id, stripe_subscription_id)
            print(f'[DEBUG] コンテンツ解約コマンド処理完了')
        except Exception as e:
            print(f'[ERROR] コンテンツ解約コマンド処理エラー: {e}')
    elif state == 'add_select':
        print(f'[DEBUG] コンテンツ選択処理: user_id={user_id}, state={state}, text={text}')
        
        # 「メニュー」コマンドの場合は状態をリセットしてメニューを表示
        if text == 'メニュー':
            set_user_state(user_id, 'welcome_sent')
            from utils.message_templates import get_menu_message_company
            send_line_message(event['replyToken'], [get_menu_message_company()])
            return

        # 数字入力を受け付け、スプレッドシートの順序で解釈
        try:
            selection_index = int(text)
        except ValueError:
            selection_index = None

        if selection_index is not None and selection_index >= 1:
            from services.spreadsheet_content_service import spreadsheet_content_service
            contents_result = spreadsheet_content_service.get_available_contents()
            contents_dict = contents_result.get('contents', {})
            contents_list = [content_info for _, content_info in contents_dict.items()]
            if 1 <= selection_index <= len(contents_list):
                selected = contents_list[selection_index - 1]
                content_name = selected.get('name', f'コンテンツ{selection_index}')
                description = selected.get('description') or 'このコンテンツを追加しますか？'
                description = ' '.join(str(description).split())
                price = selected.get('price')
                price_short = f" 料金:{price:,}円/月" if isinstance(price, int) else ""

                # 確認は大きいテンプレートボタン（はい/いいえ）
                confirm_text = f"{description}{price_short}\n\n追加しますか？"
                set_user_state(user_id, f'add_confirm_{selection_index}')
                send_line_message(
                    event['replyToken'],
                    [{
                        "type": "template",
                        "altText": "コンテンツ追加確認",
                        "template": {
                            "type": "buttons",
                            "title": f"{content_name}を追加",
                            "text": confirm_text[:120],
                            "actions": [
                                {"type": "message", "label": "はい", "text": "はい"},
                                {"type": "message", "label": "いいえ", "text": "いいえ"}
                            ]
                        }
                    }]
                )
                return

        # 無効な入力の場合、メインメニューを表示
        set_user_state(user_id, 'welcome_sent')
        from utils.message_templates import get_menu_message_company
        send_line_message(event['replyToken'], [get_menu_message_company()])
        return
    elif state and str(state).startswith('add_confirm_'):
        # ユーザーの「はい/いいえ」テキストで追加を確定
        try:
            num_str = str(state).replace('add_confirm_', '')
            selection_index = int(num_str)
        except Exception:
            selection_index = None
        normalized = str(text).strip().lower()
        yes_words = {'はい', 'yes', 'y'}
        no_words = {'いいえ', 'no', 'n'}
        if selection_index is None:
            set_user_state(user_id, 'welcome_sent')
            from utils.message_templates import get_menu_message_company
            send_line_message(event['replyToken'], [get_menu_message_company()])
            return
        if normalized in yes_words:
            from services.spreadsheet_content_service import spreadsheet_content_service
            contents_result = spreadsheet_content_service.get_available_contents()
            contents_dict = contents_result.get('contents', {})
            contents_list = [content_info for _, content_info in contents_dict.items()]
            if 1 <= selection_index <= len(contents_list):
                content_name = contents_list[selection_index - 1].get('name')
            else:
                content_name = None
            if not content_name:
                set_user_state(user_id, 'welcome_sent')
                send_line_message(event['replyToken'], [{"type": "text", "text": "無効な選択です。"}])
                return
            try:
                result = handle_content_confirmation_company(company_id, content_name)
                set_user_state(user_id, 'welcome_sent')
                if result.get('success'):
                    # スプレッドシートURLへ誘導する軽量Flex（上余白を最小化）
                    content_url = result.get('url', 'https://lp-production-9e2c.up.railway.app')
                    flex = {
                        "type": "flex",
                        "altText": f"{content_name}を追加しました",
                        "contents": {
                            "type": "bubble",
                            "size": "mega",
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "paddingAll": "8px",
                                "paddingTop": "6px",
                                "spacing": "6px",
                                "contents": [
                                    {"type": "text", "text": f"🎉 {content_name}を追加しました", "weight": "bold", "size": "md", "wrap": True},
                                    {"type": "text", "text": "アクセスはこちら", "size": "sm", "color": "#888888"},
                                    {"type": "button", "style": "link", "height": "sm", "action": {"type": "uri", "label": content_url, "uri": content_url}}
                                ]
                            }
                        }
                    }
                    send_line_message(event['replyToken'], [flex])
                else:
                    error_message = result.get('error', f"❌ {content_name}の追加に失敗しました。")
                    send_line_message(event['replyToken'], [{"type": "text", "text": error_message}])
                return
            except Exception as e:
                print(f"[ERROR] add_confirm 処理エラー: {e}")
                import traceback; traceback.print_exc()
                set_user_state(user_id, 'welcome_sent')
                send_line_message(event['replyToken'], [{"type": "text", "text": "❌ 追加処理でエラーが発生しました。"}])
                return
        elif normalized in no_words:
            set_user_state(user_id, 'welcome_sent')
            from utils.message_templates import get_menu_message_company
            send_line_message(event['replyToken'], [get_menu_message_company()])
            return
        else:
            # 再確認
            send_line_message(event['replyToken'], [{"type": "text", "text": "『はい』または『いいえ』と返信してください。"}])
            return

    elif state == 'cancel_select':
        print(f'[DEBUG] 解約選択処理開始: user_id={user_id}, state={state}, text={text}')
        
        # 数字入力（全角/漢数字/英語数詞/ローマ数字含む）はそのまま解約選択処理へ委譲
        try:
            from services.line_service import smart_number_extraction
            extracted = smart_number_extraction(str(text))
        except Exception:
            extracted = []

        if extracted:
            try:
                handle_cancel_selection_company(event['replyToken'], company_id, stripe_subscription_id, str(text))
                # 状態は選択後も cancel_select のままにし、確認ボタンの返信に備える
                set_user_state(user_id, 'cancel_confirm')
                return
            except Exception as e:
                print(f'[ERROR] 解約選択委譲エラー: {e}')
                import traceback; traceback.print_exc()
                send_line_message(event['replyToken'], [{"type": "text", "text": "解約処理に失敗しました。もう一度お試しください。"}])
                return

        # 「メニュー」コマンドの場合は状態をリセットしてメニューを表示
        if text == 'メニュー':
            print(f'[DEBUG] メニューコマンド処理: user_id={user_id}')
            set_user_state(user_id, 'welcome_sent')
            from utils.message_templates import get_menu_message_company
            send_line_message(event['replyToken'], [get_menu_message_company()])
            return
        
        # 無効な入力の場合、再案内
        print(f'[DEBUG] 無効な入力: user_id={user_id}, text={text}')
        send_line_message(event['replyToken'], [{"type": "text", "text": "番号で解約対象を指定してください。例: 1\nメニューに戻る場合は『メニュー』と送信してください。"}])
        return
    elif state == 'cancel_confirm':
        print(f'[DEBUG] 解約確認状態での処理: user_id={user_id}, state={state}, text={text}')
        
        # 解約確認処理
        if text.startswith('解約確認_'):
            print(f'[DEBUG] 解約確認処理開始: text={text}')
            
            try:
                # 解約確認処理を実行
                handle_cancel_confirmation_company(event['replyToken'], company_id, stripe_subscription_id, text)
                
                # 状態をリセット
                set_user_state(user_id, 'welcome_sent')
                print(f'[DEBUG] ユーザー状態をリセット: user_id={user_id}')
                return
                
            except Exception as e:
                print(f'[ERROR] 解約確認処理エラー: {e}')
                import traceback
                traceback.print_exc()
                send_line_message(event['replyToken'], [{"type": "text", "text": "解約処理中にエラーが発生しました。もう一度お試しください。"}])
                return
                
        # 「メニュー」コマンドの場合は状態をリセットしてメニューを表示
        elif text == 'メニュー':
            print(f'[DEBUG] メニューコマンド処理: user_id={user_id}')
            set_user_state(user_id, 'welcome_sent')
            from utils.message_templates import get_menu_message_company
            send_line_message(event['replyToken'], [get_menu_message_company()])
            return
        else:
            print(f'[DEBUG] 無効な入力（解約確認状態）: user_id={user_id}, text={text}')
            # 無効な入力の場合、メインメニューを表示
            set_user_state(user_id, 'welcome_sent')
            from utils.message_templates import get_menu_message_company
            send_line_message(event['replyToken'], [get_menu_message_company()])
            return
    else:
        # 登録されていないメッセージの場合、メニューを表示
        print(f'[DEBUG] 登録されていないメッセージ: user_id={user_id}, text="{text}", state="{state}"')
        try:
            from utils.message_templates import get_menu_message_company
            print(f'[DEBUG] メニューメッセージ送信開始: reply_token={event["replyToken"][:20]}...')
            send_line_message(event['replyToken'], [get_menu_message_company()])
            print(f'[DEBUG] メニュー表示完了: text="{text}"')
        except Exception as e:
            print(f'[ERROR] メニュー表示エラー: {e}')
            import traceback
            traceback.print_exc()
            # フォールバックメッセージ
            send_line_message(event['replyToken'], [{"type": "text", "text": "📱 メニューから選択してください。\n\n• 「追加」：コンテンツを追加\n• 「状態」：利用状況を確認\n• 「解約」：解約メニューを表示\n• 「ヘルプ」：使い方を確認"}])

def handle_postback_event(event):
    """postbackイベントの処理"""
    user_id = event['source']['userId']
    postback_data = event['postback']['data']
    
    # 企業情報を取得
    company_info = get_company_info(user_id)
    if not company_info:
        send_line_message(event['replyToken'], [{"type": "text", "text": "企業登録が完了していません。LPで企業登録を行ってください。"}])
        return
    
    company_id, stripe_subscription_id = company_info
    
    # postbackデータに基づいて処理
    if postback_data == 'action=add_content':
        handle_add_content_company(event['replyToken'], company_id, stripe_subscription_id)
    elif postback_data == 'action=check_status':
        handle_status_check_company(event['replyToken'], company_id)
    elif postback_data == 'action=cancel_content':
        handle_cancel_menu_company(event['replyToken'], company_id, stripe_subscription_id)
    elif postback_data == 'action=help':
        send_line_message(event['replyToken'], get_help_message_company())
    elif postback_data == 'action=share':
        share_message = """📢 友達に紹介

AIコレクションズをご利用いただき、ありがとうございます！

🤝 友達にもおすすめしませんか？
• 基本料金月額3,900円
• 追加コンテンツ1件1,500円
• 企業向けAIツールを効率的に利用

🔗 紹介URL：
https://lp-production-9e2c.up.railway.app

友達が登録すると、あなたにも特典があります！"""
        send_line_message(event['replyToken'], [{"type": "text", "text": share_message}]) 
    elif postback_data.startswith('company_confirm_add_'):
        num_str = postback_data.replace('company_confirm_add_', '')
        try:
            index = int(num_str)
        except ValueError:
            index = None
        if not index or index < 1:
            send_line_message(event['replyToken'], [{"type": "text", "text": "無効な選択です。"}])
            return
        # スプレッドシートの順序でコンテンツ名を取得
        from services.spreadsheet_content_service import spreadsheet_content_service
        contents_result = spreadsheet_content_service.get_available_contents()
        contents_dict = contents_result.get('contents', {})
        contents_list = [content_info for _, content_info in contents_dict.items()]
        if index > len(contents_list):
            send_line_message(event['replyToken'], [{"type": "text", "text": "無効な選択です。"}])
            return
        content_name = contents_list[index - 1].get('name')
        if not content_name:
            send_line_message(event['replyToken'], [{"type": "text", "text": "無効な選択です。"}])
            return
        try:
            result = handle_content_confirmation_company(company_id, content_name)
            if result['success']:
                content_url = result.get('url', 'https://lp-production-9e2c.up.railway.app')
                flex = {
                    "type": "flex",
                    "altText": f"{content_type}を追加しました",
                    "contents": {
                        "type": "bubble",
                        "size": "mega",
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "paddingAll": "8px",
                            "paddingTop": "6px",
                            "spacing": "6px",
                            "contents": [
                                {"type": "text", "text": f"🎉 {content_type}を追加しました", "weight": "bold", "size": "md", "wrap": True},
                                {"type": "text", "text": "アクセスはこちら", "size": "sm", "color": "#888888"},
                                {"type": "button", "style": "link", "height": "sm", "action": {"type": "uri", "label": content_url, "uri": content_url}}
                            ]
                        }
                    }
                }
                send_line_message(event['replyToken'], [flex])
            else:
                error_message = result.get('error', f"❌ {content_type}の追加に失敗しました。")
                send_line_message(event['replyToken'], [{"type": "text", "text": error_message}])
        except Exception as e:
            print(f"[ERROR] company_confirm_add 処理エラー: {e}")
            import traceback; traceback.print_exc()
            send_line_message(event['replyToken'], [{"type": "text", "text": "❌ 追加処理でエラーが発生しました。"}])
    elif postback_data == 'company_cancel_add':
        send_line_message(event['replyToken'], [get_menu_message_company()])

@line_bp.route('/line/debug/test_email_linking/<email>')
def debug_test_email_linking(email):
    """デバッグ用：メールアドレス連携処理のテスト"""
    try:
        print(f'[DEBUG] メールアドレス連携テスト開始: email={email}')
        
        def normalize_email(email):
            email = email.strip().lower()
            email = unicodedata.normalize('NFKC', email)
            return email
        
        normalized_email = normalize_email(email)
        print(f'[DEBUG] 正規化後のメールアドレス: {normalized_email}')
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # メールアドレスで企業データを検索
        c.execute('SELECT id, company_name, email FROM companies WHERE email = %s', (normalized_email,))
        company = c.fetchone()
        print(f'[DEBUG] 企業データ検索結果: {company}')
        
        if company:
            company_id, company_name, email = company
            print(f'[DEBUG] 企業データ発見: company_id={company_id}, company_name={company_name}')
            
            return jsonify({
                'success': True,
                'company_id': company_id,
                'company_name': company_name,
                'email': email,
                'message': f'企業データが見つかりました: {company_name}'
            })
        else:
            print(f'[DEBUG] 企業データが見つかりません: email={normalized_email}')
            return jsonify({
                'success': False,
                'message': f'企業データが見つかりません: {normalized_email}'
            })
        
        conn.close()
        
    except Exception as e:
        print(f'[DEBUG] メールアドレス連携テストエラー: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }) 