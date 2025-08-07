import requests
import sqlite3
import psycopg2
import os
import stripe
import traceback
import time
from datetime import datetime, timedelta
from utils.db import get_db_connection, get_db_type
from services.stripe_service import check_subscription_status
import re
from services.subscription_period_service import SubscriptionPeriodService
import json

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

def send_line_message(reply_token, messages):
    """LINEメッセージ送信（複数メッセージ対応）"""
    print(f'[DEBUG] send_line_message開始: reply_token={reply_token[:20]}...')
    
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    
    if not LINE_CHANNEL_ACCESS_TOKEN:
        print('❌ LINE_CHANNEL_ACCESS_TOKENが設定されていません')
        return
    
    print(f'[DEBUG] LINE_CHANNEL_ACCESS_TOKEN確認: {LINE_CHANNEL_ACCESS_TOKEN[:20]}...')
    
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
    
    print(f'[DEBUG] ヘッダー設定完了: Authorization={headers["Authorization"][:20]}...')
    
    # 単一メッセージの場合はリスト化
    if not isinstance(messages, list):
        messages = [messages]
    
    print(f'[DEBUG] メッセージ数: {len(messages)}')
    
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
        print(f'[DEBUG] LINE APIリクエスト送信: URL=https://api.line.me/v2/bot/message/reply')
        response = requests.post('https://api.line.me/v2/bot/message/reply', headers=headers, json=data, timeout=10)
        print(f'[DEBUG] LINE APIレスポンス受信: status_code={response.status_code}')
        
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
    """ボタン付きウェルカムメッセージを送信"""
    welcome_message = {
        "type": "template",
        "altText": "ようこそ！AIコレクションズへ",
        "template": {
            "type": "buttons",
            "title": "ようこそ！AIコレクションズへ",
            "text": "企業向けAIツールを効率的に利用しましょう。\n\n何かお手伝いできることはありますか？",
            "actions": [
                {
                    "type": "postback",
                    "label": "コンテンツ追加",
                    "data": "action=add_content"
                },
                {
                    "type": "postback",
                    "label": "利用状況確認",
                    "data": "action=check_status"
                },
                {
                    "type": "postback",
                    "label": "ヘルプ",
                    "data": "action=help"
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
        for content in available_contents:
            c.execute(f'SELECT COUNT(*) FROM usage_logs WHERE user_id = {placeholder} AND content_type = {placeholder}', (user_id_db, content['name']))
            same_content_count = c.fetchone()[0]
            print(f'[DEBUG] {content["name"]}の追加回数: {same_content_count}')
        
        conn.close()
        
        print(f'[DEBUG] total_usage_count: {total_usage_count}')
        
        # コンテンツ選択メニューを作成
        actions = []
        for i, content in enumerate(available_contents, 1):
            actions.append({
                "type": "message",
                "label": f"{i}. {content['name']}",
                "text": f"{i}"
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
                "text": f"現在の利用状況：\n• 追加済みコンテンツ：{total_usage_count}件\n\n追加したいコンテンツを選択してください：",
                "actions": actions
            }
        }
        
        send_line_message(reply_token, [message])
        
    except Exception as e:
        print(f'[DEBUG] コンテンツ追加エラー: {e}')
        import traceback
        traceback.print_exc()
        send_line_message(reply_token, [{"type": "text", "text": "コンテンツ追加処理でエラーが発生しました。"}])

def handle_content_selection(reply_token, user_id_db, stripe_subscription_id, content_number):
    """コンテンツ選択処理"""
    try:
        # データベースタイプを取得
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        # コンテンツ情報を定義
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
        
        if content_number not in content_info:
            send_line_message(reply_token, [{"type": "text", "text": "無効なコンテンツ番号です。"}])
            return
        
        content = content_info[content_number]
        
        # 既に追加されているコンテンツを確認
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute(f'SELECT COUNT(*) FROM usage_logs WHERE user_id = {placeholder} AND content_type = {placeholder}', (user_id_db, content['name']))
        existing_count = c.fetchone()[0]
        
        if existing_count > 0:
            send_line_message(reply_token, [{"type": "text", "text": f"{content['name']}は既に追加済みです。"}])
            conn.close()
            return
        
        # サブスクリプション状態をチェック
        subscription_status = check_subscription_status(stripe_subscription_id)
        is_trial_period = subscription_status.get('subscription', {}).get('status') == 'trialing'
        
        # 料金計算
        if is_trial_period:
            price = 0
            price_message = "料金：無料（トライアル期間中）"
        else:
            price = content['price']
            price_message = f"料金：{price:,}円（月額料金に追加）"
        
        # 確認メッセージを送信
        confirmation_message = {
            "type": "template",
            "altText": "コンテンツ追加確認",
            "template": {
                "type": "buttons",
                "title": f"{content['name']}を追加",
                "text": f"{content['description']}\n\n{price_message}\n\n追加しますか？",
                "actions": [
                    {
                        "type": "postback",
                        "label": "はい",
                        "data": f"confirm_add_{content_number}"
                    },
                    {
                        "type": "postback",
                        "label": "いいえ",
                        "data": "cancel_add"
                    }
                ]
            }
        }
        
        send_line_message(reply_token, [confirmation_message])
        conn.close()
        
    except Exception as e:
        print(f'[ERROR] コンテンツ選択処理エラー: {e}')
        import traceback
        traceback.print_exc()
        send_line_message(reply_token, [{"type": "text", "text": "コンテンツ選択処理でエラーが発生しました。"}])

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

def handle_content_confirmation(user_id_db, content_type, stripe_subscription_id):
    """コンテンツ確認処理"""
    try:
        # データベースタイプを取得
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # サブスクリプション状態をチェック
        subscription_status = check_subscription_status(stripe_subscription_id)
        print(f'[DEBUG] サブスクリプション状態: {subscription_status}')
        
        # 利用可能なコンテンツを定義
        content_info = {
            'AI予定秘書': {
                'price': 1500,
                "description": '日程調整のストレスから解放される、スケジュール管理の相棒',
                'usage': 'Googleカレンダーと連携し、LINEで予定の追加・確認・空き時間の提案まで。調整のやりとりに追われる時間を、もっとクリエイティブに使えるように。',
                'url': 'https://lp-production-9e2c.up.railway.app/schedule',
                'line_url': 'https://line.me/R/ti/p/@ai_schedule_secretary'
            },
            'AI経理秘書': {
                'price': 1500,
                "description": '打合せ後すぐ送れる、スマートな請求書作成アシスタント',
                'usage': 'LINEで項目を送るだけで、見積書や請求書を即作成。営業から事務処理までを一気通貫でスムーズに。',
                'url': 'https://lp-production-9e2c.up.railway.app/accounting',
                'line_url': 'https://line.me/R/ti/p/@ai_accounting_secretary'
            },
            'AIタスクコンシェルジュ': {
                'price': 1500,
                "description": '今日やるべきことを、ベストなタイミングで',
                'usage': '登録したタスクを空き時間に自動で配置し、理想的な1日をAIが提案。「やりたいのにできない」を、「自然にこなせる」毎日に。',
                'url': 'https://lp-production-9e2c.up.railway.app/task',
                'line_url': 'https://line.me/R/ti/p/@ai_task_concierge'
            }
        }
        
        if content_type not in content_info:
            print(f'[ERROR] 無効なコンテンツタイプ: {content_type}')
            return {'success': False, 'error': f'無効なコンテンツタイプ: {content_type}'}
        
        content = content_info[content_type]
        
        # 既に追加されているコンテンツを確認
        c.execute(f'SELECT COUNT(*) FROM usage_logs WHERE user_id = {placeholder} AND content_type = {placeholder}', (user_id_db, content_type))
        existing_count = c.fetchone()[0]
        
        if existing_count > 0:
            print(f'[DEBUG] 既に追加済みのコンテンツ: {content_type}')
            return {'success': False, 'error': f'コンテンツ {content_type} は既に追加されています'}
        
        # サブスクリプション状態に基づく処理
        is_trial_period = subscription_status.get('subscription', {}).get('status') == 'trialing'
        is_free = is_trial_period or is_first_content  # トライアル期間中または初回コンテンツは無料
        
        if is_free:
            print(f'[DEBUG] トライアル期間中または初回コンテンツのため無料で追加')
            # トライアル期間中または初回コンテンツは無料で追加
            c.execute(f'INSERT INTO usage_logs (user_id, content_type, price, status, created_at) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, NOW())', 
                     (user_id_db, content_type, 0, 'active'))
        else:
            print(f'[DEBUG] 有料コンテンツ追加')
            # 有料コンテンツの場合はStripe処理を実行
            c.execute(f'INSERT INTO usage_logs (user_id, content_type, price, status, created_at) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, NOW())', 
                     (user_id_db, content_type, content['price'], 'active'))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'content_type': content_type,
            'price': content['price'],
            'description': content['description'],
            'usage': content['usage'],
            'url': content['url']
        }
        
    except Exception as e:
        print(f'[ERROR] コンテンツ確認処理エラー: {e}')
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def handle_status_check(reply_token, user_id_db):
    """利用状況確認"""
    try:
        # データベースタイプを取得
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 使用量ログを取得
        c.execute(f'''
            SELECT content_type, price, created_at 
            FROM usage_logs 
            WHERE user_id = {placeholder} 
            ORDER BY created_at DESC
        ''', (user_id_db,))
        
        usage_logs = c.fetchall()
        
        if not usage_logs:
            status_message = "現在追加されているコンテンツはありません。\n\n「追加」と入力してコンテンツを追加してください。"
        else:
            status_message = "現在の利用状況：\n\n"
            total_price = 0
            
            for log in usage_logs:
                content_type, price, created_at = log
                total_price += price if price else 0
                created_date = created_at.strftime('%Y年%m月%d日') if created_at else '不明'
                status_message += f"• {content_type}（{created_date}追加）\n"
            
            status_message += f"\n合計料金：{total_price:,}円/月"
        
        conn.close()
        
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
        print(f'[DEBUG] handle_add_content_company開始: company_id={company_id}, stripe_subscription_id={stripe_subscription_id}')
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
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        # 企業のサブスクリプション数を確認
        c.execute(f'SELECT COUNT(*) FROM company_subscriptions WHERE company_id = {placeholder} AND subscription_status = {placeholder}', (company_id, 'active'))
        total_subscription_count = c.fetchone()[0]
        
        # 企業のLINEアカウント数を確認
        c.execute(f'SELECT COUNT(*) FROM company_line_accounts WHERE company_id = {placeholder} AND status = {placeholder}', (company_id, 'active'))
        total_line_account_count = c.fetchone()[0]
        
        conn.close()
        
        print(f'[DEBUG] 企業コンテンツ追加: company_id={company_id}, total_subscription_count={total_subscription_count}, total_line_account_count={total_line_account_count}')
        
        # コンテンツ選択メニューを作成
        actions = []
        for i, content in enumerate(available_contents, 1):
            actions.append({
                "type": "message",
                "label": f"{i}. {content['name']}",
                "text": f"{i}"
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
        
        print(f'[DEBUG] メッセージ送信開始: reply_token={reply_token[:20]}...')
        send_line_message(reply_token, [message])
        print(f'[DEBUG] メッセージ送信完了')
        
    except Exception as e:
        print(f'[DEBUG] 企業コンテンツ追加エラー: {e}')
        import traceback
        traceback.print_exc()
        send_line_message(reply_token, [{"type": "text", "text": "コンテンツ追加処理でエラーが発生しました。"}])

def handle_status_check_company(reply_token, company_id):
    """企業ユーザー専用：利用状況確認"""
    try:
        # データベースタイプを取得
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 企業情報を取得
        c.execute(f'SELECT company_name FROM companies WHERE id = {placeholder}', (company_id,))
        company = c.fetchone()
        
        if not company:
            send_line_message(reply_token, [{"type": "text", "text": "企業情報が見つかりません。"}])
            conn.close()
            return
        
        company_name = company[0]
        
        # 企業のコンテンツ一覧を取得
        c.execute(f'''
            SELECT content_type, total_price, created_at 
            FROM company_subscriptions 
            WHERE company_id = {placeholder} AND subscription_status = 'active'
            ORDER BY created_at DESC
        ''', (company_id,))
        
        active_contents = c.fetchall()
        conn.close()
        
        # メッセージを構築
        status_message = f"📊 利用状況\n\n"
        status_message += f"🏢 企業名: {company_name}\n\n"
        
        if active_contents:
            status_message += "📋 利用コンテンツ:\n"
            total_price = 0
            
            for content in active_contents:
                content_type, total_price_content, created_at = content
                total_price += total_price_content if total_price_content else 0
                created_date = created_at.strftime('%Y年%m月%d日') if created_at else '不明'
                status_message += f"• {content_type}（{created_date}追加）\n"
            
            status_message += f"\n合計料金：{total_price:,}円/月"
        else:
            status_message += "📋 利用コンテンツ: まだ利用していません\n"
        
        status_message += "\n💡 何かお手伝いできることはありますか？\n"
        status_message += "📱 「メニュー」と入力すると、メインメニューに戻れます。\n"
        status_message += "❓ 使い方がわからない場合は「ヘルプ」と入力してください。"
        
        send_line_message(reply_token, [{"type": "text", "text": status_message}])
        
    except Exception as e:
        print(f'[ERROR] 企業利用状況確認エラー: {e}')
        import traceback
        traceback.print_exc()
        send_line_message(reply_token, [{"type": "text", "text": "❌ エラーが発生しました。しばらく時間をおいて再度お試しください。"}])

def handle_cancel_menu_company(reply_token, company_id, stripe_subscription_id):
    """企業ユーザー専用：解約メニュー表示"""
    try:
        print(f'[DEBUG] handle_cancel_menu_company開始: company_id={company_id}, stripe_subscription_id={stripe_subscription_id}')
        message = {
            "type": "template",
            "altText": "解約メニュー",
            "template": {
                "type": "buttons",
                "title": "解約メニュー",
                "text": "どの解約を行いますか？",
                "actions": [
                    {
                        "type": "message",
                        "label": "サブスクリプション解約",
                        "text": "サブスクリプション解約"
                    },
                    {
                        "type": "message",
                        "label": "コンテンツ解約",
                        "text": "コンテンツ解約"
                    },
                    {
                        "type": "message",
                        "label": "戻る",
                        "text": "メニュー"
                    }
                ]
            }
        }
        
        print(f'[DEBUG] 解約メニューメッセージ送信開始: reply_token={reply_token[:20]}...')
        send_line_message(reply_token, [message])
        print(f'[DEBUG] 解約メニューメッセージ送信完了')
        
    except Exception as e:
        print(f'[DEBUG] 解約メニューエラー: {e}')
        import traceback
        traceback.print_exc()
        send_line_message(reply_token, [{"type": "text", "text": "解約メニューでエラーが発生しました。"}])

def handle_cancel_request_company(reply_token, company_id, stripe_subscription_id):
    """企業ユーザー専用：個別コンテンツ解約メニュー表示"""
    try:
        # データベースタイプを取得
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # アクティブなコンテンツを取得
        c.execute(f'''
            SELECT id, content_type, created_at 
            FROM company_subscriptions 
            WHERE company_id = {placeholder} AND subscription_status = 'active'
            ORDER BY created_at DESC
        ''', (company_id,))
        
        active_contents = c.fetchall()
        print(f'[DEBUG] 企業解約対象コンテンツ取得: company_id={company_id}, count={len(active_contents)}')
        
        if not active_contents:
            send_line_message(reply_token, [{"type": "text", "text": "解約可能なコンテンツが見つかりませんでした。"}])
            return
        
        # コンテンツ選択メッセージを作成
        actions = []
        for i, (subscription_id, content_type, created_at) in enumerate(active_contents, 1):
            # ai_scheduleをAI予定秘書に変換
            display_name = 'AI予定秘書' if content_type == 'ai_schedule' else content_type
            print(f'[DEBUG] コンテンツ: ({content_type}, {created_at})')
            
            actions.append({
                "type": "message",
                "label": f"{i}. {display_name}",
                "text": str(i)
            })
        
        actions.append({
            "type": "message",
            "label": "戻る",
            "text": "メニュー"
        })
        
        message = {
            "type": "template",
            "altText": "コンテンツ解約選択",
            "template": {
                "type": "buttons",
                "title": "解約するコンテンツを選択",
                "text": "解約したいコンテンツを選択してください：",
                "actions": actions
            }
        }
        
        send_line_message(reply_token, [message])
        print(f'[DEBUG] コンテンツ解約コマンド処理完了')
        
    except Exception as e:
        print(f'[DEBUG] コンテンツ解約メニューエラー: {e}')
        import traceback
        traceback.print_exc()
        send_line_message(reply_token, [{"type": "text", "text": "コンテンツ解約メニューでエラーが発生しました。"}])

def handle_cancel_selection_company(reply_token, company_id, stripe_subscription_id, selection_text):
    """企業ユーザー専用：解約選択処理"""
    try:
        # データベースタイプを取得
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 企業のアクティブなコンテンツを取得
        c.execute(f'''
            SELECT id, content_type, created_at 
            FROM company_subscriptions 
            WHERE company_id = {placeholder} AND subscription_status = 'active'
            ORDER BY created_at DESC
        ''', (company_id,))
        
        active_contents = c.fetchall()
        
        # 選択された番号を解析
        numbers = smart_number_extraction(selection_text)
        valid_numbers, invalid_reasons, duplicates = validate_selection_numbers(numbers, len(active_contents))
        selected_indices = valid_numbers
        
        print(f'[DEBUG] 選択テキスト: {selection_text}')
        print(f'[DEBUG] 抽出された数字: {numbers}')
        print(f'[DEBUG] 有効な選択インデックス: {selected_indices}')
        print(f'[DEBUG] 最大選択可能数: {len(active_contents)}')
        
        if invalid_reasons:
            print(f'[DEBUG] 無効な入力: {invalid_reasons}')
        if duplicates:
            print(f'[DEBUG] 重複除去: {duplicates}')
        
        cancelled = []
        
        # 選択されたコンテンツを解約
        for i, (subscription_id, content_type, created_at) in enumerate(active_contents, 1):
            if i in selected_indices:
                print(f'[DEBUG] 解約処理開始: content_type={content_type}, subscription_id={subscription_id}')
                
                # Stripe UsageRecordを削除（有料コンテンツの場合）
                try:
                    # 企業のStripeサブスクリプションIDを取得
                    c.execute(f'SELECT stripe_subscription_id FROM company_subscriptions WHERE company_id = {placeholder} AND subscription_status = {placeholder} LIMIT 1', (company_id, 'active'))
                    stripe_result = c.fetchone()
                    print(f'[DEBUG] StripeサブスクリプションID取得結果: {stripe_result}')
                    
                    if stripe_result and stripe_result[0]:
                        stripe_subscription_id = stripe_result[0]
                        
                        # Stripeからsubscription_item_id取得
                        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
                        USAGE_PRICE_ID = os.getenv('STRIPE_USAGE_PRICE_ID')
                        print(f'[DEBUG] Stripeサブスクリプション取得: {stripe_subscription_id}, USAGE_PRICE_ID={USAGE_PRICE_ID}')
                        
                        usage_item = None
                        for item in subscription['items']['data']:
                            if item['price']['id'] == USAGE_PRICE_ID:
                                usage_item = item
                                break
                        
                        if usage_item:
                            # UsageRecordを削除（quantity=1で減算）
                            import time
                            stripe.UsageRecord.create(
                                subscription_item=usage_item['id'],
                                quantity=1,
                                timestamp=int(time.time()),
                                action='decrement',  # 使用量を減算
                            )
                            print(f'[DEBUG] Stripe UsageRecord削除成功: content_type={content_type}')
                        else:
                            print(f'[DEBUG] UsageItemが見つかりません: USAGE_PRICE_ID={USAGE_PRICE_ID}')
                except Exception as e:
                    print(f'[DEBUG] Stripe UsageRecord削除エラー: {e}')
                    import traceback
                    traceback.print_exc()
                    # エラーが発生しても処理は続行
                
                # データベース更新処理
                try:
                    # サブスクリプションを停止
                    c.execute(f'''
                        UPDATE company_subscriptions 
                        SET subscription_status = 'canceled'
                        WHERE id = {placeholder}
                    ''', (subscription_id,))
                    print(f'[DEBUG] company_subscriptions更新成功: subscription_id={subscription_id}')
                    
                    # LINEアカウントも停止
                    c.execute(f'''
                        UPDATE company_line_accounts 
                        SET status = 'inactive'
                        WHERE company_id = {placeholder} AND content_type = {placeholder}
                    ''', (company_id, content_type))
                    print(f'[DEBUG] company_line_accounts更新成功: company_id={company_id}, content_type={content_type}')
                    
                    # トランザクションをコミット
                    conn.commit()
                    print(f'[DEBUG] データベーストランザクションコミット成功')
                    
                    cancelled.append(content_type)
                    print(f'[DEBUG] 企業コンテンツ解約処理完了: content_type={content_type}, subscription_id={subscription_id}')
                    
                except Exception as e:
                    print(f'[DEBUG] データベース更新エラー: {e}')
                    import traceback
                    traceback.print_exc()
                    
                    # トランザクションをロールバック
                    try:
                        conn.rollback()
                        print(f'[DEBUG] データベーストランザクションロールバック成功')
                    except Exception as rollback_error:
                        print(f'[DEBUG] ロールバックエラー: {rollback_error}')
                    
                    # エラーが発生した場合は処理をスキップ
                    continue
        
        print(f'[DEBUG] 解約対象コンテンツ数: {len(cancelled)}')
        print(f'[DEBUG] 解約対象: {cancelled}')
        
        if cancelled:
            # 解約完了メッセージを送信
            cancelled_text = '\n'.join([f'• {content}' for content in cancelled])
            success_message = f'以下のコンテンツの解約を受け付けました：\n\n{cancelled_text}'
            send_line_message(reply_token, [{"type": "text", "text": success_message}])
        else:
            # 解約対象がない場合
            send_line_message(reply_token, [{"type": "text", "text": "解約対象のコンテンツが見つかりませんでした。"}])
    
    except Exception as e:
        print(f'[ERROR] 企業解約選択処理エラー: {e}')
        import traceback
        traceback.print_exc()
        send_line_message(reply_token, [{"type": "text", "text": "❌ 解約処理に失敗しました。しばらく時間をおいて再度お試しください。"}])
    finally:
        # データベース接続を確実にクローズ
        if 'c' in locals():
            c.close()
        if 'conn' in locals():
            conn.close()

def handle_subscription_cancel_company(reply_token, company_id, stripe_subscription_id):
    """企業ユーザー専用：サブスクリプション全体の解約処理"""
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
                
                # データベースも更新
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('''
                    UPDATE company_subscriptions 
                    SET subscription_status = 'canceled'
                    WHERE company_id = %s
                ''', (company_id,))
                c.execute('''
                    UPDATE company_line_accounts 
                    SET status = 'inactive'
                    WHERE company_id = %s
                ''', (company_id,))
                conn.commit()
                conn.close()
                
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
        print(f'[ERROR] 企業サブスクリプション解約処理エラー: {e}')
        import traceback
        traceback.print_exc()
        send_line_message(reply_token, [{"type": "text", "text": "❌ エラーが発生しました。しばらく時間をおいて再度お試しください。"}])

def get_welcome_message():
    return "ようこそ！LINE連携が完了しました。"

def get_not_registered_message():
    return "ご登録情報が見つかりません。LPからご登録ください。"

def handle_content_confirmation_company(company_id, content_type):
    """企業ユーザー専用：コンテンツ追加確認処理"""
    try:
        print(f'[DEBUG] 企業コンテンツ確認処理開始: company_id={company_id}, content_type={content_type}')
        
        # データベースタイプを取得
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 既存のコンテンツをチェック
        c.execute(f'''
            SELECT id, content_type, subscription_status 
            FROM company_subscriptions 
            WHERE company_id = {placeholder} AND content_type = {placeholder}
        ''', (company_id, content_type))
        
        existing_content = c.fetchone()
        if existing_content:
            subscription_id, existing_content_type, status = existing_content
            print(f'[DEBUG] 既存コンテンツ発見: subscription_id={subscription_id}, content_type={existing_content_type}, status={status}')
            
            if status == 'active':
                return {
                    'success': False, 
                    'error': f'✅ {content_type}は既に追加済みです。\n\n📱 他のコンテンツを追加する場合は、再度「追加」を選択してください。\n\n💡 現在の利用状況を確認する場合は「状態」を選択してください。'
                }
            elif status == 'canceled':
                # キャンセル済みの場合は再アクティブ化
                c.execute(f'''
                    UPDATE company_subscriptions 
                    SET subscription_status = 'active', updated_at = CURRENT_TIMESTAMP
                    WHERE id = {placeholder}
                ''', (subscription_id,))
                conn.commit()
                print(f'[DEBUG] キャンセル済みコンテンツを再アクティブ化: subscription_id={subscription_id}')
                
                return {
                    'success': True,
                    'company_id': company_id,
                    'content_type': content_type,
                    'description': f'{content_type}を再アクティブ化しました',
                    'url': 'https://lp-production-9e2c.up.railway.app',
                    'usage': 'LINEアカウントからご利用いただけます',
                    'is_free': False
                }
        
        # コンテンツ情報を取得
        content_info = {
            'AI予定秘書': {
                'description': 'AIが予定管理をサポート',
                'url': 'https://ai-schedule.example.com',
                'usage': '予定を入力すると、AIが最適なスケジュールを提案します'
            },
            'AI経理秘書': {
                'description': 'AIが経理業務をサポート',
                'url': 'https://ai-accounting.example.com',
                'usage': '経理データを入力すると、AIが自動で仕訳を提案します'
            },
            'AIタスクコンシェルジュ': {
                'description': 'AIがタスク管理をサポート',
                'url': 'https://ai-task.example.com',
                'usage': 'タスクを入力すると、AIが優先順位を提案します'
            }
        }
        
        # 既存のコンテンツ数を取得
        c.execute(f'''
            SELECT COUNT(*) 
            FROM company_subscriptions 
            WHERE company_id = {placeholder} AND subscription_status = 'active'
        ''', (company_id,))
        
        existing_count = c.fetchone()[0]
        print(f'[DEBUG] 既存コンテンツ数: {existing_count}')
        
        # 料金計算
        base_price = 3900  # 基本料金
        additional_price_per_content = 1500  # 追加コンテンツ料金
        
        # 新しく追加するコンテンツの料金を計算
        # 既に追加済みのコンテンツがある場合は、追加料金のみ
        if existing_count == 0:
            # 初回コンテンツ（無料）
            total_price = 0
            is_first_content = True
        else:
            # 追加コンテンツ（1,500円/個）
            total_price = additional_price_per_content  # 新しく追加するコンテンツ1個分のみ
            is_first_content = False
        
        # 企業のStripeサブスクリプションIDを取得
        c.execute(f'''
            SELECT stripe_subscription_id 
            FROM company_subscriptions 
            WHERE company_id = {placeholder} AND subscription_status = 'active' 
            LIMIT 1
        ''', (company_id,))
        
        stripe_result = c.fetchone()
        if not stripe_result:
            return {'success': False, 'error': 'Stripeサブスクリプションが見つかりません'}
        
        stripe_subscription_id = stripe_result[0]
        print(f'[DEBUG] StripeサブスクリプションID: {stripe_subscription_id}')
        
        # サブスクリプション状態をチェック
        subscription_status = check_subscription_status(stripe_subscription_id)
        is_trial_period = subscription_status.get('subscription', {}).get('status') == 'trialing'
        
        is_free = is_trial_period or is_first_content  # トライアル期間中または初回コンテンツは無料
        
        # Stripe UsageRecord作成（有料の場合のみ）
        usage_record = None
        if not is_free:
            try:
                # Stripeサブスクリプションを取得
                subscription = stripe.Subscription.retrieve(stripe_subscription_id)
                USAGE_PRICE_ID = os.getenv('STRIPE_USAGE_PRICE_ID')
                print(f'[DEBUG] Stripeサブスクリプション取得: {stripe_subscription_id}, USAGE_PRICE_ID={USAGE_PRICE_ID}')
                
                # 従量課金アイテムを検索
                usage_item = None
                for item in subscription['items']['data']:
                    print(f"アイテム確認: price_id={item['price']['id']}, usage_price_id={USAGE_PRICE_ID}")
                    if item['price']['id'] == USAGE_PRICE_ID:
                        usage_item = item
                        print(f"従量課金アイテム発見: {item}")
                        break
                
                if not usage_item:
                    print(f"従量課金アイテムが見つかりません: usage_price_id={USAGE_PRICE_ID}")
                    print(f"利用可能なアイテム: {[item['price']['id'] for item in subscription['items']['data']]}")
                    
                    # 従量課金アイテムを自動追加
                    try:
                        print(f"従量課金アイテムを自動追加中...")
                        usage_item = stripe.SubscriptionItem.create(
                            subscription=stripe_subscription_id,
                            price=USAGE_PRICE_ID
                        )
                        print(f"従量課金アイテム追加成功: {usage_item.id}")
                    except Exception as add_error:
                        print(f"従量課金アイテム追加エラー: {add_error}")
                        return {'success': False, 'error': f'従量課金アイテムの追加に失敗しました: {str(add_error)}'}
                
                subscription_item_id = usage_item['id']
                print(f"従量課金アイテムID: {subscription_item_id}")
                
                # Usage Record作成
                try:
                    # 月額サブスクリプションの請求期間を取得
                    subscription = stripe.Subscription.retrieve(stripe_subscription_id)
                    current_period_start = subscription.current_period_start
                    
                    usage_record = stripe.UsageRecord.create(
                        subscription_item=subscription_item_id,
                        quantity=1,
                        timestamp=current_period_start,  # 月額サブスクリプションの請求期間開始時に合わせる
                        action='increment',
                    )
                    print(f"Usage Record作成成功: {usage_record.id}")
                except Exception as usage_error:
                    print(f"Usage Record作成エラー: {usage_error}")
                    return {'success': False, 'error': f'使用量記録の作成に失敗しました: {str(usage_error)}'}
            
            except Exception as e:
                print(f'[DEBUG] Stripe処理エラー: {e}')
                return {'success': False, 'error': f'Stripe処理に失敗しました: {str(e)}'}
        
        # 新しいサブスクリプションを作成
        if db_type == 'postgresql':
            # PostgreSQL用の日付計算
            c.execute(f'''
                INSERT INTO company_subscriptions 
                (company_id, content_type, subscription_status, base_price, additional_price, total_price, current_period_end) 
                VALUES ({placeholder}, {placeholder}, 'active', {placeholder}, {placeholder}, {placeholder}, NOW() + INTERVAL '1 month')
            ''', (company_id, content_type, base_price, additional_price_per_content, total_price))
        else:
            # SQLite用の日付計算
            c.execute(f'''
                INSERT INTO company_subscriptions 
                (company_id, content_type, subscription_status, base_price, additional_price, total_price, current_period_end) 
                VALUES ({placeholder}, {placeholder}, 'active', {placeholder}, {placeholder}, {placeholder}, DATE_ADD(NOW(), INTERVAL 1 MONTH))
            ''', (company_id, content_type, base_price, additional_price_per_content, total_price))
        
        conn.commit()
        conn.close()
        
        # コンテンツ情報を取得
        content_info = {
            'AI予定秘書': {
                'description': 'AIが予定管理をサポート',
                'url': 'https://ai-schedule.example.com',
                'usage': '予定を入力すると、AIが最適なスケジュールを提案します'
            },
            'AI経理秘書': {
                'description': 'AIが経理業務をサポート',
                'url': 'https://ai-accounting.example.com',
                'usage': '経理データを入力すると、AIが自動で仕訳を提案します'
            },
            'AIタスクコンシェルジュ': {
                'description': 'AIがタスク管理をサポート',
                'url': 'https://ai-task.example.com',
                'usage': 'タスクを入力すると、AIが優先順位を提案します'
            }
        }
        
        # 選択されたコンテンツの情報を取得
        selected_content = content_info.get(content_type, {})
        
        return {
            'success': True,
            'company_id': company_id,
            'content_type': content_type,
            'total_price': total_price,
            'description': selected_content.get('description', f'{content_type}の説明'),
            'url': selected_content.get('url', 'https://lp-production-9e2c.up.railway.app'),
            'usage': selected_content.get('usage', 'LINEアカウントからご利用いただけます'),
            'is_free': is_free,
            'usage_record_id': usage_record.id if usage_record else None
        }
        
    except Exception as e:
        print(f'[ERROR] 企業コンテンツ確認処理エラー: {e}')
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}
    finally:
        if c:
            c.close()
        if conn:
            conn.close()

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

def send_company_welcome_message(line_user_id, company_name, email):
    """企業向けのLINE案内メッセージを送信"""
    try:
        print(f'[DEBUG] 企業向け案内メッセージ送信開始: line_user_id={line_user_id}, company_name={company_name}')
        
        # 企業向けの案内メッセージを作成
        welcome_message = {
            "type": "template",
            "altText": "AIコレクションズ 企業向けサービスへようこそ",
            "template": {
                "type": "buttons",
                "title": f"🎉 {company_name}様、ようこそ！",
                "text": f"AIコレクションズの企業向けサービスにご登録いただき、ありがとうございます。\n\n📧 登録メール: {email}\n💰 月額料金: ¥3,900\n\n以下のメニューから操作してください：",
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
                        "label": "ヘルプ",
                        "text": "ヘルプ"
                    }
                ]
            }
        }
        
        print(f'[DEBUG] 案内メッセージ作成完了: {welcome_message}')
        
        # プッシュメッセージとして送信
        success = send_line_message_push(line_user_id, [welcome_message])
        
        if success:
            print(f'[DEBUG] 企業向け案内メッセージ送信成功: line_user_id={line_user_id}')
            return True
        else:
            print(f'[DEBUG] 企業向け案内メッセージ送信失敗: line_user_id={line_user_id}')
            return False
            
    except Exception as e:
        print(f'[DEBUG] 企業向け案内メッセージ送信エラー: {e}')
        import traceback
        traceback.print_exc()
        return False

def send_line_message_push(user_id, messages):
    """プッシュメッセージとしてLINEメッセージを送信"""
    try:
        LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
        print(f'[DEBUG] LINE_CHANNEL_ACCESS_TOKEN確認: {LINE_CHANNEL_ACCESS_TOKEN[:20]}...')
        
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        print(f'[DEBUG] ヘッダー設定完了: Authorization=Bearer {LINE_CHANNEL_ACCESS_TOKEN[:20]}...')
        
        data = {
            'to': user_id,
            'messages': messages
        }
        
        print(f'[DEBUG] メッセージ数: {len(messages)}')
        print(f'[DEBUG] LINE送信内容: {data}')
        
        response = requests.post(
            'https://api.line.me/v2/bot/message/push',
            headers=headers,
            json=data
        )
        
        print(f'[DEBUG] LINE API送信開始')
        print(f'[DEBUG] LINE APIリクエスト送信: URL=https://api.line.me/v2/bot/message/push')
        print(f'[DEBUG] LINE APIレスポンス受信: status_code={response.status_code}')
        
        if response.status_code == 200:
            print(f'[DEBUG] LINE API送信成功: status_code={response.status_code}')
            print(f'[DEBUG] LINE API送信処理完了')
            return True
        else:
            print(f'[DEBUG] LINE API送信失敗: status_code={response.status_code}, response={response.text}')
            return False
            
    except Exception as e:
        print(f'[DEBUG] LINE送信エラー: {e}')
        return False