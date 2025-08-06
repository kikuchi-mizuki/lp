import requests
import sqlite3
import psycopg2
import os
import stripe
import traceback
import time
from datetime import datetime, timedelta
from utils.db import get_db_connection
from services.stripe_service import check_subscription_status
import re
from services.subscription_period_service import SubscriptionPeriodService
import json

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

def send_line_message(reply_token, messages):
    """LINEメッセージ送信（複数メッセージ対応）"""
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    
    if not LINE_CHANNEL_ACCESS_TOKEN:
        print('❌ LINE_CHANNEL_ACCESS_TOKENが設定されていません')
        return
    
    # replyTokenの重複使用チェック
    if hasattr(send_line_message, 'used_tokens'):
        if reply_token in send_line_message.used_tokens:
            print(f'[WARN] replyTokenが既に使用済みです: {reply_token}')
            return
    else:
        send_line_message.used_tokens = set()
    
    # replyTokenを記録
    send_line_message.used_tokens.add(reply_token)
    
    # 古いトークンをクリア（30秒以上前のもの）
    current_time = time.time()
    if hasattr(send_line_message, 'token_times'):
        expired_tokens = [token for token, timestamp in send_line_message.token_times.items() 
                         if current_time - timestamp > 30]
        for token in expired_tokens:
            send_line_message.used_tokens.discard(token)
            del send_line_message.token_times[token]
    else:
        send_line_message.token_times = {}
    
    send_line_message.token_times[reply_token] = current_time
    
    headers = {
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # 単一メッセージの場合はリスト化
    if not isinstance(messages, list):
        messages = [messages]
    
    # メッセージの検証と修正
    validated_messages = []
    for msg in messages:
        if msg.get('type') == 'text':
            # テキストメッセージの文字数制限（2000文字）
            text = msg.get('text', '')
            if len(text) > 2000:
                print(f'[WARN] テキストが長すぎます（{len(text)}文字）。2000文字に制限します。')
                msg['text'] = text[:1997] + '...'
        elif msg.get('type') == 'template' and 'template' in msg:
            tmpl = msg['template']
            if tmpl.get('type') == 'buttons':
                # actionsが5つ以上のボタンテンプレートがあれば4つまでに制限
                if 'actions' in tmpl and len(tmpl['actions']) > 4:
                    print('[WARN] actionsが5つ以上のため4つまでに自動制限します')
                    tmpl['actions'] = tmpl['actions'][:4]
                # テキストの文字数制限（120文字）
                if 'text' in tmpl and len(tmpl['text']) > 120:
                    print(f'[WARN] ボタンテンプレートのテキストが長すぎます（{len(tmpl["text"])}文字）。120文字に制限します。')
                    tmpl['text'] = tmpl['text'][:117] + '...'
        
        validated_messages.append(msg)
    
    data = {
        'replyToken': reply_token,
        'messages': validated_messages
    }
    
    print('[DEBUG] LINE送信内容:', data)
    print('[DEBUG] LINE API送信開始')
    
    try:
        response = requests.post('https://api.line.me/v2/bot/message/reply', headers=headers, json=data, timeout=10)
        
        if response.status_code == 400:
            print(f'[DEBUG] LINE API 400エラー詳細: {response.text}')
            try:
                error_detail = response.json()
                print(f'[DEBUG] LINE API エラー詳細JSON: {error_detail}')
                if 'message' in error_detail:
                    if 'reply token' in error_detail['message'].lower():
                        print(f'[DEBUG] replyTokenエラー: {error_detail["message"]}')
                        # replyTokenエラーの場合は、トークンを削除して再試行を許可
                        send_line_message.used_tokens.discard(reply_token)
                        if reply_token in send_line_message.token_times:
                            del send_line_message.token_times[reply_token]
                        # replyTokenエラーの場合は、エラーとして処理せずに正常終了
                        print(f'[DEBUG] replyTokenエラーのため、メッセージ送信をスキップします')
                        return
                    elif 'invalid' in error_detail['message'].lower():
                        print(f'[DEBUG] 無効なリクエストエラー: {error_detail["message"]}')
                        # 無効なリクエストの場合は、エラーとして処理
                        raise Exception(f'LINE API 無効なリクエスト: {error_detail["message"]}')
            except Exception as parse_error:
                print(f'[DEBUG] LINE API エラー詳細（JSON解析失敗）: {response.text}')
                # JSON解析に失敗した場合は、エラーとして処理
                raise Exception(f'LINE API 400エラー: {response.text}')
        
        response.raise_for_status()
        print(f'[DEBUG] LINE API送信成功: status_code={response.status_code}')
        print('[DEBUG] LINE API送信処理完了')
    except requests.exceptions.Timeout:
        print('❌ LINE API タイムアウトエラー')
        with open('error.log', 'a', encoding='utf-8') as f:
            f.write(f'{datetime.now().isoformat()} - LINE API タイムアウトエラー\n')
    except Exception as e:
        print(f'LINEメッセージ送信エラー: {e}')
        if hasattr(e, 'response') and e.response is not None:
            print(f'LINE API エラー詳細: {e.response.text}')
            print(f'LINE API レスポンスヘッダー: {e.response.headers}')
            print(f'LINE API リクエストデータ: {data}')
        traceback.print_exc()
        # エラー詳細をerror.logにも追記
        with open('error.log', 'a', encoding='utf-8') as f:
            f.write(f'{datetime.now().isoformat()} - LINEメッセージ送信エラー: {str(e)}\n')
            if hasattr(e, 'response') and e.response is not None:
                f.write(f'LINE API エラー詳細: {e.response.text}\n')
                f.write(f'LINE API リクエストデータ: {data}\n')
            f.write(traceback.format_exc() + '\n')

def send_welcome_with_buttons(reply_token):
    """ウェルカムメッセージ（ボタン付き）"""
    welcome_message = {
        "type": "template",
        "altText": "AI Collections へようこそ",
        "template": {
            "type": "buttons",
            "title": "AI Collections へようこそ",
            "text": "AI予定秘書、AI経理秘書、AIタスクコンシェルジュの3つのサービスをご利用いただけます。",
            "thumbnailImageUrl": "https://ai-collections.herokuapp.com/static/images/logo.png",
            "imageAspectRatio": "rectangle",
            "imageSize": "cover",
            "imageBackgroundColor": "#FFFFFF",
            "actions": [
                {
                    "type": "message",
                    "label": "コンテンツ追加",
                    "text": "追加"
                },
                {
                    "type": "message",
                    "label": "利用状況確認",
                    "text": "状態"
                },
                {
                    "type": "message",
                    "label": "解約",
                    "text": "解約"
                },
                {
                    "type": "message",
                    "label": "ヘルプ",
                    "text": "ヘルプ"
                }
            ]
        }
    }
    send_line_message(reply_token, [welcome_message])

def send_welcome_with_buttons_push(user_id):
    """プッシュメッセージでウェルカムメッセージ（ボタン付き）"""
    welcome_message = {
        "type": "template",
        "altText": "AI Collections へようこそ",
        "template": {
            "type": "buttons",
            "title": "AI Collections へようこそ",
            "text": "AI予定秘書、AI経理秘書、AIタスクコンシェルジュの3つのサービスをご利用いただけます。",
            "thumbnailImageUrl": "https://ai-collections.herokuapp.com/static/images/logo.png",
            "imageAspectRatio": "rectangle",
            "imageSize": "cover",
            "imageBackgroundColor": "#FFFFFF",
            "actions": [
                {
                    "type": "message",
                    "label": "コンテンツ追加",
                    "text": "追加"
                },
                {
                    "type": "message",
                    "label": "利用状況確認",
                    "text": "状態"
                },
                {
                    "type": "message",
                    "label": "解約",
                    "text": "解約"
                },
                {
                    "type": "message",
                    "label": "ヘルプ",
                    "text": "ヘルプ"
                }
            ]
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
    }
    
    push_data = {
        'to': user_id,
        'messages': [welcome_message]
    }
    
    try:
        response = requests.post(
            'https://api.line.me/v2/bot/message/push',
            headers=headers,
            data=json.dumps(push_data)
        )
        
        if response.status_code == 200:
            print(f'[DEBUG] プッシュメッセージ送信成功: {user_id}')
        else:
            print(f'[DEBUG] プッシュメッセージ送信失敗: {response.status_code}, {response.text}')
    except Exception as e:
        print(f'[DEBUG] プッシュメッセージ送信エラー: {e}')

def handle_add_content(reply_token, user_id_db, stripe_subscription_id):
    """コンテンツ追加メニュー表示"""
    try:
        # サブスクリプション状態をチェック
        subscription_status = check_subscription_status(stripe_subscription_id)
        is_trial_period = subscription_status.get('subscription', {}).get('status') == 'trialing'
        
        # 利用可能なコンテンツを定義
        available_contents = [
            {'name': 'AI予定秘書', 'description': 'スケジュール管理をAIがサポート'},
            {'name': 'AI経理秘書', 'description': '経理作業をAIが効率化'},
            {'name': 'AIタスクコンシェルジュ', 'description': 'タスク管理をAIが最適化'}
        ]
        
        # 既に追加されているコンテンツを確認
        conn = get_db_connection()
        c = conn.cursor()
        
        # データベースタイプに応じて適切なプレースホルダーを使用
        from utils.db import get_db_type
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        # 使用量ログを確認
        c.execute(f'SELECT COUNT(*) FROM usage_logs WHERE user_id = {placeholder}', (user_id_db,))
        total_usage_count = c.fetchone()[0]
        
        # デバッグ用：実際のusage_logsを確認
        c.execute(f'SELECT id, content_type, created_at FROM usage_logs WHERE user_id = {placeholder} ORDER BY created_at', (user_id_db,))
        all_logs = c.fetchall()
        print(f'[DEBUG] 全usage_logs: {all_logs}')
        
        # 同じコンテンツの追加回数を確認
        c.execute(f'SELECT COUNT(*) FROM usage_logs WHERE user_id = {placeholder} AND content_type = {placeholder}', (user_id_db, content['name']))
        same_content_count = c.fetchone()[0]
        conn.close()
        
        print(f'[DEBUG] total_usage_count: {total_usage_count}')
        print(f'[DEBUG] same_content_count: {same_content_count}')
        print(f'[DEBUG] content_type: {content["name"]}')
        
        # 同じコンテンツが既に追加されている場合
        if same_content_count > 0:
            already_added_message = {
                "type": "template",
                "altText": "すでに追加されています",
                "template": {
                    "type": "buttons",
                    "title": "すでに追加されています",
                    "text": f"{content['name']}は既に追加済みです。\n\n他のコンテンツを追加するか、利用状況を確認してください。",
                    "actions": [
                        {
                            "type": "message",
                            "label": "他のコンテンツ追加",
                            "text": "追加"
                        },
                        {
                            "type": "message",
                            "label": "利用状況確認",
                            "text": "状態"
                        }
                    ]
                }
            }
            send_line_message(reply_token, [already_added_message])
            return
        
        # サブスクリプションのトライアル期間をチェック
        try:
            subscription_status = check_subscription_status(stripe_subscription_id)
            is_trial_period = subscription_status.get('subscription', {}).get('status') == 'trialing'
            print(f'[DEBUG] サブスクリプション状態: {subscription_status}')
        except Exception as e:
            print(f'[DEBUG] Stripeサブスクリプション状態確認エラー: {e}')
            # エラーの場合はデフォルト値を使用
            is_trial_period = False
            subscription_status = {'subscription': {'status': 'error'}}
        
        # トライアル期間終了後のコンテンツ追加回数を正しく計算
        if is_trial_period:
            # トライアル期間中でも、1個目は無料、2個目以降は有料（トライアル終了後に課金）
            current_count = total_usage_count + 1
            is_free = current_count == 1
            print(f'[DEBUG] トライアル期間中: total_usage_count={total_usage_count}, current_count={current_count}, is_free={is_free}')
        else:
            # トライアル期間終了後は、トライアル期間中の追加分を除いて計算
            # トライアル期間中の追加分を取得
            try:
                conn_trial = get_db_connection()
                c_trial = conn_trial.cursor()
                
                # データベースタイプに応じて適切なプレースホルダーを使用
                db_type = get_db_type()
                placeholder = '%s' if db_type == 'postgresql' else '?'
                
                c_trial.execute(f'''
                    SELECT COUNT(*) FROM usage_logs 
                    WHERE user_id = {placeholder} AND pending_charge = FALSE
                ''', (user_id_db,))
                trial_additions = c_trial.fetchone()[0]
                conn_trial.close()
                
                # トライアル期間終了後の追加回数
                post_trial_count = total_usage_count - trial_additions + 1
                current_count = post_trial_count
                is_free = current_count == 1
                print(f'[DEBUG] 通常期間: total_usage_count={total_usage_count}, trial_additions={trial_additions}, current_count={current_count}, is_free={is_free}')
            except Exception as e:
                print(f'[DEBUG] トライアル期間計算エラー: {e}')
                # エラーの場合はシンプルな計算
                current_count = total_usage_count + 1
                is_free = current_count == 1
                print(f'[DEBUG] フォールバック計算: total_usage_count={total_usage_count}, current_count={current_count}, is_free={is_free}')
        
        if current_count == 1:
            price_message = f"料金：無料（{current_count}個目）"
        else:
            price_message = f"料金：1,500円（{current_count}個目、月額料金に追加）"
            print(f'[DEBUG] 2個目以降のコンテンツ追加: is_free={is_free}, current_count={current_count}')
        
        # コンテンツ選択メニューを表示
        content_selection_message = {
            "type": "template",
            "altText": "コンテンツ選択",
            "template": {
                "type": "buttons",
                "title": "コンテンツ選択",
                "text": "追加したいコンテンツを選択してください：\n\n1. AI予定秘書\n2. AI経理秘書\n3. AIタスクコンシェルジュ",
                "actions": [
                    {
                        "type": "message",
                        "label": "AI予定秘書",
                        "text": "1"
                    },
                    {
                        "type": "message",
                        "label": "AI経理秘書",
                        "text": "2"
                    },
                    {
                        "type": "message",
                        "label": "AIタスクコンシェルジュ",
                        "text": "3"
                    }
                ]
            }
        }
        send_line_message(reply_token, [content_selection_message])
        
    except Exception as e:
        print(f'コンテンツ追加メニュー表示エラー: {e}')
        send_line_message(reply_token, [{"type": "text", "text": "❌ エラーが発生しました。しばらく時間をおいて再度お試しください。"}])

def handle_content_selection(reply_token, user_id_db, stripe_subscription_id, content_number):
    """コンテンツ選択処理"""
    try:
        # コンテンツ番号からコンテンツ名を取得
        content_mapping = {
            '1': 'AI予定秘書',
            '2': 'AI経理秘書', 
            '3': 'AIタスクコンシェルジュ'
        }
        
        content_type = content_mapping.get(content_number)
        if not content_type:
            return {
                'success': False,
                'error': '無効なコンテンツ番号です'
            }
        
        # データベースタイプに応じて適切なプレースホルダーを使用
        from utils.db import get_db_type
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        # 解約対象のコンテンツを取得
        c.execute(f'''
            SELECT id, content_type, is_free, stripe_usage_record_id 
            FROM usage_logs 
            WHERE user_id = {placeholder} AND content_type = {placeholder}
            ORDER BY created_at DESC
            LIMIT 1
        ''', (user_id_db, content_type))
        
        usage_log = c.fetchone()
        if not usage_log:
            return {
                'success': False,
                'error': f'{content_type}は追加されていません'
            }
        
        usage_id, content_type, is_free, stripe_usage_record_id = usage_log
        
        # 解約処理
        # 1. usage_logsテーブルから削除
        c.execute(f'DELETE FROM usage_logs WHERE id = {placeholder}', (usage_id,))
        
        # 2. StripeのUsage Recordを削除（課金済みの場合）
        if stripe_usage_record_id and not is_free:
            try:
                stripe.UsageRecord.delete(stripe_usage_record_id)
                print(f'[DEBUG] Stripe Usage Record削除: {stripe_usage_record_id}')
            except Exception as e:
                print(f'[DEBUG] Stripe Usage Record削除エラー: {e}')
        
        conn.commit()
        conn.close()
        
        print(f'[DEBUG] 解約処理完了: user_id={user_id_db}, content_type={content_type}')
        
        return {
            'success': True,
            'content_type': content_type
        }
        
    except Exception as e:
        print(f'[ERROR] 解約確認処理エラー: {e}')
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

def get_welcome_message():
    return "ようこそ！LINE連携が完了しました。"

def get_not_registered_message():
    return "ご登録情報が見つかりません。LPからご登録ください。"

def handle_cancel_request(reply_token, user_id_db, stripe_subscription_id):
    """解約リクエスト処理"""
    try:
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        items = subscription['items']['data']
        
        # サブスクリプション状態をチェック
        subscription_status = check_subscription_status(stripe_subscription_id)
        is_trial_period = subscription_status.get('subscription', {}).get('status') == 'trialing'
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # データベースタイプに応じて適切なプレースホルダーを使用
        from utils.db import get_db_type
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        # 実際に追加されたコンテンツを取得
        c.execute(f'SELECT content_type, is_free FROM usage_logs WHERE user_id = {placeholder} ORDER BY created_at', (user_id_db,))
        added_contents = c.fetchall()
        conn.close()
        
        print(f'[DEBUG] 解約対象コンテンツ取得: user_id={user_id_db}, count={len(added_contents)}')
        for content in added_contents:
            print(f'[DEBUG] コンテンツ: {content}')
        
        content_choices = []
        choice_index = 1
        
        # 実際に追加されたコンテンツのみを表示
        for content_type, is_free in added_contents:
            if content_type in ['AI予定秘書', 'AI経理秘書', 'AIタスクコンシェルジュ']:
                if is_free:
                    display_price = '無料'
                else:
                    display_price = '1,500円'
                
                content_choices.append({
                    'index': choice_index,
                    'type': content_type,
                    'price': display_price,
                    'is_free': is_free
                })
                choice_index += 1
        
        if not content_choices:
            # 解約対象のコンテンツがない場合
            no_content_message = {
                "type": "template",
                "altText": "解約対象なし",
                "template": {
                    "type": "buttons",
                    "title": "解約対象なし",
                    "text": "現在、解約可能なコンテンツはありません。\n\nコンテンツを追加してから解約してください。",
                    "actions": [
                        {
                            "type": "message",
                            "label": "コンテンツ追加",
                            "text": "追加"
                        },
                        {
                            "type": "message",
                            "label": "メニューに戻る",
                            "text": "メニュー"
                        }
                    ]
                }
            }
            send_line_message(reply_token, [no_content_message])
            return
        
        # 解約メニューを表示
        cancel_menu_text = "解約したいコンテンツを選択してください：\n\n"
        for choice in content_choices:
            cancel_menu_text += f"{choice['index']}. {choice['type']} ({choice['price']})\n"
        
        cancel_menu_message = {
            "type": "template",
            "altText": "解約メニュー",
            "template": {
                "type": "buttons",
                "title": "解約メニュー",
                "text": cancel_menu_text,
                "actions": [
                    {
                        "type": "message",
                        "label": "メニューに戻る",
                        "text": "メニュー"
                    }
                ]
            }
        }
        send_line_message(reply_token, [cancel_menu_message])
        
    except Exception as e:
        print(f'[ERROR] 解約リクエスト処理エラー: {e}')
        import traceback
        traceback.print_exc()
        send_line_message(reply_token, [{"type": "text", "text": "❌ エラーが発生しました。しばらく時間をおいて再度お試しください。"}])

def handle_cancel_selection(reply_token, user_id_db, stripe_subscription_id, selection_text):
    """解約選択処理"""
    try:
        # Stripeの設定は既にapp.pyで行われているため、ここでは不要
        
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        items = subscription['items']['data']
        
        # 実際に追加されたコンテンツを取得
        conn = get_db_connection()
        c = conn.cursor()
        
        # データベースタイプに応じて適切なプレースホルダーを使用
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        c.execute(f'SELECT id, content_type, is_free FROM usage_logs WHERE user_id = {placeholder} ORDER BY created_at', (user_id_db,))
        added_contents = c.fetchall()
        
        # 選択された番号を解析（AI技術を活用した高度な数字抽出処理）
        numbers = smart_number_extraction(selection_text)
        valid_numbers, invalid_reasons, duplicates = validate_selection_numbers(numbers, len(added_contents))
        selected_indices = valid_numbers
        
        print(f'[DEBUG] 選択テキスト: {selection_text}')
        print(f'[DEBUG] 抽出された数字: {numbers}')
        print(f'[DEBUG] 有効な選択インデックス: {selected_indices}')
        print(f'[DEBUG] 最大選択可能数: {len(added_contents)}')
        
        if invalid_reasons:
            print(f'[DEBUG] 無効な入力: {invalid_reasons}')
        if duplicates:
            print(f'[DEBUG] 重複除去: {duplicates}')
        
        # LINEユーザーIDを事前に取得
        line_user_id = None
        c.execute(f'SELECT line_user_id FROM users WHERE id = {placeholder}', (user_id_db,))
        line_result = c.fetchone()
        if line_result and line_result[0]:
            line_user_id = line_result[0]
        
        cancelled = []
        choice_index = 1
        
        # 実際に追加されたコンテンツの処理
        for usage_id, content_type, is_free in added_contents:
            if content_type in ['AI予定秘書', 'AI経理秘書', 'AIタスクコンシェルジュ']:
                print(f'[DEBUG] 処理中: choice_index={choice_index}, content_type={content_type}, usage_id={usage_id}')
                if choice_index in selected_indices:
                    # まずstripe_usage_record_idを取得（削除前に）
                    stripe_usage_record_id = None
                    if not is_free:
                        c.execute('SELECT stripe_usage_record_id FROM usage_logs WHERE id = %s', (usage_id,))
                        result = c.fetchone()
                        if result and result[0]:
                            stripe_usage_record_id = result[0]
                    
                    # データベースからusage_logsを削除
                    c.execute('DELETE FROM usage_logs WHERE id = %s', (usage_id,))
                    cancelled.append(content_type)
                    print(f'[DEBUG] 解約処理: content_type={content_type}, usage_id={usage_id}')
                    
                    # StripeのInvoice Itemを削除（有料コンテンツの場合）
                    if stripe_usage_record_id:
                        try:
                            print(f'[DEBUG] Stripe InvoiceItem削除開始: {stripe_usage_record_id}')
                            
                            # StripeのInvoice Itemを削除
                            invoice_item = stripe.InvoiceItem.retrieve(stripe_usage_record_id)
                            invoice_item.delete()
                            print(f'[DEBUG] Stripe InvoiceItem削除成功: {stripe_usage_record_id}')
                        
                        except Exception as e:
                            print(f'[DEBUG] Stripe InvoiceItem削除エラー: {e}')
                            # エラーが発生しても処理は続行
                choice_index += 1
        
        print(f'[DEBUG] 解約対象コンテンツ数: {len(cancelled)}')
        print(f'[DEBUG] 解約対象: {cancelled}')
        
        # データベースの変更をコミット
        conn.commit()
        conn.close()
        
        if cancelled:
            # サブスクリプション状態をチェック
            subscription_status = check_subscription_status(stripe_subscription_id)
            is_trial_period = subscription_status.get('subscription', {}).get('status') == 'trialing'
            
            # 1通目: 解約完了のテキストメッセージ
            cancel_text_message = {
                "type": "text",
                "text": f"以下のコンテンツの解約を受け付けました：\n\n" + "\n".join([f"• {content}" for content in cancelled])
            }
            send_line_message(reply_token, [cancel_text_message])
            
            # 2通目: 公式LINE利用制限メッセージ
            line_restriction_message = {
                "type": "template",
                "altText": "公式LINEの利用制限",
                "template": {
                    "type": "buttons",
                    "title": "公式LINEの利用制限",
                    "text": f"解約されたコンテンツの公式LINEは利用できなくなります。\n\n解約されたコンテンツ：\n" + "\n".join([f"• {content}" for content in cancelled]),
                    "thumbnailImageUrl": "https://ai-collections.herokuapp.com/static/images/logo.png",
                    "imageAspectRatio": "rectangle",
                    "imageSize": "cover",
                    "imageBackgroundColor": "#FFFFFF",
                    "actions": [
                        {
                            "type": "message",
                            "label": "他のコンテンツ追加",
                            "text": "追加"
                        },
                        {
                            "type": "message",
                            "label": "利用状況確認",
                            "text": "状態"
                        }
                    ]
                }
            }
            
            # push_messageで2通目のメッセージを送信
            if line_user_id:
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
                }
                
                push_data = {
                    'to': line_user_id,
                    'messages': [line_restriction_message]
                }
                
                response = requests.post(
                    'https://api.line.me/v2/bot/message/push',
                    headers=headers,
                    data=json.dumps(push_data)
                )
                
                if response.status_code == 200:
                    print(f'[DEBUG] 2通目の公式LINE制限メッセージ送信成功: {line_user_id}')
                else:
                    print(f'[DEBUG] 2通目の公式LINE制限メッセージ送信失敗: {response.status_code}, {response.text}')
            
            # 3通目: アクションボタン（push_messageで送信）
            cancel_buttons_message = {
                "type": "template",
                "altText": "次のアクションを選択",
                "template": {
                    "type": "buttons",
                    "title": "次のアクション",
                    "text": "何か他にお手伝いできることはありますか？",
                    "actions": [
                        {
                            "type": "message",
                            "label": "他のコンテンツ追加",
                            "text": "追加"
                        },
                        {
                            "type": "message",
                            "label": "利用状況確認",
                            "text": "状態"
                        },
                        {
                            "type": "message",
                            "label": "メニューに戻る",
                            "text": "メニュー"
                        }
                    ]
                }
            }
            
            # push_messageで3通目のボタンメッセージを送信
            if line_user_id:
                push_data = {
                    'to': line_user_id,
                    'messages': [cancel_buttons_message]
                }
                
                response = requests.post(
                    'https://api.line.me/v2/bot/message/push',
                    headers=headers,
                    data=json.dumps(push_data)
                )
                
                if response.status_code == 200:
                    print(f'[DEBUG] 3通目のボタンメッセージ送信成功: {line_user_id}')
                else:
                    print(f'[DEBUG] 3通目のボタンメッセージ送信失敗: {response.status_code}, {response.text}')
            else:
                print(f'[DEBUG] LINEユーザーIDが見つかりません: user_id_db={user_id_db}')
            
            # 請求期間についての説明を別メッセージで送信（push_messageで送信）
            if is_trial_period:
                period_message = {
                    "type": "text",
                    "text": "トライアル期間中は料金が発生しません。"
                }
            else:
                period_message = {
                    "type": "text",
                    "text": "請求期間終了まで利用可能です。"
                }
            
            # push_messageで3通目のメッセージを送信
            if line_user_id:
                push_data = {
                    'to': line_user_id,
                    'messages': [period_message]
                }
                
                response = requests.post(
                    'https://api.line.me/v2/bot/message/push',
                    headers=headers,
                    data=json.dumps(push_data)
                )
                
                if response.status_code == 200:
                    print(f'[DEBUG] 3通目の期間説明メッセージ送信成功: {line_user_id}')
                else:
                    print(f'[DEBUG] 3通目の期間説明メッセージ送信失敗: {response.status_code}, {response.text}')
            
            # ユーザー状態をリセット
            from models.user_state import clear_user_state
            if line_user_id:
                clear_user_state(line_user_id)
                print(f'[DEBUG] ユーザー状態リセット: {line_user_id}')
        else:
            send_line_message(reply_token, [{"type": "text", "text": "有効な番号が選択されませんでした。もう一度お試しください。"}])
    
    except Exception as e:
        print(f'[ERROR] 解約選択処理エラー: {e}')
        import traceback
        traceback.print_exc()
        send_line_message(reply_token, [{"type": "text", "text": "❌ エラーが発生しました。しばらく時間をおいて再度お試しください。"}])

def handle_subscription_cancel(reply_token, user_id_db, stripe_subscription_id):
    """サブスクリプション全体の解約処理"""
    try:
        # サブスクリプション状態をチェック
        subscription_status = check_subscription_status(stripe_subscription_id)
        is_trial_period = subscription_status.get('subscription', {}).get('status') == 'trialing'
        
        if is_trial_period:
            # トライアル期間中の場合は、期間終了時に解約
            try:
                stripe.Subscription.modify(
                    stripe_subscription_id,
                    cancel_at_period_end=True
                )
                cancel_message = {
                    "type": "template",
                    "altText": "サブスクリプション解約予定",
                    "template": {
                        "type": "buttons",
                        "title": "サブスクリプション解約予定",
                        "text": "サブスクリプションが期間終了時に解約予定になりました。\n\nトライアル期間終了までご利用いただけます。",
                        "actions": [
                            {
                                "type": "message",
                                "label": "メニューに戻る",
                                "text": "メニュー"
                            }
                        ]
                    }
                }
                send_line_message(reply_token, [cancel_message])
            except Exception as e:
                print(f'[DEBUG] Stripe解約エラー: {e}')
                error_message = {
                    "type": "text",
                    "text": "❌ 解約処理中にエラーが発生しました。しばらく時間をおいて再度お試しください。"
                }
                send_line_message(reply_token, [error_message])
        else:
            # 通常期間の場合は、即座に解約
            try:
                stripe.Subscription.delete(stripe_subscription_id)
                cancel_message = {
                    "type": "template",
                    "altText": "サブスクリプション解約完了",
                    "template": {
                        "type": "buttons",
                        "title": "サブスクリプション解約完了",
                        "text": "サブスクリプションを解約しました。\n\nご利用ありがとうございました。",
                        "actions": [
                            {
                                "type": "message",
                                "label": "メニューに戻る",
                                "text": "メニュー"
                            }
                        ]
                    }
                }
                send_line_message(reply_token, [cancel_message])
            except Exception as e:
                print(f'[DEBUG] Stripe解約エラー: {e}')
                error_message = {
                    "type": "text",
                    "text": "❌ 解約処理中にエラーが発生しました。しばらく時間をおいて再度お試しください。"
                }
                send_line_message(reply_token, [error_message])
    
    except Exception as e:
        print(f'[ERROR] サブスクリプション解約処理エラー: {e}')
        import traceback
        traceback.print_exc()
        send_line_message(reply_token, [{"type": "text", "text": "❌ エラーが発生しました。しばらく時間をおいて再度お試しください。"}])

def handle_cancel_menu(reply_token, user_id_db, stripe_subscription_id):
    """解約メニュー表示"""
    try:
        # サブスクリプション状態をチェック
        subscription_status = check_subscription_status(stripe_subscription_id)
        is_trial_period = subscription_status.get('subscription', {}).get('status') == 'trialing'
        
        # 解約メニューを表示
        cancel_menu_message = {
            "type": "template",
            "altText": "解約メニュー",
            "template": {
                "type": "buttons",
                "title": "解約メニュー",
                "text": "どの解約をご希望ですか？",
                "actions": [
                    {
                        "type": "message",
                        "label": "サブスクリプション全体を解約",
                        "text": "サブスクリプション解約"
                    },
                    {
                        "type": "message",
                        "label": "コンテンツを個別解約",
                        "text": "コンテンツ解約"
                    },
                    {
                        "type": "message",
                        "label": "メニューに戻る",
                        "text": "メニュー"
                    }
                ]
            }
        }
        send_line_message(reply_token, [cancel_menu_message])
        
    except Exception as e:
        print(f'[ERROR] 解約メニュー表示エラー: {e}')
        import traceback
        traceback.print_exc()
        send_line_message(reply_token, [{"type": "text", "text": "❌ 解約メニューの表示に失敗しました。しばらく時間をおいて再度お試しください。"}])

def handle_cancel_confirmation(user_id, content_number):
    """解約確認処理"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # コンテンツ番号からコンテンツ名を取得
        content_mapping = {
            '1': 'AI予定秘書',
            '2': 'AI経理秘書', 
            '3': 'AIタスクコンシェルジュ'
        }
        
        content_type = content_mapping.get(content_number)
        if not content_type:
            return {
                'success': False,
                'error': '無効なコンテンツ番号です'
            }
        
        # データベースタイプに応じて適切なプレースホルダーを使用
        from utils.db import get_db_type
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        # 解約対象のコンテンツを取得
        c.execute(f'''
            SELECT id, content_type, is_free, stripe_usage_record_id 
            FROM usage_logs 
            WHERE user_id = {placeholder} AND content_type = {placeholder}
            ORDER BY created_at DESC
            LIMIT 1
        ''', (user_id, content_type))
        
        usage_log = c.fetchone()
        if not usage_log:
            return {
                'success': False,
                'error': f'{content_type}は追加されていません'
            }
        
        usage_id, content_type, is_free, stripe_usage_record_id = usage_log
        
        # 解約処理
        # 1. usage_logsテーブルから削除
        c.execute(f'DELETE FROM usage_logs WHERE id = {placeholder}', (usage_id,))
        
        # 2. StripeのUsage Recordを削除（課金済みの場合）
        if stripe_usage_record_id and not is_free:
            try:
                stripe.UsageRecord.delete(stripe_usage_record_id)
                print(f'[DEBUG] Stripe Usage Record削除: {stripe_usage_record_id}')
            except Exception as e:
                print(f'[DEBUG] Stripe Usage Record削除エラー: {e}')
        
        conn.commit()
        conn.close()
        
        print(f'[DEBUG] 解約処理完了: user_id={user_id}, content_type={content_type}')
        
        return {
            'success': True,
            'content_type': content_type
        }
        
    except Exception as e:
        print(f'[ERROR] 解約確認処理エラー: {e}')
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

def handle_content_confirmation(user_id, content_type):
    """コンテンツ確認処理"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # データベースタイプに応じて適切なプレースホルダーを使用
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        # ユーザーの現在のサブスクリプション情報を取得
        c.execute(f'''
            SELECT stripe_subscription_id, current_period_start, current_period_end
            FROM subscription_periods
            WHERE user_id = {placeholder} AND status = 'active'
            ORDER BY created_at DESC
            LIMIT 1
        ''', (user_id,))
        
        subscription_info = c.fetchone()
        
        if not subscription_info:
            conn.close()
            return {
                'success': False,
                'error': 'アクティブなサブスクリプションが見つかりません'
            }
        
        stripe_subscription_id, current_period_start, current_period_end = subscription_info
        
        # Stripeからサブスクリプション情報を取得
        try:
            subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        except stripe.error.StripeError as e:
            conn.close()
            return {
                'success': False,
                'error': f'Stripeサブスクリプション取得エラー: {str(e)}'
            }
        
        # サブスクリプション期間を更新（重複を避けるためUPSERT使用）
        try:
            c.execute(f'''
                INSERT INTO subscription_periods (
                    user_id, stripe_subscription_id, subscription_status, status,
                    current_period_start, current_period_end,
                    trial_start, trial_end, created_at, updated_at
                ) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                ON CONFLICT (user_id, stripe_subscription_id) DO UPDATE SET
                    subscription_status = EXCLUDED.subscription_status,
                    status = EXCLUDED.status,
                    current_period_start = EXCLUDED.current_period_start,
                    current_period_end = EXCLUDED.current_period_end,
                    trial_start = EXCLUDED.trial_start,
                    trial_end = EXCLUDED.trial_end,
                    updated_at = EXCLUDED.updated_at
            ''', (
                user_id,
                subscription.id,
                subscription.status,
                'active',
                datetime.fromtimestamp(subscription.current_period_start),
                datetime.fromtimestamp(subscription.current_period_end),
                datetime.fromtimestamp(subscription.trial_start) if subscription.trial_start else None,
                datetime.fromtimestamp(subscription.trial_end) if subscription.trial_end else None,
                datetime.now(),
                datetime.now()
            ))
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            conn.close()
            return {
                'success': False,
                'error': f'サブスクリプション期間更新エラー: {str(e)}'
            }
        
        # コンテンツ確認ログを記録
        try:
            c.execute(f'''
                INSERT INTO usage_logs (
                    user_id, content_type, usage_quantity, is_free, pending_charge, created_at
                ) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (
                user_id,
                content_type,
                1,  # usage_quantity
                False,  # is_free
                True,   # pending_charge
                datetime.now()
            ))
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            conn.close()
            return {
                'success': False,
                'error': f'使用ログ記録エラー: {str(e)}'
            }
        
        conn.close()
        
        # 企業登録フォームへのリンクを生成
        base_url = os.getenv('BASE_URL', 'https://lp-production-9e2c.up.railway.app')
        registration_url = f"{base_url}/company-registration?subscription_id={subscription.id}&content_type={content_type}"
        
        return {
            'success': True,
            'message': 'コンテンツ確認が完了しました',
            'subscription_status': subscription.status,
            'trial_end': subscription.trial_end,
            'registration_url': registration_url
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'コンテンツ確認処理エラー: {str(e)}'
        }

def handle_status_check(reply_token, user_id_db):
    """ユーザーの利用状況を確認してLINEメッセージで返す"""
    try:
        # LINEユーザーIDを直接使用
        line_user_id = user_id_db
        
        # 企業紐付け完了後のため、制限チェックは不要
        
        # 決済済みユーザーの場合、企業情報を取得
        conn = get_db_connection()
        c = conn.cursor()
        
        # 企業情報を取得
        c.execute('SELECT company_name, stripe_subscription_id FROM companies WHERE line_user_id = %s', (line_user_id,))
        company = c.fetchone()
        
        if not company:
            send_line_message(reply_token, [{"type": "text", "text": "企業情報が見つかりません。"}])
            return
        
        company_name = company[0]
        stripe_subscription_id = company[1]
        
        # 利用状況を取得（企業中心）
        c.execute('''
            SELECT content_type, created_at, is_free, subscription_status
            FROM usage_logs 
            WHERE company_id = (SELECT id FROM companies WHERE line_user_id = %s)
            ORDER BY created_at DESC
        ''', (line_user_id,))
        usage_logs = c.fetchall()
        
        # サブスクリプション状況を確認
        subscription_status = "無効"
        if stripe_subscription_id:
            try:
                subscription = stripe.Subscription.retrieve(stripe_subscription_id)
                if subscription.status == 'active':
                    subscription_status = "有効"
                elif subscription.status == 'trialing':
                    subscription_status = "トライアル中"
                elif subscription.status == 'canceled':
                    subscription_status = "解約済み"
                elif subscription.status == 'past_due':
                    subscription_status = "支払い遅延"
            
            except Exception as e:
                print(f'[DEBUG] Stripe API エラー: {e}')
                subscription_status = "確認エラー"
        
        # メッセージを構築
        status_message = f"📊 利用状況\n\n"
        status_message += f"🏢 企業名: {company_name}\n"
        status_message += f"💳 サブスクリプション: {subscription_status}\n\n"
        
        if usage_logs:
            status_message += "📋 利用コンテンツ:\n"
            content_count = {}
            for log in usage_logs:
                content_type = log[0]
                created_at = log[1]
                is_free = log[2]
                subscription_status = log[3]
                
                if content_type not in content_count:
                    content_count[content_type] = {
                        'total': 0,
                        'free': 0,
                        'paid': 0,
                        'active': 0
                    }
                
                content_count[content_type]['total'] += 1
                if is_free:
                    content_count[content_type]['free'] += 1
                elif subscription_status == 'active':
                    content_count[content_type]['active'] += 1
                else:
                    content_count[content_type]['paid'] += 1
            
            for content_type, counts in content_count.items():
                status_message += f"• {content_type}: {counts['total']}回利用"
                if counts['free'] > 0:
                    status_message += f" (無料: {counts['free']}回)"
                if counts['paid'] > 0:
                    status_message += f" (有料: {counts['paid']}回)"
                if counts['active'] > 0:
                    status_message += f" (有効: {counts['active']}回)"
                status_message += "\n"
        else:
            status_message += "📋 利用コンテンツ: まだ利用していません\n"
        
        # 一通りの流れが終わった後の案内を追加
        status_message += "\n💡 何かお手伝いできることはありますか？\n"
        status_message += "📱 「メニュー」と入力すると、メインメニューに戻れます。\n"
        status_message += "❓ 使い方がわからない場合は「ヘルプ」と入力してください。"
        
        send_line_message(reply_token, [{"type": "text", "text": status_message}])
        
    except Exception as e:
        print(f'[ERROR] 利用状況確認エラー: {e}')
        import traceback
        traceback.print_exc()
        send_line_message(reply_token, [{"type": "text", "text": "❌ エラーが発生しました。しばらく時間をおいて再度お試しください。"}])

def extract_numbers_from_text(text):
    """AI技術を活用した高度な数字抽出処理"""
    import re
    
    # 基本的な数字抽出
    numbers = re.findall(r'\d+', text)
    
    # 日本語の数字表現も対応（一、二、三など）
    japanese_numbers = {
        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
        '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
        '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15,
        '十六': 16, '十七': 17, '十八': 18, '十九': 19, '二十': 20
    }
    
    for japanese, number in japanese_numbers.items():
        if japanese in text:
            numbers.append(str(number))
    
    # 重複を除去してソート
    unique_numbers = list(set(numbers))
    unique_numbers.sort(key=int)
    
    return unique_numbers

def validate_selection_numbers(numbers, max_count):
    """選択された数字の検証"""
    valid_numbers = []
    invalid_reasons = []
    duplicates = []
    
    for num_str in numbers:
        try:
            num = int(num_str)
            if num < 1:
                invalid_reasons.append(f"{num}は1未満です")
            elif num > max_count:
                invalid_reasons.append(f"{num}は最大値{max_count}を超えています")
            elif num in valid_numbers:
                duplicates.append(num)
            else:
                valid_numbers.append(num)
        except ValueError:
            invalid_reasons.append(f"{num_str}は有効な数字ではありません")
    
    return valid_numbers, invalid_reasons, duplicates

def smart_number_extraction(text):
    """AI技術を活用した高度な数字抽出処理"""
    import re
    
    # 基本的な数字抽出
    numbers = re.findall(r'\d+', text)
    
    # 日本語の数字表現も対応（一、二、三など）
    japanese_numbers = {
        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
        '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
        '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15,
        '十六': 16, '十七': 17, '十八': 18, '十九': 19, '二十': 20
    }
    
    for japanese, number in japanese_numbers.items():
        if japanese in text:
            numbers.append(str(number))
    
    # 重複を除去してソート
    unique_numbers = list(set(numbers))
    unique_numbers.sort(key=int)
    
    return unique_numbers 

def handle_add_content_company(reply_token, company_id, stripe_subscription_id):
    """企業ユーザー専用：コンテンツ追加メニュー表示"""
    try:
        # サブスクリプション状態をチェック
        subscription_status = check_subscription_status(stripe_subscription_id)
        is_trial_period = subscription_status.get('subscription', {}).get('status') == 'trialing'
        
        # 利用可能なコンテンツを定義
        available_contents = [
            {'name': 'AI予定秘書', 'description': 'スケジュール管理をAIがサポート'},
            {'name': 'AI経理秘書', 'description': '経理作業をAIが効率化'},
            {'name': 'AIタスクコンシェルジュ', 'description': 'タスク管理をAIが最適化'}
        ]
        
        # 既に追加されているコンテンツを確認
        conn = get_db_connection()
        c = conn.cursor()
        
        # データベースタイプに応じて適切なプレースホルダーを使用
        from utils.db import get_db_type
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        # 企業のサブスクリプション数を確認
        c.execute(f'SELECT COUNT(*) FROM company_subscriptions WHERE company_id = {placeholder} AND subscription_status = {placeholder}', (company_id, 'active'))
        total_subscription_count = c.fetchone()[0]
        
        # 企業のLINEアカウント数を確認
        c.execute(f'SELECT COUNT(*) FROM company_line_accounts WHERE company_id = {placeholder} AND status = "active"', (company_id,))
        total_line_account_count = c.fetchone()[0]
        
        conn.close()
        
        print(f'[DEBUG] 企業コンテンツ追加: company_id={company_id}, total_subscription_count={total_subscription_count}, total_line_account_count={total_line_account_count}')
        
        # コンテンツ選択メニューを作成
        actions = []
        for i, content in enumerate(available_contents, 1):
            actions.append({
                "type": "postback",
                "label": f"{i}. {content['name']}",
                "data": f"content_selection={i}"
            })
        
        # 戻るボタンを追加
        actions.append({
            "type": "message",
            "label": "戻る",
            "text": "メニュー"
        })
        
        message = {
            "type": "template",
            "altText": "コンテンツ追加メニュー",
            "template": {
                "type": "buttons",
                "title": "追加するコンテンツを選択",
                "text": f"現在の利用状況：\n• サブスクリプション：{total_subscription_count}件\n• LINEアカウント：{total_line_account_count}件\n\n追加したいコンテンツを選択してください：",
                "actions": actions
            }
        }
        
        send_line_message(reply_token, [message])
        
    except Exception as e:
        print(f'[DEBUG] 企業コンテンツ追加エラー: {e}')
        import traceback
        traceback.print_exc()
        send_line_message(reply_token, [{"type": "text", "text": "コンテンツ追加処理でエラーが発生しました。"}])

def handle_status_check_company(reply_token, company_id):
    """企業ユーザー専用：利用状況確認"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # データベースタイプに応じて適切なプレースホルダーを使用
        from utils.db import get_db_type
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        # 企業基本情報を取得
        c.execute(f'SELECT company_name, email FROM companies WHERE id = {placeholder}', (company_id,))
        company_info = c.fetchone()
        
        if not company_info:
            send_line_message(reply_token, [{"type": "text", "text": "企業情報が見つかりません。"}])
            conn.close()
            return
            
        company_name, email = company_info
        
        # サブスクリプション情報を取得
        c.execute(f'''
            SELECT content_type, subscription_status, base_price, additional_price, total_price, current_period_end 
            FROM company_subscriptions 
            WHERE company_id = {placeholder}
        ''', (company_id,))
        subscriptions = c.fetchall()
        
        # LINEアカウント情報を取得
        c.execute(f'''
            SELECT content_type, status, line_channel_id 
            FROM company_line_accounts 
            WHERE company_id = {placeholder}
        ''', (company_id,))
        line_accounts = c.fetchall()
        
        conn.close()
        
        # 利用状況メッセージを作成
        status_message = f"🏢 {company_name}\n📧 {email}\n\n"
        
        if subscriptions:
            status_message += "📊 サブスクリプション状況：\n"
            total_monthly_cost = 0
            for sub in subscriptions:
                content_type, status, base_price, additional_price, total_price, period_end = sub
                status_message += f"• {content_type}: {status}\n"
                status_message += f"  料金: {total_price:,}円/月\n"
                if period_end:
                    status_message += f"  次回請求: {period_end.strftime('%Y/%m/%d')}\n"
                total_monthly_cost += total_price
            status_message += f"\n💰 月額合計: {total_monthly_cost:,}円\n\n"
        else:
            status_message += "📊 サブスクリプション: なし\n\n"
        
        if line_accounts:
            status_message += "📱 LINEアカウント状況：\n"
            for account in line_accounts:
                content_type, status, line_channel_id = account
                status_message += f"• {content_type}: {status}\n"
        else:
            status_message += "📱 LINEアカウント: なし\n"
        
        send_line_message(reply_token, [{"type": "text", "text": status_message}])
        
    except Exception as e:
        print(f'[DEBUG] 企業利用状況確認エラー: {e}')
        import traceback
        traceback.print_exc()
        send_line_message(reply_token, [{"type": "text", "text": "利用状況確認でエラーが発生しました。"}])

def handle_cancel_menu_company(reply_token, company_id, stripe_subscription_id):
    """企業ユーザー専用：コンテンツ削除メニュー表示"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # データベースタイプに応じて適切なプレースホルダーを使用
        from utils.db import get_db_type
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        # アクティブなサブスクリプションを取得
        c.execute(f'''
            SELECT content_type, total_price 
            FROM company_subscriptions 
            WHERE company_id = {placeholder} AND subscription_status = {placeholder}
        ''', (company_id, 'active'))
        active_subscriptions = c.fetchall()
        
        conn.close()
        
        if not active_subscriptions:
            send_line_message(reply_token, [{"type": "text", "text": "削除可能なコンテンツがありません。"}])
            return
        
        # 削除メニューを作成
        actions = []
        for i, (content_type, total_price) in enumerate(active_subscriptions, 1):
            actions.append({
                "type": "postback",
                "label": f"{i}. {content_type} ({total_price:,}円/月)",
                "data": f"cancel_selection={content_type}"
            })
        
        # 戻るボタンを追加
        actions.append({
            "type": "message",
            "label": "戻る",
            "text": "メニュー"
        })
        
        message = {
            "type": "template",
            "altText": "コンテンツ削除メニュー",
            "template": {
                "type": "buttons",
                "title": "削除するコンテンツを選択",
                "text": f"現在のアクティブなコンテンツ：{len(active_subscriptions)}件\n\n削除したいコンテンツを選択してください：",
                "actions": actions
            }
        }
        
        send_line_message(reply_token, [message])
        
    except Exception as e:
        print(f'[DEBUG] 企業コンテンツ削除メニューエラー: {e}')
        import traceback
        traceback.print_exc()
        send_line_message(reply_token, [{"type": "text", "text": "コンテンツ削除メニューでエラーが発生しました。"}])

def get_help_message_company():
    """企業ユーザー専用：ヘルプメッセージ"""
    return """🤖 AIコレクションズ 企業向けヘルプ

📋 利用可能なコマンド：
• 「追加」- 新しいコンテンツを追加
• 「状態」- 現在の利用状況を確認
• 「削除」- コンテンツを削除
• 「メニュー」- メインメニューを表示

💰 料金体系：
• 基本料金：月額3,900円
• 追加コンテンツ：1件1,500円/月

📞 サポート：
ご不明な点がございましたら、お気軽にお問い合わせください。""" 

def handle_content_confirmation_company(company_id, content_type):
    """企業ユーザー専用：コンテンツ確認処理"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # データベースタイプに応じて適切なプレースホルダーを使用
        from utils.db import get_db_type
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        # 既存のサブスクリプション数を確認
        c.execute(f'SELECT COUNT(*) FROM company_subscriptions WHERE company_id = {placeholder} AND subscription_status = {placeholder}', (company_id, 'active'))
        existing_count = c.fetchone()[0]
        
        # 料金計算
        base_price = 3900
        additional_price_per_content = 1500
        
        if existing_count == 0:
            # 初回コンテンツ（基本料金のみ）
            total_price = base_price
        else:
            # 追加コンテンツ（基本料金 + 追加料金）
            total_price = base_price + (existing_count * additional_price_per_content)
        
        # 新しいサブスクリプションを作成
        c.execute(f'''
            INSERT INTO company_subscriptions 
            (company_id, content_type, subscription_status, base_price, additional_price, total_price, current_period_end) 
            VALUES ({placeholder}, {placeholder}, 'active', {placeholder}, {placeholder}, {placeholder}, DATE_ADD(NOW(), INTERVAL 1 MONTH))
        ''', (company_id, content_type, base_price, additional_price_per_content, total_price))
        
        # 新しいLINEアカウントを作成
        line_channel_id = f"company_{company_id}_{content_type}_{int(time.time())}"
        c.execute(f'''
            INSERT INTO company_line_accounts 
            (company_id, content_type, line_channel_id, status) 
            VALUES ({placeholder}, {placeholder}, {placeholder}, 'active')
        ''', (company_id, content_type, line_channel_id))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'company_id': company_id,
            'content_type': content_type,
            'total_price': total_price,
            'line_channel_id': line_channel_id
        }
        
    except Exception as e:
        print(f'[DEBUG] 企業コンテンツ確認エラー: {e}')
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if c:
            c.close()
        if conn:
            conn.close() 