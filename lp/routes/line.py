from flask import Blueprint, request, jsonify
import os, json, hmac, hashlib, base64
import traceback
import requests
import stripe
import unicodedata
import logging
from services.line_service import send_line_message
from services.line_service import (
    handle_add_content, handle_content_selection, handle_cancel_request,
    handle_cancel_selection, handle_subscription_cancel, handle_cancel_menu,
    handle_status_check, send_welcome_with_buttons, get_welcome_message,
    get_not_registered_message, extract_numbers_from_text, validate_selection_numbers,
    smart_number_extraction, handle_cancel_confirmation, handle_content_confirmation,
    handle_add_content_company, handle_status_check_company, handle_cancel_menu_company,
    handle_content_confirmation_company, handle_cancel_request_company, 
    handle_cancel_selection_company, handle_subscription_cancel_company
)
from utils.message_templates import get_menu_message, get_help_message, get_default_message, get_help_message_company, get_menu_message_company
from utils.db import get_db_connection
from models.user_state import get_user_state, set_user_state, clear_user_state, init_user_states_table
from services.user_service import is_paid_user, is_paid_user_company_centric, get_restricted_message, is_paid_user_by_email, update_line_user_id_for_email
# from services.cancellation_service import is_content_cancelled, get_restriction_message_for_content  # 削除された関数

line_bp = Blueprint('line', __name__)

