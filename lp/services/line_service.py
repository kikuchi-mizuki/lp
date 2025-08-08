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
        
        if response.status_code == 200:
            print('[DEBUG] LINE送信成功')
            return True
        else:
            print(f'[ERROR] LINE送信失敗: status_code={response.status_code}, response={response.text}')
            return False
            
    except requests.exceptions.Timeout:
        print('[ERROR] LINE API送信タイムアウト')
        # エラーログに記録
        with open('error.log', 'a', encoding='utf-8') as f:
            f.write(f'{datetime.now().isoformat()} - LINE API送信タイムアウト\n')
        return False
    except requests.exceptions.RequestException as e:
        print(f'[ERROR] LINE API送信エラー: {e}')
        # エラーログに記録
        with open('error.log', 'a', encoding='utf-8') as f:
            f.write(f'{datetime.now().isoformat()} - LINE API送信エラー: {str(e)}\n')
        return False
    except Exception as e:
        print(f'[ERROR] LINE送信予期しないエラー: {e}')
        # エラーログに記録
        with open('error.log', 'a', encoding='utf-8') as f:
            f.write(f'{datetime.now().isoformat()} - LINE送信予期しないエラー: {str(e)}\n')
            f.write(traceback.format_exc() + '\n')
        return False

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
    """企業ユーザー専用：利用状況確認（company_line_accountsベース）"""
    try:
        print(f'[DEBUG] 企業利用状況確認開始: company_id={company_id}')
        
        conn = get_db_connection()
        c = conn.cursor()
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        # 企業名を取得
        c.execute(f'SELECT company_name FROM companies WHERE id = {placeholder}', (company_id,))
        company_result = c.fetchone()
        if not company_result:
            send_line_message(reply_token, [{"type": "text", "text": "❌ 企業情報が見つかりません"}])
            return
        company_name = company_result[0]
        
        # 月額基本サブスクリプション情報を取得
        c.execute(f'''
            SELECT subscription_status, monthly_base_price, current_period_end
            FROM company_monthly_subscriptions 
            WHERE company_id = {placeholder}
        ''', (company_id,))
        
        monthly_subscription = c.fetchone()
        
        # 実際のLINEアカウント利用状況を取得
        c.execute(f'''
            SELECT content_type, status, created_at
            FROM company_line_accounts 
            WHERE company_id = {placeholder} AND status = 'active'
            ORDER BY created_at DESC
        ''', (company_id,))
        
        line_accounts = c.fetchall()
        conn.close()
        
        # メッセージを構築
        status_message = f"📊 利用状況\n\n"
        status_message += f"🏢 企業名: {company_name}\n\n"
        
        # 月額基本サブスクリプション情報
        if monthly_subscription:
            subscription_status, monthly_base_price, current_period_end = monthly_subscription
            status_message += f"💳 月額基本料金: {monthly_base_price:,}円/月\n"
            status_message += f"📅 ステータス: {'アクティブ' if subscription_status == 'active' else '非アクティブ'}\n"
            
            if current_period_end:
                period_end = current_period_end.strftime('%Y年%m月%d日')
                status_message += f"📅 次回更新日: {period_end}\n"
            
            status_message += "\n"
        else:
            status_message += "❌ 月額基本サブスクリプションが見つかりません\n\n"
        
        # アクティブなLINEアカウント利用状況のみ表示
        if line_accounts:
            status_message += "📋 利用コンテンツ:\n"
            
            active_content_count = 0
            for account in line_accounts:
                content_type, status, created_at = account
                created_date = created_at.strftime('%Y年%m月%d日') if created_at else '不明'
                
                # アクティブなコンテンツの順番を管理
                if status == "active":
                    active_content_count += 1
                    if active_content_count == 1:
                        price_text = "（無料）"  # 1個目は無料
                    else:
                        price_text = "（+1,500円/月）"  # 2個目以降は有料
                else:
                    price_text = "（停止中）"
                
                status_message += f"• {content_type}{price_text}（{created_date}追加）\n"
        else:
            status_message += "📋 利用コンテンツ: まだ追加していません\n"
        
        # 合計料金計算
        if monthly_subscription:
            monthly_base_price = monthly_subscription[1]
            total_additional_price = 0
            
            # アクティブなコンテンツの追加料金を計算（1個目は無料、2個目以降は有料）
            active_count = 0
            for account in line_accounts:
                if account[1] == "active":  # statusがactive
                    active_count += 1
                    if active_count > 1:  # 2個目以降のみ課金
                        total_additional_price += 1500
            
            total_monthly_price = monthly_base_price + total_additional_price
            status_message += f"\n💰 合計料金: {total_monthly_price:,}円/月"
            status_message += f"\n  └ 基本料金: {monthly_base_price:,}円"
            status_message += f"\n  └ 追加料金: {total_additional_price:,}円"
        else:
            status_message += f"\n💰 合計料金: 0円/月（サブスクリプションなし）"
        
        status_message += "\n\n💡 何かお手伝いできることはありますか？\n"
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
        
        # アクティブなコンテンツ（企業の有効なLINEアカウント＝追加済みコンテンツ）を取得
        c.execute(f'''
            SELECT id, content_type, created_at
            FROM company_line_accounts
            WHERE company_id = {placeholder} AND status = 'active'
            ORDER BY created_at DESC
        ''', (company_id,))

        active_contents = c.fetchall()
        print(f'[DEBUG] 企業解約対象コンテンツ取得: company_id={company_id}, count={len(active_contents)}')
        
        if not active_contents:
            send_line_message(reply_token, [{"type": "text", "text": "解約可能なコンテンツが見つかりませんでした。"}])
            conn.close()
            return
        
        # コンテンツ選択メッセージを作成
        actions = []
        for i, (account_id, content_type, created_at) in enumerate(active_contents, 1):
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
    finally:
        if conn:
            conn.close()

