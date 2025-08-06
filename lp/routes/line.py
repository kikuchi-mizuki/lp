from flask import Blueprint, request, jsonify
import os, json, hmac, hashlib, base64
import traceback
import requests
import stripe
import unicodedata
from services.line_service import send_line_message
from services.line_service import (
    handle_add_content, handle_content_selection, handle_cancel_request,
    handle_cancel_selection, handle_subscription_cancel, handle_cancel_menu,
    handle_status_check, send_welcome_with_buttons, get_welcome_message,
    get_not_registered_message, extract_numbers_from_text, validate_selection_numbers,
    smart_number_extraction, handle_cancel_confirmation, handle_content_confirmation,
    handle_add_content_company, handle_status_check_company, handle_cancel_menu_company,
    handle_content_confirmation_company
)
from utils.message_templates import get_menu_message, get_help_message, get_default_message, get_help_message_company
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
    print(f'[DEBUG] LINE Webhook受信開始')
    print(f'[DEBUG] リクエストメソッド: {request.method}')
    print(f'[DEBUG] リクエストヘッダー: {dict(request.headers)}')
    print(f'[DEBUG] リクエストボディ: {request.data.decode("utf-8")}')
    
    signature = request.headers.get('X-Line-Signature', '')
    body = request.data.decode('utf-8')
    LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
    
    # 署名検証（本番環境用）
    if LINE_CHANNEL_SECRET:
        try:
            hash = hmac.new(LINE_CHANNEL_SECRET.encode('utf-8'), body.encode('utf-8'), hashlib.sha256).digest()
            expected_signature = base64.b64encode(hash).decode('utf-8')
            if not hmac.compare_digest(signature, expected_signature):
                print(f'[DEBUG] 署名検証失敗: expected={expected_signature}, received={signature}')
                return 'Invalid signature', 400
            else:
                print(f'[DEBUG] 署名検証成功')
        except Exception as e:
            print(f'[DEBUG] 署名検証エラー: {e}')
            return 'Signature verification error', 400
    try:
        events = json.loads(body).get('events', [])
        print(f'[DEBUG] イベント数: {len(events)}')
        for event in events:
            print(f'[DEBUG] イベント処理開始: {event.get("type")}')
            print(f'[DEBUG] イベント詳細: {json.dumps(event, ensure_ascii=False, indent=2)}')
            # 友達追加イベントの処理
            if event.get('type') == 'follow':
                user_id = event['source']['userId']
                print(f'[DEBUG] 友達追加イベント: user_id={user_id}')
                
                # 既に案内文が送信されているかチェック
                if get_user_state(user_id) == 'welcome_sent':
                    print(f'[DEBUG] 既に案内文送信済み、スキップ: user_id={user_id}')
                    continue
                
                # 企業ID中心統合システムで企業情報を検索
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('SELECT id, company_name FROM companies WHERE line_user_id = %s', (user_id,))
                existing_company = c.fetchone()
                print(f'[DEBUG] 友達追加時の企業検索結果: {existing_company}')
                
                if existing_company:
                    # 既に紐付け済みの場合
                    print(f'[DEBUG] 既に紐付け済み: user_id={user_id}, company_id={existing_company[0]}')
                    
                    # ボタン付きのウェルカムメッセージを送信
                    print(f'[DEBUG] 案内文送信開始: user_id={user_id}, replyToken={event["replyToken"]}')
                    try:
                        send_welcome_with_buttons(event['replyToken'])
                        print(f'[DEBUG] ウェルカムメッセージ送信完了: user_id={user_id}')
                        # ユーザー状態を設定して重複送信を防ぐ
                        set_user_state(user_id, 'welcome_sent')
                    except Exception as e:
                        print(f'[DEBUG] ウェルカムメッセージ送信エラー: {e}')
                        traceback.print_exc()
                        print(f'[DEBUG] replyToken使用済みのため代替メッセージ送信をスキップ: user_id={user_id}')
                        set_user_state(user_id, 'welcome_sent')
                else:
                    # 未紐付け企業を検索
                    c.execute('SELECT id, company_name FROM companies WHERE line_user_id IS NULL ORDER BY created_at DESC LIMIT 1')
                    unlinked_company = c.fetchone()
                    print(f'[DEBUG] 友達追加時の未紐付け企業検索結果: {unlinked_company}')
                    
                    if unlinked_company:
                        # 新しい紐付けを作成
                        c.execute('UPDATE companies SET line_user_id = %s WHERE id = %s', (user_id, unlinked_company[0]))
                        conn.commit()
                        print(f'[DEBUG] 企業紐付け完了: user_id={user_id}, company_id={unlinked_company[0]}')
                        
                        # ボタン付きのウェルカムメッセージを送信
                        print(f'[DEBUG] 案内文送信開始: user_id={user_id}, replyToken={event["replyToken"]}')
                        try:
                            send_welcome_with_buttons(event['replyToken'])
                            print(f'[DEBUG] ウェルカムメッセージ送信完了: user_id={user_id}')
                            # ユーザー状態を設定して重複送信を防ぐ
                            set_user_state(user_id, 'welcome_sent')
                        except Exception as e:
                            print(f'[DEBUG] ウェルカムメッセージ送信エラー: {e}')
                            traceback.print_exc()
                            print(f'[DEBUG] replyToken使用済みのため代替メッセージ送信をスキップ: user_id={user_id}')
                            set_user_state(user_id, 'welcome_sent')
                    else:
                        # 未登録企業の場合
                        print(f'[DEBUG] 未登録企業: user_id={user_id}')
                        send_line_message(event['replyToken'], [{"type": "text", "text": get_not_registered_message()}])
                
                conn.close()
                continue
            
            # 友達削除イベントの処理
            elif event.get('type') == 'unfollow':
                user_id = event['source']['userId']
                print(f'[DEBUG] 友達削除イベント: user_id={user_id}')
                
                # line_user_idをクリア（ブロックされた場合の対応）
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('UPDATE companies SET line_user_id = NULL WHERE line_user_id = %s', (user_id,))
                conn.commit()
                conn.close()
                
                # ユーザー状態もクリア
                clear_user_state(user_id)
                print(f'[DEBUG] 企業紐付け解除: user_id={user_id}')
                continue
            
            # テキストメッセージの処理
            if event.get('type') == 'message' and event['message'].get('type') == 'text':
                user_id = event['source']['userId']
                text = event['message']['text']
                print(f'[DEBUG] テキストメッセージ受信: user_id={user_id}, text={text}')
                print(f'[DEBUG] イベント全体: {json.dumps(event, ensure_ascii=False, indent=2)}')
                
                print(f'[DEBUG] データベース接続開始')
                conn = get_db_connection()
                print(f'[DEBUG] データベース接続成功')
                c = conn.cursor()
                print(f'[DEBUG] カーソル作成成功')
                
                # 1. まずcompaniesテーブルでLINEユーザーIDを検索（決済済みユーザー）
                print(f'[DEBUG] companiesテーブル検索開始: line_user_id={user_id}')
                c.execute('SELECT id, company_name FROM companies WHERE line_user_id = %s', (user_id,))
                print(f'[DEBUG] SQLクエリ実行完了')
                company = c.fetchone()
                print(f'[DEBUG] companiesテーブル検索結果: {company}')
                
                if company:
                    # 決済済みユーザーとして認識
                    company_id = company[0]
                    company_name = company[1]
                    
                    # stripe_subscription_idはcompany_subscriptionsテーブルから取得
                    c.execute('SELECT stripe_subscription_id FROM company_subscriptions WHERE company_id = %s AND subscription_status = "active" LIMIT 1', (company_id,))
                    subscription = c.fetchone()
                    stripe_subscription_id = subscription[0] if subscription else None
                    
                    print(f'[DEBUG] 決済済みユーザーとして認識: user_id={user_id}, company_id={company_id}')
                    
                    # 決済状況をチェック
                    print(f'[DEBUG] 決済済みユーザーの決済チェック開始: user_id={user_id}')
                    payment_check = is_paid_user_company_centric(user_id)
                    print(f'[DEBUG] 決済済みユーザーの決済チェック結果: user_id={user_id}, is_paid={payment_check["is_paid"]}, status={payment_check["subscription_status"]}')
                    
                    if payment_check['is_paid']:
                        print(f'[DEBUG] 決済済み確認: user_id={user_id}')
                        # 既に案内文が送信されているかチェック
                        if get_user_state(user_id) == 'welcome_sent':
                            print(f'[DEBUG] 既に案内文送信済み、スキップ: user_id={user_id}')
                            conn.close()
                            continue
                        
                        # 案内メッセージを送信
                        try:
                            send_welcome_with_buttons(event['replyToken'])
                            print(f'[DEBUG] 決済済みユーザーの案内文送信完了: user_id={user_id}')
                            # ユーザー状態を設定
                            set_user_state(user_id, 'welcome_sent')
                        except Exception as e:
                            print(f'[DEBUG] 決済済みユーザーの案内文送信エラー: {e}')
                            traceback.print_exc()
                            send_line_message(event['replyToken'], [{"type": "text", "text": "ようこそ！AIコレクションズへ\n\n「追加」と入力してコンテンツを追加してください。"}])
                            set_user_state(user_id, 'welcome_sent')
                    else:
                        print(f'[DEBUG] 未決済確認: user_id={user_id}, status={payment_check["subscription_status"]}')
                        # 制限メッセージを送信
                        restricted_message = get_restricted_message()
                        send_line_message(event['replyToken'], [restricted_message])
                        conn.close()
                        continue
                else:
                    # 2. companiesテーブルで見つからない場合、メールアドレス連携を促す
                    print(f'[DEBUG] 既存企業が見つからないため、メールアドレス連携を促す')
                    # メールアドレス連携を促すメッセージを送信
                    send_line_message(event['replyToken'], [{"type": "text", "text": "決済済みの方は、登録時のメールアドレスを送信してください。\n\n例: example@example.com\n\n※メールアドレスを送信すると、自動的に企業データと紐付けされます。"}])
                    conn.close()
                    continue
                    print(f'[DEBUG] ユーザー状態確認: user_id={user_id}, state={state}')
                    print(f'[DEBUG] 状態詳細: state={state}, text={text}')
                    
                    # 初回案内文が既に送信されている場合は、通常のメッセージ処理に進む
                    if state == 'welcome_sent':
                        print(f'[DEBUG] 初回案内文送信済み、通常メッセージ処理に進む: user_id={user_id}')
                        # 通常のメッセージ処理に進む
                    else:
                        print(f'[DEBUG] ユーザーは特定の状態: user_id={user_id}, state={state}')
                    
                    # 状態に基づく処理（優先順位順）
                    print(f'[DEBUG] 状態チェック: state={state}, text={text}')
                    print(f'[DEBUG] メッセージ処理分岐開始: text="{text}", state="{state}"')
                    if state == 'add_select':
                        print(f'[DEBUG] add_select状態での処理: user_id={user_id}, text={text}')
                        if text in ['1', '2', '3', '4']:
                            print(f'[DEBUG] コンテンツ選択: text={text}')
                            set_user_state(user_id, f'confirm_{text}')
                            handle_content_selection(event['replyToken'], company_id, stripe_subscription_id, text)
                        elif text == 'メニュー':
                            set_user_state(user_id, 'welcome_sent')
                            send_line_message(event['replyToken'], [get_menu_message()])
                        elif text == 'ヘルプ':
                            send_line_message(event['replyToken'], get_help_message_company())
                        elif text == '状態':
                            handle_status_check_company(event['replyToken'], company_id)
                        else:
                            send_line_message(event['replyToken'], [{"type": "text", "text": "1〜3の数字でコンテンツを選択してください。\n\nまたは「メニュー」でメインメニューに戻ります。"}])
                        continue
                    # 削除関連のコマンドを優先処理
                    elif text == '削除':
                        print(f'[DEBUG] 削除コマンド受信: user_id={user_id}')
                        handle_cancel_menu_company(event['replyToken'], company_id, stripe_subscription_id)
                    elif text == 'サブスクリプション解約':
                        handle_subscription_cancel(event['replyToken'], company_id, stripe_subscription_id)
                    elif text == 'コンテンツ解約':
                        set_user_state(user_id, 'cancel_select')
                        handle_cancel_request(event['replyToken'], company_id, stripe_subscription_id)
                    elif state == 'cancel_select':
                        print(f'[DEBUG] 削除選択処理: user_id={user_id}, state={state}, text={text}')
                        
                        # 削除対象のコンテンツを選択
                        if text in ['1', '2', '3']:
                            print(f'[DEBUG] 削除対象コンテンツ選択: text={text}')
                            # 削除確認状態に設定
                            set_user_state(user_id, f'cancel_confirm_{text}')
                            # 削除確認メッセージを送信
                            handle_cancel_selection(event['replyToken'], company_id, stripe_subscription_id, text)
                            continue
                        # 「メニュー」コマンドの場合は状態をリセットしてメニューを表示
                        elif text == 'メニュー':
                            set_user_state(user_id, 'welcome_sent')
                            send_line_message(event['replyToken'], [get_menu_message()])
                            continue
                        # 主要なコマンドの場合は通常の処理に切り替え
                        elif text == '追加':
                            set_user_state(user_id, 'add_select')
                            handle_add_content_company(event['replyToken'], company_id, stripe_subscription_id)
                            continue
                        elif text == '状態':
                            handle_status_check_company(event['replyToken'], company_id)
                            continue
                        elif text == 'ヘルプ':
                            send_line_message(event['replyToken'], get_help_message_company())
                            continue
                        else:
                            # AI技術を活用した高度な数字抽出関数を使用して処理
                            from services.line_service import smart_number_extraction, validate_selection_numbers
                            
                            # データベースからコンテンツ数を取得
                            conn = get_db_connection()
                            c = conn.cursor()
                            # データベースタイプに応じてプレースホルダーを選択
                            from utils.db import get_db_type
                            db_type = get_db_type()
                            placeholder = '%s' if db_type == 'postgresql' else '?'
                            
                            c.execute(f'SELECT COUNT(*) FROM company_subscriptions WHERE company_id = {placeholder} AND subscription_status = "active"', (company_id,))
                            content_count = c.fetchone()[0]
                            conn.close()
                            
                            numbers = smart_number_extraction(text)
                            valid_numbers, invalid_reasons, duplicates = validate_selection_numbers(numbers, content_count)
                            
                            if valid_numbers:  # 有効な数字が抽出できた場合のみ処理
                                handle_cancel_selection(event['replyToken'], company_id, stripe_subscription_id, text)
                                set_user_state(user_id, 'welcome_sent')
                            else:
                                # 数字が抽出できない場合は詳細なエラーメッセージ
                                error_message = "数字を入力してください。\n\n対応形式:\n• 1,2,3 (カンマ区切り)\n• 1.2.3 (ドット区切り)\n• 1 2 3 (スペース区切り)\n• 一二三 (日本語数字)\n• 1番目,2番目 (序数表現)\n• 最初,二番目 (日本語序数)"
                                send_line_message(event['replyToken'], [{"type": "text", "text": error_message}])

                    # その他のコマンド処理（add_select状態以外）
                    elif text == '追加' and state != 'cancel_select':
                        print(f'[DEBUG] 追加コマンド受信: user_id={user_id}, state={state}')
                        set_user_state(user_id, 'add_select')
                        print(f'[DEBUG] ユーザー状態をadd_selectに設定: user_id={user_id}')
                        print(f'[DEBUG] handle_add_content_company呼び出し開始: replyToken={event["replyToken"]}, company_id={company_id}, stripe_subscription_id={stripe_subscription_id}')
                        handle_add_content_company(event['replyToken'], company_id, stripe_subscription_id)
                        print(f'[DEBUG] handle_add_content_company呼び出し完了')
                    elif text == 'メニュー' and state != 'cancel_select':
                        print(f'[DEBUG] メニューコマンド受信: user_id={user_id}, state={state}')
                        send_line_message(event['replyToken'], [get_menu_message()])
                    elif text == 'ヘルプ' and state != 'cancel_select':
                        print(f'[DEBUG] ヘルプコマンド受信: user_id={user_id}, state={state}')
                        send_line_message(event['replyToken'], get_help_message_company())
                    elif text == '状態' and state != 'cancel_select':
                        print(f'[DEBUG] 状態コマンド受信: user_id={user_id}, state={state}')
                        handle_status_check_company(event['replyToken'], company_id)
                    elif state and state.startswith('confirm_'):
                        # 確認状態での処理
                        if text.lower() in ['はい', 'yes', 'y']:
                            # 確認状態からコンテンツ番号を取得
                            content_number = state.split('_')[1]
                            
                            # コンテンツ情報を取得
                            content_info = {
                                '1': {
                                    'name': 'AI予定秘書',
                                    'price': 1500,
                                    "description": '日程調整のストレスから解放される、スケジュール管理の相棒',
                                    'usage': 'Googleカレンダーと連携し、LINEで予定の追加・確認・空き時間の提案まで。調整のやりとりに追われる時間を、もっとクリエイティブに使えるように。',
                                    'url': 'https://lp-production-9e2c.up.railway.app/schedule',
                                    'line_url': 'https://line.me/R/ti/p/@ai_schedule_secretary'
                                },
                                '2': {
                                    'name': 'AI経理秘書',
                                    'price': 1500,
                                    "description": '打合せ後すぐ送れる、スマートな請求書作成アシスタント',
                                    'usage': 'LINEで項目を送るだけで、見積書や請求書を即作成。営業から事務処理までを一気通貫でスムーズに。',
                                    'url': 'https://lp-production-9e2c.up.railway.app/accounting',
                                    'line_url': 'https://line.me/R/ti/p/@ai_accounting_secretary'
                                },
                                '3': {
                                    'name': 'AIタスクコンシェルジュ',
                                    'price': 1500,
                                    "description": '今日やるべきことを、ベストなタイミングで',
                                    'usage': '登録したタスクを空き時間に自動で配置し、理想的な1日をAIが提案。「やりたいのにできない」を、「自然にこなせる」毎日に。',
                                    'url': 'https://lp-production-9e2c.up.railway.app/task',
                                    'line_url': 'https://line.me/R/ti/p/@ai_task_concierge'
                                }
                            }
                            
                            if content_number in content_info:
                                content = content_info[content_number]
                                # 企業ユーザー専用：コンテンツを追加
                                result = handle_content_confirmation_company(company_id, content['name'])
                                if result['success']:
                                    # 企業登録フォームへのリンクを含むメッセージ
                                    registration_url = result.get('registration_url', '')
                                    
                                    if registration_url:
                                        # 企業登録フォームへのリンク付きメッセージ
                                        success_message = f"�� {content['name']}を追加しました！\n\n✨ {content['description']}\n\n🔗 アクセスURL：\n{content['url']}\n\n💡 使い方：\n{content['usage']}\n\n🏢 企業向けLINE公式アカウント設定：\n{registration_url}\n\n📱 何かお手伝いできることはありますか？\n• 「追加」：他のコンテンツを追加\n• 「状態」：利用状況を確認\n• 「メニュー」：メインメニューに戻る\n• 「ヘルプ」：使い方を確認"
                                    else:
                                        # 従来のメッセージ（フォールバック）
                                        success_message = f"🎉 {content['name']}を追加しました！\n\n✨ {content['description']}\n\n🔗 アクセスURL：\n{content['url']}\n\n💡 使い方：\n{content['usage']}\n\n📱 何かお手伝いできることはありますか？\n• 「追加」：他のコンテンツを追加\n• 「状態」：利用状況を確認\n• 「メニュー」：メインメニューに戻る\n• 「ヘルプ」：使い方を確認"
                                    
                                    send_line_message(event['replyToken'], [{"type": "text", "text": success_message}])
                                else:
                                    error_message = f"❌ コンテンツの追加に失敗しました: {result.get('error', '不明なエラー')}\n\n📱 「メニュー」と入力すると、メインメニューに戻れます。"
                                    send_line_message(event['replyToken'], [{"type": "text", "text": error_message}])
                            else:
                                send_line_message(event['replyToken'], [{"type": "text", "text": "無効なコンテンツ番号です。\n\n📱 「メニュー」と入力すると、メインメニューに戻れます。"}])
                                
                                set_user_state(user_id, 'welcome_sent')
                        elif text.lower() in ['いいえ', 'no', 'n']:
                            # キャンセル処理
                            send_line_message(event['replyToken'], [{"type": "text", "text": "コンテンツの追加をキャンセルしました。\n\n📱 何かお手伝いできることはありますか？\n• 「追加」：他のコンテンツを追加\n• 「状態」：利用状況を確認\n• 「メニュー」：メインメニューに戻る\n• 「ヘルプ」：使い方を確認"}])
                            set_user_state(user_id, 'welcome_sent')
                        elif text == 'メニュー':
                            set_user_state(user_id, 'welcome_sent')
                            send_line_message(event['replyToken'], [get_menu_message()])
                        else:
                            # 無効な入力の場合は確認を促す
                            send_line_message(event['replyToken'], [{"type": "text", "text": "「はい」または「いいえ」で回答してください。\n\n📱 または「メニュー」でメインメニューに戻ります。"}])
                    elif state and state.startswith('cancel_confirm_'):
                        # 解約確認状態での処理
                        if text.lower() in ['はい', 'yes', 'y']:
                            # 解約確認状態からコンテンツ番号を取得
                            content_number = state.split('_')[2]  # cancel_confirm_1 → 1
                            
                            # 解約処理を実行
                            from services.line_service import handle_cancel_confirmation
                            result = handle_cancel_confirmation(company_id, content_number)
                            
                            if result['success']:
                                success_message = f"✅ コンテンツの解約が完了しました。\n\n📱 何かお手伝いできることはありますか？\n• 「追加」：他のコンテンツを追加\n• 「状態」：利用状況を確認\n• 「メニュー」：メインメニューに戻る\n• 「ヘルプ」：使い方を確認"
                                send_line_message(event['replyToken'], [{"type": "text", "text": success_message}])
                            else:
                                error_message = f"❌ 解約処理に失敗しました: {result.get('error', '不明なエラー')}\n\n📱 「メニュー」と入力すると、メインメニューに戻れます。"
                                send_line_message(event['replyToken'], [{"type": "text", "text": error_message}])
                                
                                set_user_state(user_id, 'welcome_sent')
                        elif text.lower() in ['いいえ', 'no', 'n']:
                            # キャンセル処理
                            send_line_message(event['replyToken'], [{"type": "text", "text": "解約をキャンセルしました。\n\n📱 何かお手伝いできることはありますか？\n• 「追加」：他のコンテンツを追加\n• 「状態」：利用状況を確認\n• 「メニュー」：メインメニューに戻る\n• 「ヘルプ」：使い方を確認"}])
                            set_user_state(user_id, 'welcome_sent')
                        elif text == 'メニュー':
                            set_user_state(user_id, 'welcome_sent')
                            send_line_message(event['replyToken'], [get_menu_message()])
                        else:
                            # 無効な入力の場合は確認を促す
                            send_line_message(event['replyToken'], [{"type": "text", "text": "「はい」または「いいえ」で回答してください。\n\n📱 または「メニュー」でメインメニューに戻ります。"}])
                    elif '@' in text and '.' in text and len(text) < 100:
                        print(f'[DEBUG] メールアドレス連携処理開始: user_id={user_id}, text={text}')
                        
                        def normalize_email(email):
                            email = email.strip().lower()
                            email = unicodedata.normalize('NFKC', email)
                            return email
                        
                        normalized_email = normalize_email(text)
                        print(f'[DEBUG] 正規化後のメールアドレス: {normalized_email}')
                        
                        # データベース接続を取得
                        conn = get_db_connection()
                        c = conn.cursor()
                        
                        # 1. companiesテーブルでメールアドレスを検索
                        c.execute('SELECT id, company_name FROM companies WHERE email = %s', (normalized_email,))
                        company = c.fetchone()
                        print(f'[DEBUG] companiesテーブル検索結果: {company}')
                        
                        if company:
                            company_id, company_name = company
                            print(f'[DEBUG] 企業データ発見: company_id={company_id}, company_name={company_name}')
                            
                            # stripe_subscription_idはcompany_subscriptionsテーブルから取得
                            c.execute('SELECT stripe_subscription_id FROM company_subscriptions WHERE company_id = %s AND subscription_status = "active" LIMIT 1', (company_id,))
                            subscription = c.fetchone()
                            stripe_subscription_id = subscription[0] if subscription else None
                            
                            # 企業データにLINEユーザーIDを紐付け
                            c.execute('UPDATE companies SET line_user_id = %s WHERE id = %s', (user_id, company_id))
                            conn.commit()
                            print(f'[DEBUG] 企業データ紐付け完了: user_id={user_id}, company_id={company_id}')
                            
                            # 決済状況をチェック
                            print(f'[DEBUG] 企業紐付け後の決済チェック開始: user_id={user_id}')
                            payment_check = is_paid_user_company_centric(user_id)
                            print(f'[DEBUG] 企業紐付け後の決済チェック結果: user_id={user_id}, is_paid={payment_check["is_paid"]}, status={payment_check["subscription_status"]}')
                            
                            if payment_check['is_paid']:
                                print(f'[DEBUG] 決済済み確認: user_id={user_id}')
                                # 案内メッセージを送信
                                try:
                                    send_welcome_with_buttons(event['replyToken'])
                                    print(f'[DEBUG] メールアドレス連携時の案内文送信完了: user_id={user_id}')
                                    # ユーザー状態を設定
                                    set_user_state(user_id, 'welcome_sent')
                                except Exception as e:
                                    print(f'[DEBUG] メールアドレス連携時の案内文送信エラー: {e}')
                                    traceback.print_exc()
                                    send_line_message(event['replyToken'], [{"type": "text", "text": "ようこそ！AIコレクションズへ\n\n「追加」と入力してコンテンツを追加してください。"}])
                                    set_user_state(user_id, 'welcome_sent')
                            else:
                                print(f'[DEBUG] 未決済確認: user_id={user_id}, status={payment_check["subscription_status"]}')
                                # 制限メッセージを送信
                                restricted_message = get_restricted_message()
                                send_line_message(event['replyToken'], [restricted_message])
                        else:
                            # 企業データが見つからない場合
                            print(f'[DEBUG] 企業データが見つかりません: email={normalized_email}')
                            send_line_message(event['replyToken'], [{"type": "text", "text": 'ご登録メールアドレスが見つかりません。LPでご登録済みかご確認ください。'}])
                        
                        # データベース接続を閉じる
                        conn.close()
                        continue
            else:
                print(f'[DEBUG] デフォルト処理: user_id={user_id}, state={state}, text={text}')
                print(f'[DEBUG] どの条件にも当てはまらないためデフォルト処理に進む: text="{text}", state="{state}"')
                
                # メールアドレス連携を促すメッセージを送信
                if not state or state == 'welcome_sent':
                    print(f'[DEBUG] メールアドレス連携を促すメッセージを送信: user_id={user_id}')
                    send_line_message(event['replyToken'], [{"type": "text", "text": "決済済みの方は、登録時のメールアドレスを送信してください。\n\n例: example@example.com\n\n※メールアドレスを送信すると、自動的に企業データと紐付けされます。"}])
                else:
                    # 特定の状態ではデフォルトメッセージを送信
                    print(f'[DEBUG] 特定状態でのデフォルト処理: state={state}')
                    send_line_message(event['replyToken'], [{"type": "text", "text": "無効な入力です。メニューから選択してください。"}])
            conn.close()
        
        # リッチメニューのpostbackイベントの処理
        if event.get('type') == 'postback':
            user_id = event['source']['userId']
            postback_data = event['postback']['data']
            conn = get_db_connection()
            c = conn.cursor()
            
            # 企業ユーザー専用：companiesテーブルから企業情報を取得
            c.execute('SELECT id, company_name FROM companies WHERE line_user_id = %s', (user_id,))
            company = c.fetchone()
            
            if not company:
                send_line_message(event['replyToken'], [{"type": "text", "text": "企業登録が完了していません。LPで企業登録を行ってください。"}])
                conn.close()
                return jsonify({'status': 'ok'})
                
            company_id, company_name = company
            
            # stripe_subscription_idはcompany_subscriptionsテーブルから取得
            c.execute('SELECT stripe_subscription_id FROM company_subscriptions WHERE company_id = %s AND subscription_status = "active" LIMIT 1', (company_id,))
            subscription = c.fetchone()
            stripe_subscription_id = subscription[0] if subscription else None
            
            # postbackデータに基づいて処理
            if postback_data == 'action=add_content':
                set_user_state(user_id, 'add_select')
                # 企業ユーザー専用：company_idを使用
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
            conn.close()
    except Exception as e:
        traceback.print_exc()
    return jsonify({'status': 'ok'}) 