from flask import Blueprint, request, jsonify
import os, json, hmac, hashlib, base64
from services.line_service import send_line_message
from services.line_service import (
    handle_add_content, handle_content_selection,
    handle_content_confirmation, handle_status_check, handle_cancel_request,
    handle_cancel_selection, handle_subscription_cancel, handle_cancel_menu,
    get_welcome_message, get_not_registered_message
)
from utils.message_templates import get_menu_message, get_help_message, get_default_message
from utils.db import get_db_connection
import datetime

line_bp = Blueprint('line', __name__)

user_states = {}
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
                from services.line_service import send_welcome_with_buttons_push
                success = send_welcome_with_buttons_push(line_user_id)
                if success:
                    # 自動案内文送信後にユーザー状態を設定（重複防止）
                    user_states[line_user_id] = 'welcome_sent'
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
                import requests
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
                import stripe
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
        import requests
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
            'user_states': user_states
        })
    except Exception as e:
        return jsonify({'error': str(e)})

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
            # 友達追加イベントの処理
            if event.get('type') == 'follow':
                user_id = event['source']['userId']
                print(f'[DEBUG] 友達追加イベント: user_id={user_id}')
                
                # 既に案内文が送信されているかチェック
                if user_states.get(user_id) == 'welcome_sent':
                    print(f'[DEBUG] 既に案内文送信済み、スキップ: user_id={user_id}')
                    continue
                
                # 直近のline_user_id未設定ユーザーを自動で紐付け
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('SELECT id, stripe_subscription_id FROM users WHERE line_user_id IS NULL ORDER BY created_at DESC LIMIT 1')
                user = c.fetchone()
                print(f'[DEBUG] 友達追加時の未紐付けユーザー検索結果: {user}')
                
                if user:
                    # 既存のLINEユーザーID紐付けを解除（重複回避）
                    c.execute('UPDATE users SET line_user_id = NULL WHERE line_user_id = %s', (user_id,))
                    
                    # 新しい紐付けを作成
                    c.execute('UPDATE users SET line_user_id = %s WHERE id = %s', (user_id, user[0]))
                    conn.commit()
                    print(f'[DEBUG] ユーザー紐付け完了: user_id={user_id}, db_user_id={user[0]}')
                    
                    # ボタン付きのウェルカムメッセージを送信（必ず送信）
                    print(f'[DEBUG] 案内文送信開始: user_id={user_id}, replyToken={event["replyToken"]}')
                    try:
                        from services.line_service import send_welcome_with_buttons
                        send_welcome_with_buttons(event['replyToken'])
                        print(f'[DEBUG] ウェルカムメッセージ送信完了: user_id={user_id}')
                        # ユーザー状態を設定して重複送信を防ぐ
                        user_states[user_id] = 'welcome_sent'
                    except Exception as e:
                        print(f'[DEBUG] ウェルカムメッセージ送信エラー: {e}')
                        import traceback
                        traceback.print_exc()
                        # エラーが発生した場合は簡単なテキストメッセージを送信
                        print(f'[DEBUG] 代替メッセージ送信開始: user_id={user_id}')
                        send_line_message(event['replyToken'], [{"type": "text", "text": "ようこそ！AIコレクションズへ\n\n「追加」と入力してコンテンツを追加してください。"}])
                        user_states[user_id] = 'welcome_sent'
                        print(f'[DEBUG] 代替メッセージ送信完了: user_id={user_id}')
                else:
                    # 未登録ユーザーの場合
                    print(f'[DEBUG] 未登録ユーザー: user_id={user_id}')
                    from utils.message_templates import get_not_registered_message
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
                c.execute('UPDATE users SET line_user_id = NULL WHERE line_user_id = %s', (user_id,))
                conn.commit()
                conn.close()
                
                # ユーザー状態もクリア
                if user_id in user_states:
                    del user_states[user_id]
                print(f'[DEBUG] ユーザー紐付け解除: user_id={user_id}')
                continue
            
            # テキストメッセージの処理
            if event.get('type') == 'message' and event['message'].get('type') == 'text':
                user_id = event['source']['userId']
                text = event['message']['text']
                print(f'[DEBUG] テキストメッセージ受信: user_id={user_id}, text={text}')
                
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('SELECT id, stripe_subscription_id, line_user_id FROM users WHERE line_user_id = %s', (user_id,))
                user = c.fetchone()
                print(f'[DEBUG] 既存ユーザー検索結果: {user}')
                
                if not user:
                    print(f'[DEBUG] 既存ユーザーが見つからないため、未紐付けユーザーを検索')
                    c.execute('SELECT id, stripe_subscription_id FROM users WHERE line_user_id IS NULL ORDER BY created_at DESC LIMIT 1')
                    user = c.fetchone()
                    print(f'[DEBUG] 未紐付けユーザー検索結果: {user}')
                    
                    if user:
                        print(f'[DEBUG] 未紐付けユーザー発見、紐付け処理開始: user_id={user_id}, db_user_id={user[0]}')
                        
                        # 既に案内文が送信されているかチェック
                        if user_states.get(user_id) == 'welcome_sent':
                            print(f'[DEBUG] 既に案内文送信済み、スキップ: user_id={user_id}')
                            conn.close()
                            continue
                        
                        # 既存のLINEユーザーID紐付けを解除（重複回避）
                        c.execute('UPDATE users SET line_user_id = NULL WHERE line_user_id = %s', (user_id,))
                        
                        # 新しい紐付けを作成
                        c.execute('UPDATE users SET line_user_id = %s WHERE id = %s', (user_id, user[0]))
                        conn.commit()
                        print(f'[DEBUG] 初回メッセージ時のユーザー紐付け完了: user_id={user_id}, db_user_id={user[0]}')
                        
                        # 決済画面からLINEに移動した時の初回案内文（必ず送信）
                        print(f'[DEBUG] 案内文送信開始: user_id={user_id}, replyToken={event["replyToken"]}')
                        try:
                            from services.line_service import send_welcome_with_buttons
                            send_welcome_with_buttons(event['replyToken'])
                            print(f'[DEBUG] 初回メッセージ時の案内文送信完了: user_id={user_id}')
                            # ユーザー状態を設定して重複送信を防ぐ
                            user_states[user_id] = 'welcome_sent'
                        except Exception as e:
                            print(f'[DEBUG] 初回メッセージ時の案内文送信エラー: {e}')
                            import traceback
                            traceback.print_exc()
                            # エラーが発生した場合は簡単なテキストメッセージを送信
                            send_line_message(event['replyToken'], [{"type": "text", "text": "ようこそ！AIコレクションズへ\n\n「追加」と入力してコンテンツを追加してください。"}])
                            user_states[user_id] = 'welcome_sent'
                    else:
                        print(f'[DEBUG] 未紐付けユーザーも見つからない')
                        send_line_message(event['replyToken'], [{"type": "text", "text": get_not_registered_message()}])
                    conn.close()
                    continue
                else:
                    user_id_db = user[0]
                    stripe_subscription_id = user[1]
                    
                    # 既に案内文が送信されているかチェック
                    if user_states.get(user_id) == 'welcome_sent':
                        print(f'[DEBUG] 既に案内文送信済み、通常メッセージ処理に進む: user_id={user_id}')
                        # 通常のメッセージ処理に進む
                    else:
                        # 初回案内文が未送信の場合のみ送信
                        print(f'[DEBUG] 初回案内文未送信、案内文送信: user_id={user_id}')
                        try:
                            from services.line_service import send_welcome_with_buttons
                            send_welcome_with_buttons(event['replyToken'])
                            print(f'[DEBUG] 初回案内文送信完了: user_id={user_id}')
                            user_states[user_id] = 'welcome_sent'
                            conn.close()
                            continue
                        except Exception as e:
                            print(f'[DEBUG] 初回案内文送信エラー: {e}')
                            # エラーが発生した場合は通常のメッセージ処理に進む
                            user_states[user_id] = 'welcome_sent'
                
                # ユーザー状態の確認
                state = user_states.get(user_id, 'welcome_sent')
                print(f'[DEBUG] ユーザー状態確認: user_id={user_id}, state={state}, user_states={user_states}')
                
                # 初回案内文が既に送信されている場合は、通常のメッセージ処理に進む
                if state == 'welcome_sent':
                    print(f'[DEBUG] 初回案内文送信済み、通常メッセージ処理に進む: user_id={user_id}')
                    # 通常のメッセージ処理に進む
                else:
                    print(f'[DEBUG] ユーザーは特定の状態: user_id={user_id}, state={state}')
                
                # 解約関連のコマンドを優先処理
                if text == '解約':
                    print(f'[DEBUG] 解約コマンド受信: user_id={user_id}')
                    handle_cancel_menu(event['replyToken'], user_id_db, stripe_subscription_id)
                elif text == 'サブスクリプション解約':
                    handle_subscription_cancel(event['replyToken'], user_id_db, stripe_subscription_id)
                elif text == 'コンテンツ解約':
                    user_states[user_id] = 'cancel_select'
                    handle_cancel_request(event['replyToken'], user_id_db, stripe_subscription_id)
                elif state == 'cancel_select':
                    print(f'[DEBUG] 解約選択処理: user_id={user_id}, state={state}, text={text}')
                    
                    # 「メニュー」コマンドの場合は状態をリセットしてメニューを表示
                    if text == 'メニュー':
                        user_states[user_id] = 'welcome_sent'
                        send_line_message(event['replyToken'], [get_menu_message()])
                        continue
                    
                    # 主要なコマンドの場合は通常の処理に切り替え
                    if text == '追加':
                        user_states[user_id] = 'add_select'
                        handle_add_content(event['replyToken'], user_id_db, stripe_subscription_id)
                        continue
                    elif text == '状態':
                        handle_status_check(event['replyToken'], user_id_db)
                        continue
                    elif text == 'ヘルプ':
                        send_line_message(event['replyToken'], get_help_message())
                        continue
                    
                    # AI技術を活用した高度な数字抽出関数を使用して処理
                    from services.line_service import smart_number_extraction, validate_selection_numbers
                    
                    # データベースからコンテンツ数を取得
                    conn = get_db_connection()
                    c = conn.cursor()
                    # データベースタイプに応じてプレースホルダーを選択
                    from utils.db import get_db_type
                    db_type = get_db_type()
                    placeholder = '%s' if db_type == 'postgresql' else '?'
                    
                    c.execute(f'SELECT COUNT(*) FROM usage_logs WHERE user_id = {placeholder} AND content_type IN ({placeholder}, {placeholder}, {placeholder})', 
                             (user_id_db, 'AI予定秘書', 'AI経理秘書', 'AIタスクコンシェルジュ'))
                    content_count = c.fetchone()[0]
                    conn.close()
                    
                    numbers = smart_number_extraction(text)
                    valid_numbers, invalid_reasons, duplicates = validate_selection_numbers(numbers, content_count)
                    
                    if valid_numbers:  # 有効な数字が抽出できた場合のみ処理
                        handle_cancel_selection(event['replyToken'], user_id_db, stripe_subscription_id, text)
                        user_states[user_id] = 'welcome_sent'
                    else:
                        # 数字が抽出できない場合は詳細なエラーメッセージ
                        error_message = "数字を入力してください。\n\n対応形式:\n• 1,2,3 (カンマ区切り)\n• 1.2.3 (ドット区切り)\n• 1 2 3 (スペース区切り)\n• 一二三 (日本語数字)\n• 1番目,2番目 (序数表現)\n• 最初,二番目 (日本語序数)"
                        send_line_message(event['replyToken'], [{"type": "text", "text": error_message}])
                # add_select状態の処理を優先
                elif state == 'add_select':
                    print(f'[DEBUG] add_select状態での処理: user_id={user_id}, text={text}, user_states={user_states}')
                    # 主要なコマンドの場合は通常の処理に切り替え
                    if text in ['1', '2', '3', '4']:
                        print(f'[DEBUG] コンテンツ選択: text={text}')
                        # 選択したコンテンツ番号を保存
                        user_states[user_id] = f'confirm_{text}'
                        handle_content_selection(event['replyToken'], user_id_db, stripe_subscription_id, text)
                    elif text == 'メニュー':
                        print(f'[DEBUG] メニューコマンド: text={text}')
                        user_states[user_id] = 'welcome_sent'
                        send_line_message(event['replyToken'], [get_menu_message()])
                    elif text == 'ヘルプ':
                        print(f'[DEBUG] ヘルプコマンド: text={text}')
                        send_line_message(event['replyToken'], get_help_message())
                    elif text == '状態':
                        print(f'[DEBUG] 状態コマンド: text={text}')
                        handle_status_check(event['replyToken'], user_id_db)
                    else:
                        print(f'[DEBUG] 無効な入力: text={text}')
                        # 無効な入力の場合はコンテンツ選択を促す
                        send_line_message(event['replyToken'], [{"type": "text", "text": "1〜3の数字でコンテンツを選択してください。\n\nまたは「メニュー」でメインメニューに戻ります。"}])
                # その他のコマンド処理（add_select状態以外）
                elif text == '追加' and state != 'cancel_select':
                    print(f'[DEBUG] 追加コマンド受信: user_id={user_id}, state={state}')
                    user_states[user_id] = 'add_select'
                    print(f'[DEBUG] ユーザー状態をadd_selectに設定: user_id={user_id}, user_states={user_states}')
                    handle_add_content(event['replyToken'], user_id_db, stripe_subscription_id)
                elif text == 'メニュー' and state != 'cancel_select':
                    print(f'[DEBUG] メニューコマンド受信: user_id={user_id}, state={state}')
                    send_line_message(event['replyToken'], [get_menu_message()])
                elif text == 'ヘルプ' and state != 'cancel_select':
                    print(f'[DEBUG] ヘルプコマンド受信: user_id={user_id}, state={state}')
                    send_line_message(event['replyToken'], get_help_message())
                elif text == '状態' and state != 'cancel_select':
                    print(f'[DEBUG] 状態コマンド受信: user_id={user_id}, state={state}')
                    handle_status_check(event['replyToken'], user_id_db)
                elif state and state.startswith('confirm_'):
                    # 確認状態での処理
                    if text.lower() in ['はい', 'yes', 'y']:
                        # 確認状態からコンテンツ番号を取得
                        content_number = state.split('_')[1]
                        handle_content_confirmation(event['replyToken'], user_id_db, stripe_subscription_id, content_number, True)
                        user_states[user_id] = 'welcome_sent'
                    elif text.lower() in ['いいえ', 'no', 'n']:
                        # 確認状態からコンテンツ番号を取得
                        content_number = state.split('_')[1]
                        handle_content_confirmation(event['replyToken'], user_id_db, stripe_subscription_id, content_number, False)
                        user_states[user_id] = 'welcome_sent'
                    elif text == 'メニュー':
                        user_states[user_id] = 'welcome_sent'
                        send_line_message(event['replyToken'], [get_menu_message()])
                    else:
                        # 無効な入力の場合は確認を促す
                        send_line_message(event['replyToken'], [{"type": "text", "text": "「はい」または「いいえ」で回答してください。\n\nまたは「メニュー」でメインメニューに戻ります。"}])
                elif '@' in text and '.' in text and len(text) < 100:
                    import unicodedata
                    def normalize_email(email):
                        email = email.strip().lower()
                        email = unicodedata.normalize('NFKC', email)
                        return email
                    normalized_email = normalize_email(text)
                    c.execute('SELECT id, line_user_id FROM users WHERE email = %s', (normalized_email,))
                    user = c.fetchone()
                    if user:
                        if user[1] is None:
                            c.execute('UPDATE users SET line_user_id = %s WHERE id = %s', (user_id, user[0]))
                            conn.commit()
                            print(f'[DEBUG] メールアドレス連携完了: user_id={user_id}, db_user_id={user[0]}')
                            # 決済画面からLINEに移動した時の初回案内文
                            try:
                                from services.line_service import send_welcome_with_buttons
                                send_welcome_with_buttons(event['replyToken'])
                                print(f'[DEBUG] メールアドレス連携時の案内文送信完了: user_id={user_id}')
                            except Exception as e:
                                print(f'[DEBUG] メールアドレス連携時の案内文送信エラー: {e}')
                                import traceback
                                traceback.print_exc()
                                # エラーが発生した場合は簡単なテキストメッセージを送信
                                send_line_message(event['replyToken'], [{"type": "text", "text": "ようこそ！AIコレクションズへ\n\n「追加」と入力してコンテンツを追加してください。"}])
                        else:
                            send_line_message(event['replyToken'], [{"type": "text", "text": 'このメールアドレスは既にLINE連携済みです。'}])
                    else:
                        # 救済策: 直近のline_user_id未設定ユーザーを自動で紐付け
                        c.execute('SELECT id FROM users WHERE line_user_id IS NULL ORDER BY created_at DESC LIMIT 1')
                        fallback_user = c.fetchone()
                        if fallback_user:
                            c.execute('UPDATE users SET line_user_id = %s WHERE id = %s', (user_id, fallback_user[0]))
                            conn.commit()
                            print(f'[DEBUG] 救済策でのユーザー紐付け完了: user_id={user_id}, db_user_id={fallback_user[0]}')
                            # 決済画面からLINEに移動した時の初回案内文
                            try:
                                from services.line_service import send_welcome_with_buttons
                                send_welcome_with_buttons(event['replyToken'])
                                print(f'[DEBUG] 救済策での案内文送信完了: user_id={user_id}')
                            except Exception as e:
                                print(f'[DEBUG] 救済策での案内文送信エラー: {e}')
                                import traceback
                                traceback.print_exc()
                                # エラーが発生した場合は簡単なテキストメッセージを送信
                                send_line_message(event['replyToken'], [{"type": "text", "text": "ようこそ！AIコレクションズへ\n\n「追加」と入力してコンテンツを追加してください。"}])
                        else:
                            send_line_message(event['replyToken'], [{"type": "text", "text": 'ご登録メールアドレスが見つかりません。LPでご登録済みかご確認ください。'}])
                else:
                    print(f'[DEBUG] デフォルト処理: user_id={user_id}, state={state}, text={text}')
                    # どの条件にも当てはまらない場合のデフォルト処理
                    if state in ['cancel_select', 'add_select'] or (state and state.startswith('confirm_')):
                        # 特定の状態ではデフォルトメッセージを送信しない
                        print(f'[DEBUG] 特定状態でのデフォルト処理: state={state}')
                        send_line_message(event['replyToken'], [{"type": "text", "text": "無効な入力です。メニューから選択してください。"}])
                    else:
                        print(f'[DEBUG] 一般的なデフォルト処理: state={state}')
                        # 初回案内文が未送信の場合のみ送信
                        if user_id not in user_states or user_states[user_id] is None:
                            print(f'[DEBUG] 初回案内文送信: user_id={user_id}')
                            try:
                                from services.line_service import send_welcome_with_buttons
                                send_welcome_with_buttons(event['replyToken'])
                                user_states[user_id] = 'welcome_sent'
                            except Exception as e:
                                print(f'[DEBUG] 初回案内文送信エラー: {e}')
                                send_line_message(event['replyToken'], [get_default_message()])
                        else:
                            send_line_message(event['replyToken'], [get_default_message()])
                conn.close()
            # リッチメニューのpostbackイベントの処理
            elif event.get('type') == 'postback':
                user_id = event['source']['userId']
                postback_data = event['postback']['data']
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('SELECT id, stripe_subscription_id, line_user_id FROM users WHERE line_user_id = %s', (user_id,))
                user = c.fetchone()
                if not user:
                    send_line_message(event['replyToken'], [{"type": "text", "text": get_not_registered_message()}])
                    conn.close()
                    continue
                user_id_db = user[0]
                stripe_subscription_id = user[1]
                # postbackデータに基づいて処理
                if postback_data == 'action=add_content':
                    user_states[user_id] = 'add_select'
                    handle_add_content(event['replyToken'], user_id_db, stripe_subscription_id)
                elif postback_data == 'action=check_status':
                    handle_status_check(event['replyToken'], user_id_db)
                elif postback_data == 'action=cancel_content':
                    handle_cancel_menu(event['replyToken'], user_id_db, stripe_subscription_id)
                elif postback_data == 'action=help':
                    send_line_message(event['replyToken'], get_help_message())
                elif postback_data == 'action=share':
                    share_message = """📢 友達に紹介

AIコレクションズをご利用いただき、ありがとうございます！

🤝 友達にもおすすめしませんか？
• 1個目のコンテンツは無料
• 月額5,000円で複数のAIツールを利用可能
• 従量課金で必要な分だけ追加

🔗 紹介URL：
https://lp-production-9e2c.up.railway.app

友達が登録すると、あなたにも特典があります！"""
                    send_line_message(event['replyToken'], [{"type": "text", "text": share_message}])
                conn.close()
    except Exception as e:
        import traceback
        traceback.print_exc()
    return jsonify({'status': 'ok'}) 