def handle_cancel_selection_company(reply_token, company_id, stripe_subscription_id, selection_text):
    """企業ユーザー専用：解約選択処理（確認ステップ追加）"""
    conn = None
    try:
        print(f'[DEBUG] === handle_cancel_selection_company 開始 ===')
        print(f'[DEBUG] 企業解約選択処理開始: company_id={company_id}, selection_text={selection_text}')
        print(f'[DEBUG] reply_token={reply_token[:20] if reply_token else "None"}..., stripe_subscription_id={stripe_subscription_id}')
        
        # データベースタイプを取得
        print(f'[DEBUG] データベースタイプ取得開始')
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        print(f'[DEBUG] データベースタイプ: {db_type}, placeholder: {placeholder}')
        
        print(f'[DEBUG] データベース接続開始')
        conn = get_db_connection()
        c = conn.cursor()
        print(f'[DEBUG] データベース接続成功')
        
        # 企業のアクティブなLINEアカウントを取得
        print(f'[DEBUG] SQLクエリ実行開始: company_id={company_id}')
        c.execute(f'''
            SELECT id, content_type, created_at 
            FROM company_line_accounts 
            WHERE company_id = {placeholder} AND status = 'active'
            ORDER BY created_at DESC
        ''', (company_id,))
        
        print(f'[DEBUG] SQLクエリ実行完了、結果取得開始')
        active_accounts = c.fetchall()
        print(f'[DEBUG] アクティブアカウント取得結果: {active_accounts}')
        
        # 選択された番号を解析
        numbers = smart_number_extraction(selection_text)
        valid_numbers, invalid_reasons, duplicates = validate_selection_numbers(numbers, len(active_accounts))
        selected_indices = valid_numbers
        
        print(f'[DEBUG] 選択テキスト: {selection_text}')
        print(f'[DEBUG] 抽出された数字: {numbers}')
        print(f'[DEBUG] 有効な選択インデックス: {selected_indices}')
        print(f'[DEBUG] 最大選択可能数: {len(active_accounts)}')
        print(f'[DEBUG] アクティブアカウント詳細:')
        for i, account in enumerate(active_accounts, 1):
            print(f'[DEBUG]   {i}. {account}')
        
        if invalid_reasons:
            print(f'[DEBUG] 無効な入力: {invalid_reasons}')
        if duplicates:
            print(f'[DEBUG] 重複除去: {duplicates}')
        
        # 選択されたコンテンツを特定
        selected_contents = []
        for i, (account_id, content_type, created_at) in enumerate(active_accounts, 1):
            if i in selected_indices:
                # ai_scheduleをAI予定秘書に変換
                display_name = 'AI予定秘書' if content_type == 'ai_schedule' else content_type
                # 1個目は無料、2個目以降は有料
                additional_price = 0 if i == 1 else 1500
                selected_contents.append({
                    'account_id': account_id,
                    'content_type': content_type,
                    'display_name': display_name,
                    'additional_price': additional_price
                })
        
        if not selected_contents:
            print(f'[DEBUG] selected_contents が空です')
            print(f'[DEBUG] 企業ID: {company_id}, 選択: {selection_text}')
            print(f'[DEBUG] アクティブアカウント: {len(active_accounts)}件')
            print(f'[DEBUG] 抽出数字: {numbers}, 有効選択: {selected_indices}')
            
            # 簡潔なエラーメッセージ
            error_message = f"❌ 解約対象が見つかりません\n\n企業ID: {company_id}\n選択: {selection_text}\nアクティブ: {len(active_accounts)}件\n\n「メニュー」でメイン画面に戻れます。"
            send_line_message(reply_token, [{"type": "text", "text": error_message}])
            return
        
        # 解約確認メッセージを作成
        content_list = '\n'.join([f'• {content["display_name"]}' for content in selected_contents])
        total_additional_price = sum(content['additional_price'] for content in selected_contents)
        
        if total_additional_price > 0:
            price_info = f"\n💰 削除される追加料金: {total_additional_price:,}円/月"
        else:
            price_info = "\n💰 追加料金なし（基本料金に含まれる）"
        
        # 請求期間情報を取得
        billing_period_info = ""
        if stripe_subscription_id:
            try:
                from services.billing_period_sync_service import BillingPeriodSyncService
                billing_sync_service = BillingPeriodSyncService()
                period_info = billing_sync_service.get_subscription_billing_period(stripe_subscription_id)
                
                if period_info:
                    from datetime import datetime
                    period_end = period_info['period_end']
                    billing_period_info = f"\n📅 次回請求日: {period_end.strftime('%Y年%m月%d日')}"
                    
            except Exception as e:
                print(f'[DEBUG] 請求期間情報取得エラー: {e}')
        
        # 簡潔な確認メッセージ
        confirmation_text = f"解約対象:\n{content_list}{price_info}\n\n解約しますか？"
        
        # 確認ボタンを作成（簡潔なテキスト）
        actions = [
            {
                "type": "message",
                "label": "解約する",
                "text": f"解約確認_{selected_indices[0]}" if selected_indices else "解約確認_1"
            },
            {
                "type": "message",
                "label": "キャンセル",
                "text": "メニュー"
            }
        ]
        
        message = {
            "type": "template",
            "altText": "解約確認",
            "template": {
                "type": "buttons",
                "title": "解約確認",
                "text": confirmation_text,
                "actions": actions
            }
        }
        
        print(f'[DEBUG] LINE API呼び出し開始: message={message}')
        result = send_line_message(reply_token, [message])
        print(f'[DEBUG] 解約確認メッセージ送信完了: result={result}')
        
    except Exception as e:
        print(f'[ERROR] 企業解約選択処理エラー: {e}')
        import traceback
        traceback.print_exc()
        send_line_message(reply_token, [{"type": "text", "text": "❌ 解約処理に失敗しました。しばらく時間をおいて再度お試しください。"}])
    finally:
        if conn:
            conn.close()