# 永続的な状態管理を使用するため、メモリ上のuser_statesは使用しない
# user_states = {}
# 決済完了後の案内文送信待ちユーザーを管理
pending_welcome_users = set()

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
                response = requests.get(f'https://api.line.me/v2/bot/profile/{user[2]}', headers=headers)
                
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
        
        response = requests.post('https://api.line.me/v2/bot/message/push', headers=headers, json=data)
        
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
        # is_restricted = is_content_cancelled(user_id, content_type)  # 削除された関数
        is_restricted = False  # 一時的に無効化
        
        return jsonify({
            'line_user_id': line_user_id,
            'user_id': user_id,
            'content_type': content_type,
            'restricted': is_restricted,
            'message': f'{content_type}は解約されているため利用できません。' if is_restricted else f'{content_type}は利用可能です。'
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
        # is_restricted = is_content_cancelled(user_id, content_type)  # 削除された関数
        is_restricted = False  # 一時的に無効化
        
        if is_restricted:
            # 制限メッセージを取得
            # restriction_message = get_restriction_message_for_content(content_type)  # 削除された関数
            restriction_message = f"{content_type}は解約されているため利用できません。"
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
        # from services.cancellation_service import get_cancelled_contents  # 削除された関数
        
        # cancelled_contents = get_cancelled_contents(user_id)  # 削除された関数
        cancelled_contents = []  # 一時的に空リスト
        
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
        body = request.data.decode('utf-8')
        events = json.loads(body).get('events', [])
        print(f'[DEBUG] イベント数: {len(events)}')
        
        for event in events:
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
    
    except Exception as e:
        print(f'[ERROR] LINE Webhook処理エラー: {e}')
        traceback.print_exc()
    finally:
        logger.info(f'[DEBUG] LINE Webhook処理完了')
    
    return jsonify({'status': 'ok'})

def handle_follow_event(event):
    """友達追加イベントの処理"""
    user_id = event['source']['userId']
    print(f'[DEBUG] 友達追加イベント: user_id={user_id}')
    
    # 既に案内文が送信されているかチェック
    if get_user_state(user_id) == 'welcome_sent':
        print(f'[DEBUG] 既に案内文送信済み、スキップ: user_id={user_id}')
        return
    
    try:
        send_welcome_with_buttons(event['replyToken'])
        print(f'[DEBUG] ウェルカムメッセージ送信完了: user_id={user_id}')
        set_user_state(user_id, 'welcome_sent')
    except Exception as e:
        print(f'[DEBUG] ウェルカムメッセージ送信エラー: {e}')
        set_user_state(user_id, 'welcome_sent')

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
    
    # 企業情報を取得
    company_info = get_company_info(user_id)
    if not company_info:
        # 企業が見つからない場合
        send_line_message(event['replyToken'], [{"type": "text", "text": "企業登録が完了していません。LPで企業登録を行ってください。"}])
        return
    
    company_id, stripe_subscription_id = company_info
    
    # 決済状況をチェック
    payment_check = is_paid_user_company_centric(user_id)
    if not payment_check['is_paid']:
        restricted_message = get_restricted_message()
        send_line_message(event['replyToken'], [restricted_message])
        return
    
    # コマンド処理
    handle_command(event, user_id, text, company_id, stripe_subscription_id)

def get_company_info(user_id):
    """企業情報を取得"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # companiesテーブルから企業情報を取得
    c.execute('SELECT id, company_name FROM companies WHERE line_user_id = %s', (user_id,))
    company = c.fetchone()
    
    if not company:
        conn.close()
        return None
    
    company_id = company[0]
    
    # stripe_subscription_idを取得
    c.execute('SELECT stripe_subscription_id FROM company_subscriptions WHERE company_id = %s AND subscription_status = %s LIMIT 1', (company_id, 'active'))
    subscription = c.fetchone()
    stripe_subscription_id = subscription[0] if subscription else None
    
    conn.close()
    return (company_id, stripe_subscription_id)

def handle_command(event, user_id, text, company_id, stripe_subscription_id):
    """コマンド処理"""
    state = get_user_state(user_id)
    
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
            from utils.message_templates import get_menu_message_company
            send_line_message(event['replyToken'], [get_menu_message_company()])
            print(f'[DEBUG] メニューコマンド処理完了')
        except Exception as e:
            print(f'[ERROR] メニューコマンド処理エラー: {e}')
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
            handle_cancel_menu_company(event['replyToken'], company_id, stripe_subscription_id)
            print(f'[DEBUG] 解約コマンド処理完了')
        except Exception as e:
            print(f'[ERROR] 解約コマンド処理エラー: {e}')
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
        
        # コンテンツ選択
        if text in ['1', '2', '3']:
            print(f'[DEBUG] コンテンツ選択: text={text}')
            # コンテンツ確認処理
            content_mapping = {
                '1': 'AI予定秘書',
                '2': 'AI経理秘書',
                '3': 'AIタスクコンシェルジュ'
            }
            content_type = content_mapping.get(text)
            if content_type:
                try:
                    result = handle_content_confirmation_company(company_id, content_type)
                    print(f'[DEBUG] コンテンツ追加結果: {result}')
                    if result['success']:
                        # 成功メッセージを送信
                        success_message = f"🎉 {content_type}を追加しました！\n\n✨ {result.get('description', '新しいコンテンツが利用可能になりました')}\n\n🔗 アクセスURL：\n{result.get('url', 'https://lp-production-9e2c.up.railway.app')}\n\n💡 使い方：\n{result.get('usage', 'LINEアカウントからご利用いただけます')}\n\n📱 何かお手伝いできることはありますか？\n• 「追加」：他のコンテンツを追加\n• 「状態」：利用状況を確認\n• 「メニュー」：メインメニューに戻る\n• 「ヘルプ」：使い方を確認"
                        send_line_message(event['replyToken'], [{"type": "text", "text": success_message}])
                    else:
                        error_message = f"❌ {content_type}の追加に失敗しました。\n\nエラー: {result.get('error', '不明なエラー')}\n\nもう一度お試しください。"
                        send_line_message(event['replyToken'], [{"type": "text", "text": error_message}])
                except Exception as e:
                    print(f'[ERROR] コンテンツ追加処理エラー: {e}')
                    import traceback
                    traceback.print_exc()
                    error_message = f"❌ {content_type}の追加中にエラーが発生しました。\n\nエラー: {str(e)}\n\nもう一度お試しください。"
                    send_line_message(event['replyToken'], [{"type": "text", "text": error_message}])
            set_user_state(user_id, 'welcome_sent')
            return
        # 「メニュー」コマンドの場合は状態をリセットしてメニューを表示
        elif text == 'メニュー':
            set_user_state(user_id, 'welcome_sent')
            from utils.message_templates import get_menu_message_company
            send_line_message(event['replyToken'], [get_menu_message_company()])
            return
        else:
            # 無効な入力の場合、コンテンツ選択を促すメッセージを送信
            send_line_message(event['replyToken'], [{"type": "text", "text": "1〜3の数字でコンテンツを選択してください。\n\nまたは「メニュー」でメインメニューに戻ります。"}])
            return
    elif state == 'cancel_select':
        print(f'[DEBUG] 解約選択処理: user_id={user_id}, state={state}, text={text}')
        
        # 解約対象のコンテンツを選択
        if text in ['1', '2', '3']:
            print(f'[DEBUG] 解約対象コンテンツ選択: text={text}')
            # 解約確認状態に設定
            set_user_state(user_id, f'cancel_confirm_{text}')
            # 解約確認メッセージを送信
            handle_cancel_selection_company(event['replyToken'], company_id, stripe_subscription_id, text)
            return
        # 「メニュー」コマンドの場合は状態をリセットしてメニューを表示
        elif text == 'メニュー':
            set_user_state(user_id, 'welcome_sent')
            from utils.message_templates import get_menu_message_company
            send_line_message(event['replyToken'], [get_menu_message_company()])
            return
        # 主要なコマンドの場合は通常の処理に切り替え
        elif text == '追加':
            set_user_state(user_id, 'add_select')
            handle_add_content_company(event['replyToken'], company_id, stripe_subscription_id)
            return
        elif text == '状態':
            handle_status_check_company(event['replyToken'], company_id)
            return
        elif text == 'ヘルプ':
            send_line_message(event['replyToken'], get_help_message_company())
            return
        else:
            # 無効な入力の場合、解約選択を促すメッセージを送信
            send_line_message(event['replyToken'], [{"type": "text", "text": "1〜3の数字で解約するコンテンツを選択してください。\n\nまたは「メニュー」でメインメニューに戻ります。"}])
            return
    else:
        # 無効な入力の場合、メニューを表示
        try:
            from utils.message_templates import get_menu_message_company
            send_line_message(event['replyToken'], [get_menu_message_company()])
            print(f'[DEBUG] 無効な入力に対するメニュー表示完了: text={text}')
        except Exception as e:
            print(f'[ERROR] メニュー表示エラー: {e}')
            # フォールバックメッセージ
            send_line_message(event['replyToken'], [{"type": "text", "text": "メニューから選択してください。"}])

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