def handle_cancel_confirmation_company(reply_token, company_id, stripe_subscription_id, confirmation_text):
    """企業ユーザー専用：解約確認処理（実際の解約実行）"""
    try:
        print(f'[DEBUG] 企業解約確認処理開始: company_id={company_id}, confirmation_text={confirmation_text}')
        
        # 確認テキストから選択インデックスを抽出
        if not confirmation_text.startswith('解約確認_'):
            send_line_message(reply_token, [{"type": "text", "text": "❌ 無効な確認リクエストです。"}])
            return
        
        selected_indices_str = confirmation_text.replace('解約確認_', '')
        selected_indices = [int(idx) for idx in selected_indices_str.split(',')]
        
        print(f'[DEBUG] 解約対象インデックス: {selected_indices}')
        
        # データベースタイプを取得
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 企業のアクティブなLINEアカウントを取得
        c.execute(f'''
            SELECT id, content_type, created_at 
            FROM company_line_accounts 
            WHERE company_id = {placeholder} AND status = 'active'
            ORDER BY created_at DESC
        ''', (company_id,))
        
        active_accounts = c.fetchall()
        
        cancelled = []
        
        # 選択されたコンテンツを解約
        for i, (account_id, content_type, created_at) in enumerate(active_accounts, 1):
            if i in selected_indices:
                print(f'[DEBUG] 解約処理開始: content_type={content_type}, account_id={account_id}')
                
                # 追加料金が必要なコンテンツかチェック（1個目は無料、2個目以降は有料）
                additional_price = 0 if i == 1 else 1500
                
                # データベース更新処理
                try:
                    # LINEアカウントを非アクティブ化
                    c.execute(f'''
                        UPDATE company_line_accounts 
                        SET status = 'inactive'
                        WHERE id = {placeholder}
                    ''', (account_id,))
                    print(f'[DEBUG] company_line_accounts更新成功: account_id={account_id}')
                    
                    # トランザクションをコミット
                    conn.commit()
                    print(f'[DEBUG] データベーストランザクションコミット成功')
                    
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
                    continue  # エラーの場合は次のループへ
                
                # Stripeの請求項目を更新（有料コンテンツ解約の場合のみ）
                if additional_price > 0 and stripe_subscription_id:
                    try:
                        import stripe
                        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
                        
                        print(f'[DEBUG] 有料コンテンツ解約後のStripe更新: {content_type}, position={i}, price={additional_price}')
                        
                        # 解約後の現在のアクティブコンテンツ数を取得
                        c.execute(f'''
                            SELECT COUNT(*) 
                            FROM company_line_accounts 
                            WHERE company_id = {placeholder} AND status = 'active'
                        ''', (company_id,))
                        
                        remaining_total_count = c.fetchone()[0]
                        # 1個目は無料なので、課金対象は総数-1（ただし0未満にはならない）
                        new_billing_count = max(0, remaining_total_count - 1)
                        print(f'[DEBUG] 解約後: 残り総数={remaining_total_count}, 課金対象={new_billing_count}')
                        
                        # Stripeサブスクリプションを取得
                        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
                        
                        # 追加料金の請求項目を更新（複数の条件で検索）
                        updated = False
                        for item in subscription.items.data:
                            price_nickname = item.price.nickname or ""
                            price_id = item.price.id
                            
                            # 複数の条件で追加料金アイテムを特定
                            if (("追加" in price_nickname) or 
                                ("additional" in price_nickname.lower()) or
                                ("metered" in price_nickname.lower()) or
                                (price_id == 'price_1Rog1nIxg6C5hAVdnqB5MJiT')):
                                
                                print(f'[DEBUG] Stripe請求項目を更新: {item.id}, 数量: {item.quantity} → {new_billing_count}')
                                stripe.SubscriptionItem.modify(
                                    item.id,
                                    quantity=new_billing_count
                                )
                                print(f'[DEBUG] Stripe請求項目更新完了: {item.id}')
                                updated = True
                                break
                        
                        if not updated:
                            print(f'[WARN] 追加料金アイテムが見つかりませんでした。')
                                
                    except Exception as e:
                        print(f'[DEBUG] Stripe請求項目更新エラー: {e}')
                        import traceback
                        traceback.print_exc()
                        # Stripeエラーが発生しても処理を続行
                
                # 請求期間同期サービスを呼び出して使用量レコードを月額サブスクリプション期間に合わせる
                if stripe_subscription_id:
                    try:
                        from services.billing_period_sync_service import BillingPeriodSyncService
                        billing_sync_service = BillingPeriodSyncService()
                        sync_success = billing_sync_service.sync_usage_records_to_subscription_period(stripe_subscription_id)
                        
                        if sync_success:
                            print(f'[DEBUG] 解約時の請求期間同期完了: subscription_id={stripe_subscription_id}')
                        else:
                            print(f'[WARN] 解約時の請求期間同期に失敗: subscription_id={stripe_subscription_id}')
                            
                    except Exception as e:
                        print(f'[DEBUG] 解約時の請求期間同期エラー: {e}')
                        # 同期エラーが発生しても処理を続行
                
                # ai_scheduleをAI予定秘書に変換
                display_name = 'AI予定秘書' if content_type == 'ai_schedule' else content_type
                cancelled.append(display_name)
                print(f'[DEBUG] 企業コンテンツ解約処理完了: content_type={content_type}, account_id={account_id}')
        
        print(f'[DEBUG] 解約対象コンテンツ数: {len(cancelled)}')
        print(f'[DEBUG] 解約対象: {cancelled}')
        
        # 解約処理完了後、全体の請求期間同期を実行
        if cancelled and stripe_subscription_id:
            try:
                from services.billing_period_sync_service import BillingPeriodSyncService
                billing_sync_service = BillingPeriodSyncService()
                sync_success = billing_sync_service.sync_usage_records_to_subscription_period(stripe_subscription_id)
                
                if sync_success:
                    print(f'[DEBUG] 解約処理後の請求期間同期完了: subscription_id={stripe_subscription_id}')
                else:
                    print(f'[WARN] 解約処理後の請求期間同期に失敗: subscription_id={stripe_subscription_id}')
                    
            except Exception as e:
                print(f'[DEBUG] 解約処理後の請求期間同期エラー: {e}')
                # 同期エラーが発生しても処理を続行
        
        if cancelled:
            # 請求期間情報を取得
            billing_period_info = ""
            if stripe_subscription_id:
                try:
                    from services.billing_period_sync_service import BillingPeriodSyncService
                    billing_sync_service = BillingPeriodSyncService()
                    period_info = billing_sync_service.get_subscription_billing_period(stripe_subscription_id)
                    
                    if period_info:
                        from datetime import datetime
                        period_end = period_info['period_end']
                        billing_period_info = f"\n📅 次回請求日: {period_end.strftime('%Y年%m月%d日')}"
                        
                except Exception as e:
                    print(f'[DEBUG] 請求期間情報取得エラー: {e}')
                    # エラーが発生しても処理を続行
            
            # 解約完了メッセージを送信
            cancelled_text = '\n'.join([f'• {content}' for content in cancelled])
            success_message = f'✅ 以下のコンテンツの解約が完了しました：\n\n{cancelled_text}\n\n次回請求から追加料金が反映されます。{billing_period_info}'
            send_line_message(reply_token, [{"type": "text", "text": success_message}])
        else:
            # 解約対象がない場合
            send_line_message(reply_token, [{"type": "text", "text": "解約対象のコンテンツが見つかりませんでした。"}])
    
    except Exception as e:
        print(f'[ERROR] 企業解約確認処理エラー: {e}')
        import traceback
        traceback.print_exc()
        send_line_message(reply_token, [{"type": "text", "text": "❌ 解約処理に失敗しました。しばらく時間をおいて再度お試しください。"}])
    finally:
        if conn:
            conn.close()

def handle_subscription_cancel_company(reply_token, company_id, stripe_subscription_id):
    """企業ユーザー専用：月額基本サブスクリプション解約処理（月額基本料金システム対応）"""
    try:
        print(f'[DEBUG] 月額基本サブスクリプション解約処理開始: company_id={company_id}, stripe_subscription_id={stripe_subscription_id}')
        
        # データベースタイプを取得
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 月額基本サブスクリプションの確認
        c.execute(f'''
            SELECT subscription_status, monthly_base_price
            FROM company_monthly_subscriptions 
            WHERE company_id = {placeholder}
        ''', (company_id,))
        
        monthly_subscription = c.fetchone()
        if not monthly_subscription:
            send_line_message(reply_token, [{"type": "text", "text": "❌ 月額基本サブスクリプションが見つかりません。"}])
            conn.close()
            return
        
        subscription_status, monthly_base_price = monthly_subscription
        
        if subscription_status != 'active':
            send_line_message(reply_token, [{"type": "text", "text": "❌ 月額基本サブスクリプションが既に非アクティブです。"}])
            conn.close()
            return
        
        # Stripeサブスクリプションの解約処理
        try:
            if stripe_subscription_id:
                # Stripeサブスクリプションを期間終了時に解約
                stripe.Subscription.modify(
                    stripe_subscription_id,
                    cancel_at_period_end=True
                )
                print(f'[DEBUG] Stripeサブスクリプション解約設定完了: {stripe_subscription_id}')
            else:
                print(f'[DEBUG] StripeサブスクリプションIDが存在しません')
        except Exception as e:
            print(f'[DEBUG] Stripe解約エラー: {e}')
            # Stripeエラーが発生しても、データベースは更新する
        
        # データベースの更新
        try:
            # 月額基本サブスクリプションを非アクティブ化
            c.execute(f'''
                UPDATE company_monthly_subscriptions 
                SET subscription_status = 'canceled', updated_at = CURRENT_TIMESTAMP
                WHERE company_id = {placeholder}
            ''', (company_id,))
            
            # 全コンテンツ追加を非アクティブ化（月額解約により全コンテンツが無効になる）
            c.execute(f'''
                UPDATE company_content_additions 
                SET status = 'inactive'
                WHERE company_id = {placeholder}
            ''', (company_id,))
            
            # LINEアカウントも非アクティブ化
            c.execute(f'''
                UPDATE company_line_accounts 
                SET status = 'inactive'
                WHERE company_id = {placeholder}
            ''', (company_id,))
            
            conn.commit()
            print(f'[DEBUG] データベース更新完了: company_id={company_id}')
            
        except Exception as e:
            print(f'[DEBUG] データベース更新エラー: {e}')
            conn.rollback()
            raise e
        
        conn.close()
        
        # 解約完了メッセージを送信
        cancel_message = {
            "type": "template",
            "altText": "月額基本サブスクリプション解約完了",
            "template": {
                "type": "buttons",
                "title": "月額基本サブスクリプション解約完了",
                "text": f"月額基本サブスクリプション（{monthly_base_price:,}円/月）を解約しました。\n\n📋 解約内容:\n• 月額基本料金の解約\n• 全コンテンツの利用停止\n\nご利用ありがとうございました。",
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
        print(f'[DEBUG] 月額基本サブスクリプション解約処理完了')
        
    except Exception as e:
        print(f'[ERROR] 月額基本サブスクリプション解約処理エラー: {e}')
        import traceback
        traceback.print_exc()
        send_line_message(reply_token, [{"type": "text", "text": "❌ 解約処理に失敗しました。しばらく時間をおいて再度お試しください。"}])

def get_welcome_message():
    return "ようこそ！LINE連携が完了しました。"

def get_not_registered_message():
    return "ご登録情報が見つかりません。LPからご登録ください。"

def handle_content_confirmation_company(company_id, content_type):
    """企業ユーザー専用：コンテンツ追加確認処理（月額基本料金システム対応・Stripe請求期間同期）"""
    conn = None
    try:
        print(f'[DEBUG] 企業コンテンツ確認処理開始: company_id={company_id}, content_type={content_type}')
        
        # データベースタイプを取得
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 月額基本サブスクリプションの確認
        c.execute(f'''
            SELECT subscription_status, stripe_subscription_id, current_period_end
            FROM company_monthly_subscriptions 
            WHERE company_id = {placeholder}
        ''', (company_id,))
        
        monthly_subscription = c.fetchone()
        if not monthly_subscription:
            return {
                'success': False, 
                'error': '❌ 月額基本サブスクリプションが見つかりません。\n\n💳 まず月額基本料金の決済を完了してください。'
            }
        
        subscription_status, stripe_subscription_id, current_period_end = monthly_subscription
        # trialing も有効扱いにする
        if subscription_status not in ('active', 'trialing'):
            return {
                'success': False, 
                'error': '❌ 月額基本サブスクリプションが非アクティブです。\n\n💳 月額基本料金の決済を完了してからコンテンツを追加してください。'
            }
        
        print(f'[DEBUG] 月額基本サブスクリプション確認: status={subscription_status}, stripe_id={stripe_subscription_id}')
        
        # Stripeサブスクリプションの請求期間を取得
        stripe_period_end = None
        if stripe_subscription_id:
            try:
                import stripe
                stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
                
                subscription = stripe.Subscription.retrieve(stripe_subscription_id)
                stripe_period_end = subscription.current_period_end
                print(f'[DEBUG] Stripe請求期間終了: {stripe_period_end}')
                
            except Exception as e:
                print(f'[DEBUG] Stripe請求期間取得エラー: {e}')
                # Stripeエラーが発生しても処理を続行
        
        # 既存のLINEアカウントをチェック
        c.execute(f'''
            SELECT id, content_type, status
            FROM company_line_accounts 
            WHERE company_id = {placeholder} AND content_type = {placeholder}
        ''', (company_id, content_type))
        
        existing_account = c.fetchone()
        if existing_account:
            account_id, existing_content_type, status = existing_account
            print(f'[DEBUG] 既存LINEアカウント発見: account_id={account_id}, content_type={existing_content_type}, status={status}')
            
            if status == 'active':
                return {
                    'success': False, 
                    'error': f'✅ {content_type}は既に追加済みです。\n\n📱 他のコンテンツを追加する場合は、再度「追加」を選択してください。\n\n💡 現在の利用状況を確認する場合は「状態」を選択してください。'
                }
            elif status == 'inactive':
                # 非アクティブの場合は再アクティブ化
                c.execute(f'''
                    UPDATE company_line_accounts 
                    SET status = 'active', created_at = CURRENT_TIMESTAMP
                    WHERE id = {placeholder}
                ''', (account_id,))
                conn.commit()
                print(f'[DEBUG] 非アクティブLINEアカウントを再アクティブ化: account_id={account_id}')
                
                # 再アクティブ化後のアクティブコンテンツ数を取得（1個目は無料なので-1）
                c.execute(f'''
                    SELECT COUNT(*) 
                    FROM company_line_accounts 
                    WHERE company_id = {placeholder} AND status = 'active'
                ''', (company_id,))
                
                total_content_count = c.fetchone()[0]
                # 1個目は無料なので、課金対象は総数-1
                if total_content_count > 0:
                    additional_price = 1500  # 2個目以降のコンテンツは有料
                    additional_content_count = max(0, total_content_count - 1)
                else:
                    additional_price = 0  # コンテンツが0個の場合
                    additional_content_count = 0
                    
                print(f'[DEBUG] 再アクティブ化: 総数={total_content_count}, 課金対象={additional_content_count}, 料金={additional_price}')
                
                if additional_price > 0 and stripe_subscription_id:
                    try:
                        import stripe
                        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
                        
                        # Stripeサブスクリプションを取得
                        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
                        
                        # 追加料金の請求項目を更新
                        for item in subscription.items.data:
                            if "追加" in (item.price.nickname or ""):
                                print(f'[DEBUG] Stripe請求項目を更新: {item.id}, 数量={additional_content_count}')
                                stripe.SubscriptionItem.modify(
                                    item.id,
                                    quantity=additional_content_count
                                )
                                print(f'[DEBUG] Stripe請求項目更新完了')
                                break
                                
                    except Exception as e:
                        print(f'[DEBUG] Stripe請求項目更新エラー: {e}')
                        # Stripeエラーが発生しても処理を続行
                
                return {
                    'success': True,
                    'company_id': company_id,
                    'content_type': content_type,
                    'description': f'{content_type}を再アクティブ化しました',
                    'url': 'https://lp-production-9e2c.up.railway.app',
                    'usage': 'LINEアカウントからご利用いただけます',
                    'additional_price': additional_price
                }
        
        # コンテンツ情報を定義
        content_info = {
            'AI予定秘書': {
                'description': '日程調整のストレスから解放される、スケジュール管理の相棒',
                'usage': 'Googleカレンダーと連携し、LINEで予定の追加・確認・空き時間の提案まで。調整のやりとりに追われる時間を、もっとクリエイティブに使えるように。',
                'url': 'https://lp-production-9e2c.up.railway.app/schedule',
                'line_url': 'https://line.me/R/ti/p/@ai_schedule_secretary',
                'additional_price': 1500  # 追加料金対象に変更
            },
            'AI経理秘書': {
                'description': '打合せ後すぐ送れる、スマートな請求書作成アシスタント',
                'usage': 'LINEで項目を送るだけで、見積書や請求書を即作成。営業から事務処理までを一気通貫でスムーズに。',
                'url': 'https://lp-production-9e2c.up.railway.app/accounting',
                'line_url': 'https://line.me/R/ti/p/@ai_accounting_secretary',
                'additional_price': 1500
            },
            'AIタスクコンシェルジュ': {
                'description': '今日やるべきことを、ベストなタイミングで',
                'usage': '登録したタスクを空き時間に自動で配置し、理想的な1日をAIが提案。「やりたいのにできない」を、「自然にこなせる」毎日に。',
                'url': 'https://lp-production-9e2c.up.railway.app/task',
                'line_url': 'https://line.me/R/ti/p/@ai_task_concierge',
                'additional_price': 1500
            }
        }
        
        if content_type not in content_info:
            return {
                'success': False, 
                'error': f'❌ 無効なコンテンツタイプ: {content_type}'
            }
        
        content = content_info[content_type]
        
        # 既存のアクティブコンテンツ数を取得
        c.execute(f'''
            SELECT COUNT(*) 
            FROM company_line_accounts 
            WHERE company_id = {placeholder} AND status = 'active'
        ''', (company_id,))
        
        existing_count = c.fetchone()[0]
        print(f'[DEBUG] 既存アクティブコンテンツ数: {existing_count}')
        
        # 1個目は無料、2個目以降は有料
        if existing_count == 0:
            additional_price = 0  # 初回コンテンツは無料
            print(f'[DEBUG] 初回コンテンツのため無料: {content_type}')
        else:
            additional_price = content['additional_price']  # 2個目以降は有料
            print(f'[DEBUG] 追加コンテンツのため有料: {content_type}, 料金={additional_price}円')
        
        # 請求期間を月額サブスクリプションに合わせる
        billing_end_date = stripe_period_end if stripe_period_end else current_period_end
        print(f'[DEBUG] 請求期間同期: billing_end_date={billing_end_date}')
        
        # 新しいLINEアカウントを登録
        c.execute(f'''
            INSERT INTO company_line_accounts 
            (company_id, content_type, line_channel_id, line_channel_access_token, status)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        ''', (company_id, content_type, f'U{company_id}_{int(time.time())}', 'temp_token', 'active'))
        
        conn.commit()
        print(f'[DEBUG] LINEアカウント登録完了: company_id={company_id}, content_type={content_type}')
        
        # Stripeの請求項目を更新（追加料金が必要なコンテンツの場合）
        if additional_price > 0 and stripe_subscription_id:
            try:
                import stripe
                stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
                
                # 現在のアクティブコンテンツ数を取得（1個目は無料なので-1）
                c.execute(f'''
                    SELECT COUNT(*) 
                    FROM company_line_accounts 
                    WHERE company_id = {placeholder} AND status = 'active'
                ''', (company_id,))
                
                total_content_count = c.fetchone()[0]
                additional_content_count = max(0, total_content_count - 1)  # 1個目は無料なので-1
                print(f'[DEBUG] 総コンテンツ数: {total_content_count}, 追加料金対象: {additional_content_count}')
                
                # Stripeサブスクリプションを取得
                subscription = stripe.Subscription.retrieve(stripe_subscription_id)
                print(f'[DEBUG] Stripeサブスクリプション取得: {subscription.id}')
                
                # サブスクリプションアイテムを詳細にログ出力
                print(f'[DEBUG] サブスクリプションアイテム数: {len(subscription.items.data)}')
                for i, item in enumerate(subscription.items.data):
                    print(f'[DEBUG] アイテム{i}: ID={item.id}, Price={item.price.id}, Nickname={item.price.nickname}, Quantity={item.quantity}')
                
                # 追加料金の請求項目を更新（複数の条件で検索）
                updated = False
                for item in subscription.items.data:
                    price_nickname = item.price.nickname or ""
                    price_id = item.price.id
                    
                    # 複数の条件で追加料金アイテムを特定
                    if (("追加" in price_nickname) or 
                        ("additional" in price_nickname.lower()) or
                        ("metered" in price_nickname.lower()) or
                        (price_id == 'price_1Rog1nIxg6C5hAVdnqB5MJiT')):  # 既知のPrice ID
                        
                        print(f'[DEBUG] 追加料金アイテム発見: {item.id}, Price={price_id}, Nickname={price_nickname}')
                        print(f'[DEBUG] Stripe請求項目を更新: {item.id}, 数量={additional_content_count}')
                        
                        # 数量を更新
                        stripe.SubscriptionItem.modify(
                            item.id,
                            quantity=additional_content_count
                        )
                        print(f'[DEBUG] Stripe請求項目更新完了: {item.id}')
                        updated = True
                        break
                
                if not updated:
                    print(f'[WARN] 追加料金アイテムが見つかりませんでした。手動で確認が必要です。')
                    print(f'[DEBUG] 利用可能なアイテム:')
                    for item in subscription.items.data:
                        print(f'  - ID: {item.id}, Price: {item.price.id}, Nickname: {item.price.nickname}')
                        
            except Exception as e:
                print(f'[ERROR] Stripe請求項目更新エラー: {e}')
                import traceback
                traceback.print_exc()
                # Stripeエラーが発生しても処理を続行
        
        # 請求期間同期サービスを呼び出して使用量レコードを月額サブスクリプション期間に合わせる
        if stripe_subscription_id:
            try:
                from services.billing_period_sync_service import BillingPeriodSyncService
                billing_sync_service = BillingPeriodSyncService()
                sync_success = billing_sync_service.sync_usage_records_to_subscription_period(stripe_subscription_id)
                
                if sync_success:
                    print(f'[DEBUG] 請求期間同期完了: subscription_id={stripe_subscription_id}')
                else:
                    print(f'[WARN] 請求期間同期に失敗: subscription_id={stripe_subscription_id}')
                    
            except Exception as e:
                print(f'[DEBUG] 請求期間同期エラー: {e}')
                # 同期エラーが発生しても処理を続行
        
        return {
            'success': True,
            'company_id': company_id,
            'content_type': content_type,
            'description': content['description'],
            'usage': content['usage'],
            'url': content['url'],
            'additional_price': additional_price,
            'billing_end_date': billing_end_date
        }
        
    except Exception as e:
        print(f'[ERROR] 企業コンテンツ確認処理エラー: {e}')
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}
    finally:
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
        return False