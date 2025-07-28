import requests
import sqlite3
import psycopg2
import os
import stripe
import traceback
import time
from utils.db import get_db_connection
import re
import datetime

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

# LINE関連のサービス層

def send_line_message(reply_token, messages):
    """LINEメッセージ送信（複数メッセージ対応）"""
    import requests
    import os
    import traceback
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    headers = {
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    # 単一メッセージの場合はリスト化
    if not isinstance(messages, list):
        messages = [messages]
    # actionsが5つ以上のボタンテンプレートがあれば4つまでに制限
    for msg in messages:
        if msg.get('type') == 'template' and 'template' in msg:
            tmpl = msg['template']
            if tmpl.get('type') == 'buttons' and 'actions' in tmpl and len(tmpl['actions']) > 4:
                print('[WARN] actionsが5つ以上のため4つまでに自動制限します')
                tmpl['actions'] = tmpl['actions'][:4]
    data = {
        'replyToken': reply_token,
        'messages': messages
    }
    print('[DEBUG] LINE送信内容:', data)  # 送信内容をprint
    try:
        response = requests.post('https://api.line.me/v2/bot/message/reply', headers=headers, json=data)
        response.raise_for_status()
    except Exception as e:
        print(f'LINEメッセージ送信エラー: {e}')
        if hasattr(e, 'response') and e.response is not None:
            print(f'LINE API エラー詳細: {e.response.text}')
        traceback.print_exc()
        # エラー詳細をerror.logにも追記
        with open('error.log', 'a', encoding='utf-8') as f:
            f.write('LINEメッセージ送信エラー: ' + str(e) + '\n')
            f.write(traceback.format_exc() + '\n')

def send_welcome_with_buttons(reply_token):
    print(f'[DEBUG] send_welcome_with_buttons開始: reply_token={reply_token}')
    import requests
    import os
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    headers = {
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        'replyToken': reply_token,
        'messages': [
            {
                "type": "text",
                "text": "ようこそ！AIコレクションズへ\n\nAIコレクションズサービスをご利用いただき、ありがとうございます。\n\n📋 サービス内容：\n• AI予定秘書：スケジュール管理\n• AI経理秘書：見積書・請求書作成\n• AIタスクコンシェルジュ：タスク管理\n\n💰 料金体系：\n• 月額基本料金：3,900円（1週間無料）\n• 追加コンテンツ：1個目無料、2個目以降1,500円/件（トライアル期間中は無料）\n\n下のボタンからお選びください。"
            },
            {
                "type": "template",
                "altText": "メニュー",
                "template": {
                    "type": "buttons",
                    "title": "メニュー",
                    "text": "ご希望の機能を選択してください。",
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
        ]
    }
    try:
        print(f'[DEBUG] LINE API送信開始: data={data}')
        response = requests.post('https://api.line.me/v2/bot/message/reply', headers=headers, json=data)
        response.raise_for_status()
        print(f'[DEBUG] LINE API送信成功: status_code={response.status_code}')
    except Exception as e:
        print(f'LINEテンプレートメッセージ送信エラー: {e}')
        import traceback
        traceback.print_exc()
        with open('error.log', 'a', encoding='utf-8') as f:
            f.write('LINEテンプレートメッセージ送信エラー: ' + str(e) + '\n')
            f.write(traceback.format_exc() + '\n')

def send_welcome_with_buttons_push(user_id):
    """LINEユーザーIDに直接案内文を送信（pushメッセージ）"""
    print(f'[DEBUG] send_welcome_with_buttons_push開始: user_id={user_id}')
    import requests
    import os
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    headers = {
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        'to': user_id,
        'messages': [
            {
                "type": "text",
                "text": "ようこそ！AIコレクションズへ\n\nAIコレクションズサービスをご利用いただき、ありがとうございます。\n\n📋 サービス内容：\n• AI予定秘書：スケジュール管理\n• AI経理秘書：見積書・請求書作成\n• AIタスクコンシェルジュ：タスク管理\n\n💰 料金体系：\n• 月額基本料金：3,900円（1週間無料）\n• 追加コンテンツ：1個目無料、2個目以降1,500円/件（トライアル期間中は無料）\n\n下のボタンからお選びください。"
            },
            {
                "type": "template",
                "altText": "メニュー",
                "template": {
                    "type": "buttons",
                    "title": "メニュー",
                    "text": "ご希望の機能を選択してください。",
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
        ]
    }
    try:
        print(f'[DEBUG] LINE Push API送信開始: data={data}')
        response = requests.post('https://api.line.me/v2/bot/message/push', headers=headers, json=data)
        response.raise_for_status()
        print(f'[DEBUG] LINE Push API送信成功: status_code={response.status_code}')
        return True
    except Exception as e:
        print(f'LINE Push テンプレートメッセージ送信エラー: {e}')
        import traceback
        traceback.print_exc()
        with open('error.log', 'a', encoding='utf-8') as f:
            f.write('LINE Push テンプレートメッセージ送信エラー: ' + str(e) + '\n')
            f.write(traceback.format_exc() + '\n')
        return False

def create_rich_menu():
    rich_menu = {
        "size": {"width": 2500, "height": 843},
        "selected": True,
        "name": "AIコレクションズ メニュー",
        "chatBarText": "メニュー",
        "areas": [
            {
                "bounds": {"x": 0, "y": 0, "width": 500, "height": 843},
                "action": {"type": "postback", "data": "action=add_content", "label": "追加"}
            },
            {
                "bounds": {"x": 500, "y": 0, "width": 500, "height": 843},
                "action": {"type": "postback", "data": "action=cancel_content", "label": "解約"}
            },
            {
                "bounds": {"x": 1000, "y": 0, "width": 500, "height": 843},
                "action": {"type": "postback", "data": "action=check_status", "label": "状態"}
            },
            {
                "bounds": {"x": 1500, "y": 0, "width": 500, "height": 843},
                "action": {"type": "postback", "data": "action=help", "label": "ヘルプ"}
            },
            {
                "bounds": {"x": 2000, "y": 0, "width": 500, "height": 843},
                "action": {"type": "postback", "data": "action=share", "label": "友達に紹介"}
            }
        ]
    }
    headers = {
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    response = requests.post('https://api.line.me/v2/bot/richmenu', headers=headers, json=rich_menu)
    response.raise_for_status()
    return response.json()['richMenuId']

def set_rich_menu_image(rich_menu_id, image_path='static/images/richmenu.png'):
    """リッチメニューに画像を設定"""
    try:
        # リッチメニュー画像を生成
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # 画像を生成
        width, height = 2500, 843
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # フォント設定（デフォルトフォントを使用）
        try:
            font = ImageFont.truetype("arial.ttf", 60)
        except:
            font = ImageFont.load_default()
        
        # メニュー項目を描画
        menu_items = [
            ("追加", (200, 200)),
            ("状態", (700, 200)),
            ("解約", (1200, 200)),
            ("メニュー", (1700, 200))
        ]
        
        for text, pos in menu_items:
            draw.text(pos, text, fill='black', font=font)
        
        # 画像をバイトデータに変換
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
            'Content-Type': 'image/png'
        }
        
        response = requests.post(
            f'https://api.line.me/v2/bot/richmenu/{rich_menu_id}/content',
            headers=headers,
            data=img_byte_arr
        )
        
        if response.status_code == 200:
            print(f"リッチメニュー画像設定成功: {rich_menu_id}")
            return True
        else:
            print(f"リッチメニュー画像設定失敗: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"リッチメニュー画像設定エラー: {e}")
        return False

def set_default_rich_menu(rich_menu_id):
    """デフォルトリッチメニューを設定"""
    try:
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f'https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}',
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"デフォルトリッチメニュー設定成功: {rich_menu_id}")
            return True
        else:
            print(f"デフォルトリッチメニュー設定失敗: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"デフォルトリッチメニュー設定エラー: {e}")
        return False

def delete_all_rich_menus():
    """既存のリッチメニューをすべて削除"""
    try:
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
        }
        
        response = requests.get('https://api.line.me/v2/bot/richmenu/list', headers=headers)
        
        if response.status_code == 200:
            richmenus = response.json().get('richmenus', [])
            for rm in richmenus:
                delete_response = requests.delete(f'https://api.line.me/v2/bot/richmenu/{rm["richMenuId"]}', headers=headers)
                if delete_response.status_code == 200:
                    print(f"リッチメニュー削除成功: {rm['richMenuId']}")
                else:
                    print(f"リッチメニュー削除失敗: {rm['richMenuId']} - {delete_response.status_code}")
            print(f"既存のリッチメニュー削除完了: {len(richmenus)}件")
        else:
            print(f"リッチメニュー一覧取得失敗: {response.status_code}")
            
    except Exception as e:
        print(f"リッチメニュー削除エラー: {e}")

def setup_rich_menu():
    import time
    delete_all_rich_menus()
    rich_menu_id = create_rich_menu()
    time.sleep(1)  # 作成直後に1秒待機
    set_rich_menu_image(rich_menu_id)
    set_default_rich_menu(rich_menu_id)
    return rich_menu_id 

def check_subscription_status(stripe_subscription_id):
    """サブスクリプションの状態をチェック"""
    try:
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        status = subscription['status']
        cancel_at_period_end = subscription.get('cancel_at_period_end', False)
        
        print(f'[DEBUG] サブスクリプション状態: status={status}, cancel_at_period_end={cancel_at_period_end}')
        
        # 有効な状態かチェック
        # trialing（試用期間）とactive（有効）の場合は有効とする
        is_active = status in ['active', 'trialing']
        
        return {
            'is_active': is_active,
            'status': status,
            'cancel_at_period_end': cancel_at_period_end,
            'current_period_end': subscription.get('current_period_end'),
            'subscription': subscription
        }
    except Exception as e:
        print(f'[ERROR] サブスクリプション状態確認エラー: {e}')
        return {
            'is_active': False,
            'status': 'error',
            'error': str(e)
        }

def handle_add_content(reply_token, user_id_db, stripe_subscription_id):
    try:
        # サブスクリプション状態をチェック
        subscription_status = check_subscription_status(stripe_subscription_id)
        
        if not subscription_status['is_active']:
            if subscription_status['status'] == 'canceled':
                # サブスクリプションが解約済み
                payment_message = {
                    "type": "template",
                    "altText": "サブスクリプション解約済み",
                    "template": {
                        "type": "buttons",
                        "title": "サブスクリプション解約済み",
                        "text": "サブスクリプションが解約されています。\n\nコンテンツを追加するには、新しいサブスクリプションが必要です。",
                        "actions": [
                            {
                                "type": "uri",
                                "label": "決済画面へ",
                                "uri": "https://lp-production-9e2c.up.railway.app"
                            }
                        ]
                    }
                }
                send_line_message(reply_token, [payment_message])
                return
            elif subscription_status['cancel_at_period_end']:
                # 期間終了時に解約予定
                payment_message = {
                    "type": "template",
                    "altText": "サブスクリプション解約予定",
                    "template": {
                        "type": "buttons",
                        "title": "サブスクリプション解約予定",
                        "text": "サブスクリプションが期間終了時に解約予定です。\n\nコンテンツを追加するには、サブスクリプションを更新してください。",
                        "actions": [
                            {
                                "type": "uri",
                                "label": "決済画面へ",
                                "uri": "https://lp-production-9e2c.up.railway.app"
                            }
                        ]
                    }
                }
                send_line_message(reply_token, [payment_message])
                return
            else:
                # その他の無効な状態
                payment_message = {
                    "type": "template",
                    "altText": "サブスクリプション無効",
                    "template": {
                        "type": "buttons",
                        "title": "サブスクリプション無効",
                        "text": "サブスクリプションが無効な状態です。\n\nコンテンツを追加するには、有効なサブスクリプションが必要です。",
                        "actions": [
                            {
                                "type": "uri",
                                "label": "決済画面へ",
                                "uri": "https://lp-production-9e2c.up.railway.app"
                            }
                        ]
                    }
                }
                send_line_message(reply_token, [payment_message])
                return
        
        # サブスクリプションが有効な場合、通常のコンテンツ選択メニューを表示
        content_menu = {
            "type": "template",
            "altText": "コンテンツ選択メニュー",
            "template": {
                "type": "buttons",
                "title": "コンテンツ選択メニュー",
                "text": "利用したいコンテンツを選択してください。\n\n1個目無料、2個目以降1,500円/件",
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
        send_line_message(reply_token, [content_menu])
    except Exception as e:
        print(f'コンテンツ選択メニューエラー: {e}')
        import traceback
        traceback.print_exc()
        send_line_message(reply_token, [{"type": "text", "text": "エラーが発生しました。しばらく時間をおいて再度お試しください。"}])

def handle_content_selection(reply_token, user_id_db, stripe_subscription_id, content_number):
    try:
        content_info = {
            '1': {
                'name': 'AI予定秘書',
                'price': 1500,
                "description": '日程調整のストレスから解放される、スケジュール管理の相棒',
                'usage': 'Googleカレンダーと連携し、LINEで予定の追加・確認・空き時間の提案まで。調整のやりとりに追われる時間を、もっとクリエイティブに使えるように。',
                'url': 'https://lp-production-9e2c.up.railway.app/schedule'
            },
            '2': {
                'name': 'AI経理秘書',
                'price': 1500,
                "description": '打合せ後すぐ送れる、スマートな請求書作成アシスタント',
                'usage': 'LINEで項目を送るだけで、見積書や請求書を即作成。営業から事務処理までを一気通貫でスムーズに。',
                'url': 'https://lp-production-9e2c.up.railway.app/accounting'
            },
            '3': {
                'name': 'AIタスクコンシェルジュ',
                'price': 1500,
                "description": '今日やるべきことを、ベストなタイミングで',
                'usage': '登録したタスクを空き時間に自動で配置し、理想的な1日をAIが提案。「やりたいのにできない」を、「自然にこなせる」毎日に。',
                'url': 'https://lp-production-9e2c.up.railway.app/task'
            }
        }
        if content_number not in content_info:
            send_line_message(reply_token, [{"type": "text", "text": "無効な選択です。1-3の数字で選択してください。"}])
            return
        content = content_info[str(content_number)]
        # 全コンテンツの合計数を取得
        conn_count = get_db_connection()
        c_count = conn_count.cursor()
        # データベースタイプに応じてプレースホルダーを選択
        from utils.db import get_db_type
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        c_count.execute(f'SELECT COUNT(*) FROM usage_logs WHERE user_id = {placeholder}', (user_id_db,))
        total_usage_count = c_count.fetchone()[0]
        
        # デバッグ用：実際のusage_logsを確認
        c_count.execute('SELECT id, content_type, created_at FROM usage_logs WHERE user_id = %s ORDER BY created_at', (user_id_db,))
        all_logs = c_count.fetchall()
        print(f'[DEBUG] 全usage_logs: {all_logs}')
        
        # 同じコンテンツの追加回数を確認
        c_count.execute(f'SELECT COUNT(*) FROM usage_logs WHERE user_id = {placeholder} AND content_type = {placeholder}', (user_id_db, content['name']))
        same_content_count = c_count.fetchone()[0]
        conn_count.close()
        
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
        subscription_status = check_subscription_status(stripe_subscription_id)
        is_trial_period = subscription_status.get('subscription', {}).get('status') == 'trialing'
        
        # トライアル期間終了後のコンテンツ追加回数を正しく計算
        if is_trial_period:
            # トライアル期間中でも、1個目は無料、2個目以降は有料（トライアル終了後に課金）
            current_count = total_usage_count + 1
            is_free = current_count == 1
            print(f'[DEBUG] トライアル期間中: total_usage_count={total_usage_count}, current_count={current_count}, is_free={is_free}')
        else:
            # トライアル期間終了後は、トライアル期間中の追加分を除いて計算
            # トライアル期間中の追加分を取得
            conn_trial = get_db_connection()
            c_trial = conn_trial.cursor()
            c_trial.execute('''
                SELECT COUNT(*) FROM usage_logs 
                WHERE user_id = %s AND pending_charge = FALSE
            ''', (user_id_db,))
            trial_additions = c_trial.fetchone()[0]
            conn_trial.close()
            
            # トライアル期間終了後の追加回数
            post_trial_count = total_usage_count - trial_additions + 1
            current_count = post_trial_count
            is_free = current_count == 1
            print(f'[DEBUG] 通常期間: total_usage_count={total_usage_count}, trial_additions={trial_additions}, current_count={current_count}, is_free={is_free}')
        
        if current_count == 1:
            price_message = f"料金：無料（{current_count}個目）"
        else:
            price_message = f"料金：1,500円（{current_count}個目、月額料金に追加）"
            print(f'[DEBUG] 2個目以降のコンテンツ追加: is_free={is_free}, current_count={current_count}')
        confirm_message = {
            "type": "template",
            "altText": "選択内容の確認",
            "template": {
                "type": "buttons",
                "title": "選択内容の確認",
                "text": f"コンテンツ：{content['name']}\n{price_message}\n\n追加しますか？",
                "actions": [
                    {
                        "type": "message",
                        "label": "はい、追加する",
                        "text": "はい"
                    },
                    {
                        "type": "message",
                        "label": "いいえ、キャンセル",
                        "text": "いいえ"
                    }
                ]
            }
        }
        send_line_message(reply_token, [confirm_message])
        
    except Exception as e:
        print(f'コンテンツ選択エラー: {e}')
        send_line_message(reply_token, [{"type": "text", "text": "❌ エラーが発生しました。しばらく時間をおいて再度お試しください。"}])

def handle_content_confirmation(reply_token, user_id_db, stripe_subscription_id, content_number, confirmed):
    import os
    import stripe
    import datetime
    from dotenv import load_dotenv
    
    # 環境変数を読み込み
    load_dotenv()
    
    # Stripe APIキーを設定
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    
    print(f'[DEBUG] handle_content_confirmation called: user_id_db={user_id_db}, content_number={content_number}, confirmed={confirmed}')
    print(f'[DEBUG] 環境変数: STRIPE_USAGE_PRICE_ID={os.getenv("STRIPE_USAGE_PRICE_ID")}, STRIPE_SECRET_KEY={os.getenv("STRIPE_SECRET_KEY")}, DATABASE_URL={os.getenv("DATABASE_URL")}, subscription_id={stripe_subscription_id}')
    try:
        if not confirmed:
            cancel_message = {
                "type": "template",
                "altText": "キャンセルしました",
                "template": {
                    "type": "buttons",
                    "title": "❌ キャンセルしました",
                    "text": "何か他にお手伝いできることはありますか？",
                    "actions": [
                        {
                            "type": "message",
                            "label": "📚 コンテンツ追加",
                            "text": "追加"
                        },
                        {
                            "type": "message",
                            "label": "📊 利用状況確認",
                            "text": "状態"
                        },
                        {
                            "type": "message",
                            "label": "❓ ヘルプ",
                            "text": "ヘルプ"
                        }
                    ]
                }
            }
            send_line_message(reply_token, [cancel_message])
            return
        
        # サブスクリプション状態をチェック
        subscription_status = check_subscription_status(stripe_subscription_id)
        
        if not subscription_status['is_active']:
            if subscription_status['status'] == 'canceled':
                # サブスクリプションが解約済み
                payment_message = {
                    "type": "template",
                    "altText": "サブスクリプション解約済み",
                    "template": {
                        "type": "buttons",
                        "title": "サブスクリプション解約済み",
                        "text": "サブスクリプションが解約されています。\n\nコンテンツを追加するには、新しいサブスクリプションが必要です。",
                        "actions": [
                            {
                                "type": "uri",
                                "label": "決済画面へ",
                                "uri": "https://lp-production-9e2c.up.railway.app"
                            }
                        ]
                    }
                }
                send_line_message(reply_token, [payment_message])
                return
            elif subscription_status['cancel_at_period_end']:
                # 期間終了時に解約予定
                payment_message = {
                    "type": "template",
                    "altText": "サブスクリプション解約予定",
                    "template": {
                        "type": "buttons",
                        "title": "サブスクリプション解約予定",
                        "text": "サブスクリプションが期間終了時に解約予定です。\n\nコンテンツを追加するには、サブスクリプションを更新してください。",
                        "actions": [
                            {
                                "type": "uri",
                                "label": "決済画面へ",
                                "uri": "https://lp-production-9e2c.up.railway.app"
                            }
                        ]
                    }
                }
                send_line_message(reply_token, [payment_message])
                return
            else:
                # その他の無効な状態
                payment_message = {
                    "type": "template",
                    "altText": "サブスクリプション無効",
                    "template": {
                        "type": "buttons",
                        "title": "サブスクリプション無効",
                    "text": "サブスクリプションが無効な状態です。\n\nコンテンツを追加するには、有効なサブスクリプションが必要です。",
                        "actions": [
                            {
                                "type": "uri",
                                "label": "決済画面へ",
                                "uri": "https://lp-production-9e2c.up.railway.app"
                            }
                        ]
                    }
                }
                send_line_message(reply_token, [payment_message])
                return
        
        # コンテンツ情報を取得
        content_info = {
            "1": {"name": "AI予定秘書", "description": "予定管理をサポートするAI秘書"},
            "2": {"name": "AI経理秘書", "description": "経理業務をサポートするAI秘書"},
            "3": {"name": "AIタスクコンシェルジュ", "description": "タスク管理をサポートするAIコンシェルジュ"}
        }
        
        content = content_info[str(content_number)]
        
        # 既に追加済みかチェック
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            SELECT COUNT(*) FROM usage_logs 
            WHERE user_id = %s AND content_type = %s
        ''', (user_id_db, content['name']))
        already_added = c.fetchone()[0] > 0
        conn.close()
        
        if already_added:
            already_added_message = {
                "type": "template",
                "altText": "既に追加済み",
                "template": {
                    "type": "buttons",
                    "title": "既に追加済み",
                    "text": f"{content['name']}は既に追加済みです。",
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
        subscription_status = check_subscription_status(stripe_subscription_id)
        is_trial_period = subscription_status.get('subscription', {}).get('status') == 'trialing'
        is_trial = subscription_status['status'] == 'trialing'
        
        # 全コンテンツの合計数を取得（handle_content_selectionと同じロジック）
        conn_count = get_db_connection()
        c_count = conn_count.cursor()
        from utils.db import get_db_type
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        c_count.execute(f'SELECT COUNT(*) FROM usage_logs WHERE user_id = {placeholder}', (user_id_db,))
        total_usage_count = c_count.fetchone()[0]
        conn_count.close()
        
        # トライアル期間終了後のコンテンツ追加回数を正しく計算（handle_content_selectionと同じロジック）
        if is_trial_period:
            # トライアル期間中でも、1個目は無料、2個目以降は有料（トライアル終了後に課金）
            current_count = total_usage_count + 1
            is_free = current_count == 1
            print(f'[DEBUG] トライアル期間中: total_usage_count={total_usage_count}, current_count={current_count}, is_free={is_free}')
        else:
            # トライアル期間終了後は、トライアル期間中の追加分を除いて計算
            # トライアル期間中の追加分を取得
            conn_trial = get_db_connection()
            c_trial = conn_trial.cursor()
            c_trial.execute('''
                SELECT COUNT(*) FROM usage_logs 
                WHERE user_id = %s AND pending_charge = FALSE
            ''', (user_id_db,))
            trial_additions = c_trial.fetchone()[0]
            conn_trial.close()
            
            # トライアル期間終了後の追加回数
            post_trial_count = total_usage_count - trial_additions + 1
            current_count = post_trial_count
            is_free = current_count == 1
            print(f'[DEBUG] 通常期間: total_usage_count={total_usage_count}, trial_additions={trial_additions}, current_count={current_count}, is_free={is_free}')
        
        if current_count == 1:
            price_message = f"料金：無料（{current_count}個目）"
        else:
            price_message = f"料金：1,500円（{current_count}個目、月額料金に追加）"
            print(f'[DEBUG] 2個目以降のコンテンツ追加: is_free={is_free}, current_count={current_count}')
        
        print(f"[DEBUG] content_type: {content['name']}")
        print(f"[DEBUG] DATABASE_URL: {os.getenv('DATABASE_URL')}")
        print(f"[DEBUG] is_free: {is_free}")
        print(f"[DEBUG] current_count: {current_count}")
        print(f"[DEBUG] is_trial_period: {is_trial_period}")
        print(f"[DEBUG] price_message: {price_message}")
        
        # データベースに記録
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO usage_logs (user_id, usage_quantity, stripe_usage_record_id, is_free, content_type, pending_charge)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (user_id_db, 1, None, is_free, content['name'], not is_free))
        conn.commit()
        conn.close()
        print(f'[DEBUG] DB登録成功: user_id={user_id_db}, content={content["name"]}, is_free={is_free}')
        
        # Stripe Invoice Itemを作成（月額料金に統合）
        # トライアル期間中でも、2個目以降のコンテンツはInvoice Itemを作成（トライアル終了後に課金）
        if not is_free:
            try:
                # サブスクリプションから顧客IDを取得
                subscription = stripe.Subscription.retrieve(stripe_subscription_id)
                customer_id = subscription.customer
                
                # 請求期間を取得（トライアル期間中の場合は次の通常期間を使用）
                if subscription.status == 'trialing':
                    # トライアル期間中の場合は、次の通常期間を計算
                    # トライアル終了日から次の月額期間を開始
                    trial_end = subscription.trial_end
                    from datetime import datetime, timedelta
                    
                    # trial_endをdatetimeオブジェクトに変換
                    if isinstance(trial_end, int):
                        trial_end_dt = datetime.fromtimestamp(trial_end)
                    else:
                        trial_end_dt = trial_end
                    
                    # 次の月額期間の開始日（トライアル終了日の翌日）
                    current_period_start = int((trial_end_dt + timedelta(days=1)).timestamp())
                    
                    # 次の月額期間の終了日（開始日から1ヶ月後）
                    next_period_end = trial_end_dt + timedelta(days=1) + timedelta(days=30)
                    current_period_end = int(next_period_end.timestamp())
                    
                    print(f'[DEBUG] トライアル期間中: trial_end={trial_end_dt}, next_period_start={datetime.fromtimestamp(current_period_start)}, next_period_end={datetime.fromtimestamp(current_period_end)}')
                else:
                    # 通常期間の場合は現在の期間を使用
                    current_period_start = subscription.current_period_start
                    current_period_end = subscription.current_period_end
                    print(f'[DEBUG] 通常期間: period_start={datetime.fromtimestamp(current_period_start)}, period_end={datetime.fromtimestamp(current_period_end)}')
                
                # Invoice Itemを作成（月額料金と同じ期間で課金）
                invoice_item = stripe.InvoiceItem.create(
                    customer=customer_id,
                    amount=1500,  # ¥1,500
                    currency='jpy',
                    description=f"コンテンツ追加: {content['name']} ({current_count}個目)",
                    subscription=stripe_subscription_id,
                    period={
                        'start': current_period_start,
                        'end': current_period_end
                    }
                )
                print(f'[DEBUG] Stripe InvoiceItem作成成功: {invoice_item.id}, amount=1500, period_start={current_period_start}, period_end={current_period_end}')
                
                # データベースのStripe Usage Record IDを更新
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('''
                    UPDATE usage_logs 
                    SET stripe_usage_record_id = %s 
                    WHERE user_id = %s AND content_type = %s AND stripe_usage_record_id IS NULL
                    ORDER BY created_at DESC 
                    LIMIT 1
                ''', (invoice_item.id, user_id_db, content['name']))
                conn.commit()
                conn.close()
                print(f'[DEBUG] DB更新成功: stripe_usage_record_id={invoice_item.id}')
                
            except Exception as e:
                print(f'[DEBUG] Stripe InvoiceItem作成エラー: {e}')
                # エラーが発生してもデータベースには記録済みなので続行
        
        # 成功メッセージを送信
        if is_free:
            success_message = {
                "type": "template",
                "altText": "追加完了",
                "template": {
                    "type": "buttons",
                    "title": "✅ 追加完了",
                    "text": f"追加内容：{content['name']}\n{price_message}\n\n次回請求時に月額料金に含まれます。",
                    "actions": [
                        {
                            "type": "message",
                            "label": "📚 他のコンテンツ追加",
                            "text": "追加"
                        },
                        {
                            "type": "message",
                            "label": "📊 利用状況確認",
                            "text": "状態"
                        },
                        {
                            "type": "message",
                            "label": "❓ ヘルプ",
                            "text": "ヘルプ"
                        }
                    ]
                }
            }
        else:
            success_message = {
                "type": "template",
                "altText": "追加完了",
                "template": {
                    "type": "buttons",
                    "title": "✅ 追加完了",
                    "text": f"追加内容：{content['name']}\n{price_message}\n\n次回請求時に月額料金に含まれます。",
                    "actions": [
                        {
                            "type": "message",
                            "label": "📚 他のコンテンツ追加",
                            "text": "追加"
                        },
                        {
                            "type": "message",
                            "label": "📊 利用状況確認",
                            "text": "状態"
                        },
                        {
                            "type": "message",
                            "label": "❓ ヘルプ",
                            "text": "ヘルプ"
                        }
                    ]
                }
            }
        
        send_line_message(reply_token, [success_message])
        
    except Exception as e:
        print(f'[DEBUG] handle_content_confirmation エラー: {e}')
        error_message = {
            "type": "template",
            "altText": "エラーが発生しました",
            "template": {
                "type": "buttons",
                "title": "❌ エラーが発生しました",
                "text": "コンテンツの追加中にエラーが発生しました。\n\nしばらく時間をおいて再度お試しください。",
                "actions": [
                    {
                        "type": "message",
                        "label": "📚 コンテンツ追加",
                        "text": "追加"
                    },
                    {
                        "type": "message",
                        "label": "❓ ヘルプ",
                        "text": "ヘルプ"
                    }
                ]
            }
        }
        send_line_message(reply_token, [error_message])

def check_and_charge_trial_expired_content(user_id_db, stripe_subscription_id):
    """トライアル期間終了時に、2個目以降のコンテンツを課金予定状態に変更する"""
    try:
        # サブスクリプション状態をチェック
        subscription_status = check_subscription_status(stripe_subscription_id)
        is_trial_period = subscription_status.get('subscription', {}).get('status') == 'trialing'
        
        # トライアル期間中の場合は何もしない
        if is_trial_period:
            return {"status": "trial_active", "message": "トライアル期間中です"}
        
        # データベースから利用状況を取得
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            SELECT id, content_type, is_free, created_at, pending_charge 
            FROM usage_logs 
            WHERE user_id = %s 
            ORDER BY created_at ASC
        ''', (user_id_db,))
        usage_logs = c.fetchall()
        conn.close()
        
        if not usage_logs:
            return {"status": "no_content", "message": "コンテンツがありません"}
        
        # 2個目以降の無料コンテンツを課金予定状態に変更
        content_to_mark = []
        for i, log in enumerate(usage_logs):
            log_id, content_type, is_free, created_at, pending_charge = log
            if i >= 1 and is_free and not pending_charge:  # 2個目以降で無料かつ課金予定でないもの
                content_to_mark.append({
                    'id': log_id,
                    'content_type': content_type,
                    'created_at': created_at,
                    'position': i + 1  # 何個目かを記録
                })
        
        if not content_to_mark:
            return {"status": "no_charge_needed", "message": "課金対象のコンテンツがありません"}
        
        print(f'[DEBUG] 課金予定対象: {len(content_to_mark)}個のコンテンツ')
        for content in content_to_mark:
            print(f'[DEBUG] 課金予定: {content["content_type"]} ({content["position"]}個目)')
        
        # データベースを更新（課金予定状態に変更）
        conn = get_db_connection()
        c = conn.cursor()
        marked_count = 0
        marked_details = []
        
        for content in content_to_mark:
            try:
                c.execute('''
                    UPDATE usage_logs 
                    SET pending_charge = TRUE 
                    WHERE id = %s
                ''', (content['id'],))
                
                marked_count += 1
                marked_details.append(f"{content['content_type']} ({content['position']}個目)")
                print(f'[DEBUG] 課金予定設定完了: {content["content_type"]} ({content["position"]}個目)')
                
            except Exception as e:
                print(f'[DEBUG] 課金予定設定エラー: {content["content_type"]} ({content["position"]}個目), error={e}')
                continue
        
        conn.commit()
        conn.close()
        
        return {
            "status": "pending_charge", 
            "message": f"{marked_count}個のコンテンツが次回請求時に課金予定になりました",
            "marked_count": marked_count,
            "marked_details": marked_details
        }
        
    except Exception as e:
        print(f'[DEBUG] 課金予定処理エラー: {e}')
        return {"status": "error", "message": f"課金予定処理でエラーが発生しました: {e}"}

def handle_status_check(reply_token, user_id_db):
    try:
        # ユーザーのサブスクリプション情報を取得
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT stripe_subscription_id FROM users WHERE id = %s', (user_id_db,))
        user = c.fetchone()
        conn.close()
        
        if not user or not user[0]:
            payment_message = {
                "type": "template",
                "altText": "決済が必要です",
                "template": {
                    "type": "buttons",
                    "title": "決済が必要です",
                    "text": "サブスクリプションが設定されていません。\n\n決済画面から登録してください。",
                    "actions": [
                        {
                            "type": "uri",
                            "label": "決済画面へ",
                            "uri": "https://lp-production-9e2c.up.railway.app"
                        }
                    ]
                }
            }
            send_line_message(reply_token, [payment_message])
            return
        
        stripe_subscription_id = user[0]
        
        # サブスクリプション状態をチェック
        subscription_status = check_subscription_status(stripe_subscription_id)
        is_trial_period = subscription_status.get('subscription', {}).get('status') == 'trialing'
        
        # トライアル期間終了時の自動課金処理
        if not is_trial_period:
            auto_charge_result = check_and_charge_trial_expired_content(user_id_db, stripe_subscription_id)
            print(f'[DEBUG] 自動課金処理結果: {auto_charge_result}')
        
        # データベースから利用状況を取得（最新のデータのみ）
        conn = get_db_connection()
        c = conn.cursor()
        # 最新のサブスクリプションIDに関連するデータのみを取得
        c.execute('''
            SELECT content_type, is_free, created_at 
            FROM usage_logs 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT 10
        ''', (user_id_db,))
        usage_logs = c.fetchall()
        conn.close()
        
        # ステータスメッセージを構築
        status_lines = ["📊 利用状況"]
        
        # 自動課金の結果を表示
        if not is_trial_period and 'auto_charge_result' in locals():
            if auto_charge_result.get('status') == 'pending_charge':
                marked_count = auto_charge_result.get('marked_count', 0)
                marked_details = auto_charge_result.get('marked_details', [])
                if marked_count > 0:
                    status_lines.append(f"💰 課金予定設定: {marked_count}個のコンテンツが次回請求時に課金予定になりました")
                    if marked_details:
                        status_lines.append("対象コンテンツ:")
                        for detail in marked_details:
                            status_lines.append(f"  • {detail}")
                    status_lines.append("")
            elif auto_charge_result.get('status') == 'success':
                charged_count = auto_charge_result.get('charged_count', 0)
                charged_details = auto_charge_result.get('charged_details', [])
                if charged_count > 0:
                    status_lines.append(f"💰 自動課金完了: {charged_count}個のコンテンツが有料に変更されました")
                    if charged_details:
                        status_lines.append("対象コンテンツ:")
                        for detail in charged_details:
                            status_lines.append(f"  • {detail}")
                    status_lines.append("")
        
        # サブスクリプション状態を追加
        if subscription_status['is_active']:
            if subscription_status['cancel_at_period_end']:
                status_lines.append("🔴 サブスクリプション: 期間終了時に解約予定")
            else:
                status_lines.append("🟢 サブスクリプション: 有効")
        else:
            if subscription_status['status'] == 'canceled':
                status_lines.append("🔴 サブスクリプション: 解約済み")
            else:
                status_lines.append("🔴 サブスクリプション: 無効")
        
        # 料金体系の情報を追加
        status_lines.append("")
        if is_trial_period:
            status_lines.append("💰 料金体系（トライアル期間中）:")
            status_lines.append("• 1個目: 無料")
            status_lines.append("• 2個目以降: 1,500円/件（月額料金に追加）")
        else:
            status_lines.append("💰 料金体系:")
            status_lines.append("• 1個目: 無料")
            status_lines.append("• 2個目以降: 1,500円/件（月額料金に追加）")
        
        status_lines.append("")  # 空行
        
        if not usage_logs:
            status_lines.append("📈 今月の追加回数：0回")
            status_lines.append("💰 追加料金：0円")
            status_lines.append("")
            status_lines.append("💡 ヒント：")
            status_lines.append("• 「追加」でコンテンツを追加")
            status_lines.append("• 「メニュー」で機能一覧を確認")
        else:
            total_cost = 0
            content_list = []
            
            # 実際の追加回数（重複を含む）を計算
            actual_count = len(usage_logs)
            
            for log in usage_logs:
                content_type = log[0] or "不明"
                is_free = log[1]
                created_at = log[2]
                if not is_free:
                    total_cost += 1500
                # 日付を簡潔に表示（YYYY-MM-DD形式）
                date_str = created_at.strftime('%Y-%m-%d')
                content_list.append(f"• {content_type} ({'無料' if is_free else '1,500円'}) - {date_str}")
            
            status_lines.append(f"📈 今月の追加回数：{actual_count}回")
            status_lines.append(f"💰 追加料金：{total_cost:,}円")
            
            # 次回追加時の料金予告
            next_count = actual_count + 1
            if next_count == 1:
                next_price = "無料"
            else:
                next_price = "1,500円（月額料金に追加）"
            status_lines.append(f"📝 次回追加時（{next_count}個目）: {next_price}")
            
            status_lines.append("")
            status_lines.append("📚 追加済みコンテンツ：")
            status_lines.extend(content_list[:5])  # 最新5件まで表示
            status_lines.append("")
            status_lines.append("💡 ヒント：")
            status_lines.append("• 「追加」でコンテンツを追加")
            status_lines.append("• 「メニュー」で機能一覧を確認")
        
        status_message = "\n".join(status_lines)
        send_line_message(reply_token, [{"type": "text", "text": status_message}])
    except Exception as e:
        print(f'利用状況確認エラー: {e}')
        import traceback
        traceback.print_exc()
        send_line_message(reply_token, [{"type": "text", "text": "❌ 利用状況の取得に失敗しました。しばらく時間をおいて再度お試しください。"}])

def handle_cancel_request(reply_token, user_id_db, stripe_subscription_id):
    try:
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        items = subscription['items']['data']
        
        # サブスクリプション状態をチェック
        subscription_status = check_subscription_status(stripe_subscription_id)
        is_trial_period = subscription_status.get('subscription', {}).get('status') == 'trialing'
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 実際に追加されたコンテンツを取得
        c.execute('SELECT content_type, is_free FROM usage_logs WHERE user_id = %s ORDER BY created_at', (user_id_db,))
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
                content_choices.append(f"{choice_index}. {content_type}（{display_price}）")
                print(f'[DEBUG] 解約選択肢: {choice_index}. {content_type}（{display_price}）')
                choice_index += 1
        
        if not content_choices:
            # コンテンツが存在しない場合のメッセージを改善
            no_content_message = {
                "type": "template",
                "altText": "契約中コンテンツなし",
                "template": {
                    "type": "buttons",
                    "title": "契約中コンテンツなし",
                    "text": "現在契約中のコンテンツはありません。\n\nコンテンツを追加してから解約してください。",
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
        
        choice_message = "\n".join(content_choices)
        send_line_message(reply_token, [{"type": "text", "text": f"解約したいコンテンツを選んでください（AI対応：様々な形式で入力可能）:\n{choice_message}\n\n対応形式:\n• 1,2,3 (カンマ区切り)\n• 1.2.3 (ドット区切り)\n• 1 2 3 (スペース区切り)\n• 一二三 (日本語数字)\n• 1番目,2番目 (序数表現)\n• 最初,二番目 (日本語序数)"}])
    except Exception as e:
        send_line_message(reply_token, [{"type": "text", "text": "❌ 契約中コンテンツの取得に失敗しました。しばらく時間をおいて再度お試しください。"}])

def handle_cancel_selection(reply_token, user_id_db, stripe_subscription_id, selection_text):
    try:
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        items = subscription['items']['data']
        
        # 実際に追加されたコンテンツを取得
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT id, content_type, is_free FROM usage_logs WHERE user_id = %s ORDER BY created_at', (user_id_db,))
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
        
        cancelled = []
        choice_index = 1
        
        # 実際に追加されたコンテンツの処理
        for usage_id, content_type, is_free in added_contents:
            if content_type in ['AI予定秘書', 'AI経理秘書', 'AIタスクコンシェルジュ']:
                print(f'[DEBUG] 処理中: choice_index={choice_index}, content_type={content_type}, usage_id={usage_id}')
                if choice_index in selected_indices:
                    # データベースからusage_logsを削除
                    c.execute('DELETE FROM usage_logs WHERE id = %s', (usage_id,))
                    cancelled.append(content_type)
                    print(f'[DEBUG] 解約処理: content_type={content_type}, usage_id={usage_id}')
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
            
            cancel_success_message = {
                "type": "template",
                "altText": "コンテンツ解約完了",
                "template": {
                    "type": "buttons",
                    "title": "コンテンツ解約完了",
                    "text": f"以下のコンテンツの解約を受け付けました：\n" + "\n".join(cancelled),
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
            send_line_message(reply_token, [cancel_success_message])
            
            # 請求期間についての説明を別メッセージで送信
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
            send_line_message(reply_token, [period_message])
            
            # ユーザー状態をリセット
            from models.user_state import clear_user_state
            line_user_id = None
            # LINEユーザーIDを取得
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT line_user_id FROM users WHERE id = %s', (user_id_db,))
            result = c.fetchone()
            conn.close()
            if result and result[0]:
                line_user_id = result[0]
                clear_user_state(line_user_id)
                print(f'[DEBUG] ユーザー状態リセット: {line_user_id}')
        else:
            send_line_message(reply_token, [{"type": "text", "text": "有効な番号が選択されませんでした。もう一度お試しください。"}])
    except Exception as e:
        print(f'[ERROR] 解約処理エラー: {e}')
        import traceback
        traceback.print_exc()
        send_line_message(reply_token, [{"type": "text", "text": "❌ 解約処理に失敗しました。しばらく時間をおいて再度お試しください。"}])

def handle_subscription_cancel(reply_token, user_id_db, stripe_subscription_id):
    """サブスクリプション全体を解約"""
    try:
        import datetime
        
        # サブスクリプション状態をチェック
        subscription_status = check_subscription_status(stripe_subscription_id)
        is_trial_period = subscription_status.get('subscription', {}).get('status') == 'trialing'
        
        if is_trial_period:
            # トライアル期間中は即時解約
            subscription = stripe.Subscription.modify(
                stripe_subscription_id,
                cancel_at_period_end=False
            )
            subscription = stripe.Subscription.cancel(stripe_subscription_id)
            cancel_message_text = "サブスクリプション全体の解約を受け付けました。\n\nトライアル期間中のため、即座に解約されます。"
        else:
            # 通常期間は期間終了時に解約予定
            subscription = stripe.Subscription.modify(
                stripe_subscription_id,
                cancel_at_period_end=True
            )
            cancel_message_text = "サブスクリプション全体の解約を受け付けました。\n\n請求期間終了まで全てのサービスをご利用いただけます。"
        
        # 1週間以内に追加された課金予定のコンテンツをキャンセル
        one_week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        conn = get_db_connection()
        c = conn.cursor()
        
        # 1週間以内の課金予定コンテンツを取得
        c.execute('''
            SELECT id, content_type, created_at 
            FROM usage_logs 
            WHERE user_id = %s AND pending_charge = TRUE AND created_at > %s
        ''', (user_id_db, one_week_ago))
        recent_pending = c.fetchall()
        
        # 1週間以内の課金予定をキャンセル（pending_chargeをFalseに設定）
        c.execute('''
            UPDATE usage_logs 
            SET pending_charge = FALSE 
            WHERE user_id = %s AND pending_charge = TRUE AND created_at > %s
        ''', (user_id_db, one_week_ago))
        cancelled_count = c.rowcount
        
        # 1週間以上前のコンテンツは削除
        c.execute('DELETE FROM usage_logs WHERE user_id = %s AND created_at <= %s', (user_id_db, one_week_ago))
        deleted_count = c.rowcount
        
        conn.commit()
        conn.close()
        
        print(f'[DEBUG] 解約処理: user_id={user_id_db}, cancelled_count={cancelled_count}, deleted_count={deleted_count}, is_trial={is_trial_period}')
        
        # キャンセルされたコンテンツの情報をメッセージに追加
        if cancelled_count > 0:
            cancel_message_text += f"\n\n1週間以内に追加された{cancelled_count}個のコンテンツの課金がキャンセルされました。"
        
        print(f'[DEBUG] サブスクリプション解約: user_id={user_id_db}, deleted_count={deleted_count}, is_trial={is_trial_period}')
        
        # 解約確認メッセージを送信
        cancel_message = {
            "type": "template",
            "altText": "サブスクリプション解約完了",
            "template": {
                "type": "buttons",
                "title": "サブスクリプション解約完了",
                "text": cancel_message_text,
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
        print(f'[ERROR] サブスクリプション解約エラー: {e}')
        import traceback
        traceback.print_exc()
        send_line_message(reply_token, [{"type": "text", "text": "❌ サブスクリプション解約に失敗しました。しばらく時間をおいて再度お試しください。"}])

def handle_cancel_menu(reply_token, user_id_db, stripe_subscription_id):
    """解約メニューを表示"""
    try:
        # サブスクリプション状態をチェック
        subscription_status = check_subscription_status(stripe_subscription_id)
        
        if not subscription_status['is_active']:
            if subscription_status['status'] == 'canceled':
                # サブスクリプションが解約済み
                payment_message = {
                    "type": "template",
                    "altText": "サブスクリプション解約済み",
                    "template": {
                        "type": "buttons",
                        "title": "サブスクリプション解約済み",
                        "text": "サブスクリプションが解約されています。\n\n新しいサブスクリプションを開始してください。",
                        "actions": [
                            {
                                "type": "uri",
                                "label": "決済画面へ",
                                "uri": "https://lp-production-9e2c.up.railway.app"
                            }
                        ]
                    }
                }
                send_line_message(reply_token, [payment_message])
                return
            elif subscription_status['cancel_at_period_end']:
                # 期間終了時に解約予定
                payment_message = {
                    "type": "template",
                    "altText": "サブスクリプション解約予定",
                    "template": {
                        "type": "buttons",
                        "title": "サブスクリプション解約予定",
                        "text": "サブスクリプションが期間終了時に解約予定です。\n\nサブスクリプションを更新してください。",
                        "actions": [
                            {
                                "type": "uri",
                                "label": "決済画面へ",
                                "uri": "https://lp-production-9e2c.up.railway.app"
                            }
                        ]
                    }
                }
                send_line_message(reply_token, [payment_message])
                return
            else:
                # その他の無効な状態
                payment_message = {
                    "type": "template",
                    "altText": "サブスクリプション無効",
                    "template": {
                        "type": "buttons",
                        "title": "サブスクリプション無効",
                        "text": "サブスクリプションが無効な状態です。\n\n有効なサブスクリプションが必要です。",
                        "actions": [
                            {
                                "type": "uri",
                                "label": "決済画面へ",
                                "uri": "https://lp-production-9e2c.up.railway.app"
                            }
                        ]
                    }
                }
                send_line_message(reply_token, [payment_message])
                return
        
        # サブスクリプションが有効な場合、通常の解約メニューを表示
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

def get_welcome_message():
    return "ようこそ！LINE連携が完了しました。"

def get_not_registered_message():
    return "ご登録情報が見つかりません。LPからご登録ください。" 

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
    
    # 日本語数字を検索
    for japanese, arabic in japanese_numbers.items():
        if japanese in text:
            numbers.append(str(arabic))
    
    # 漢数字の複合表現（二十一、二十二など）
    for i in range(21, 31):
        japanese = f"二十{['', '一', '二', '三', '四', '五', '六', '七', '八', '九'][i % 10]}"
        if japanese in text:
            numbers.append(str(i))
    
    # 全角数字の対応
    fullwidth_numbers = {
        '０': '0', '１': '1', '２': '2', '３': '3', '４': '4',
        '５': '5', '６': '6', '７': '7', '８': '8', '９': '9'
    }
    
    for fullwidth, halfwidth in fullwidth_numbers.items():
        if fullwidth in text:
            numbers.append(halfwidth)
    
    # 英語の数字表現
    english_numbers = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
    }
    
    text_lower = text.lower()
    for english, arabic in english_numbers.items():
        if english in text_lower:
            numbers.append(str(arabic))
    
    # 重複を除去してソート
    unique_numbers = list(set(numbers))
    unique_numbers.sort(key=lambda x: int(x))
    
    return unique_numbers

def validate_selection_numbers(numbers, max_count):
    """選択された数字が有効かチェック（AI技術を活用）"""
    valid_numbers = []
    invalid_reasons = []
    
    for num in numbers:
        try:
            num_int = int(num)
            if 1 <= num_int <= max_count:
                valid_numbers.append(num_int)
            else:
                invalid_reasons.append(f'{num_int} (範囲外: 1-{max_count})')
                print(f'[DEBUG] 無効な番号: {num_int} (範囲外: 1-{max_count})')
        except ValueError:
            invalid_reasons.append(f'{num} (無効な数字形式)')
            print(f'[DEBUG] 無効な数字形式: {num}')
    
    # 重複チェック
    duplicates = []
    seen = set()
    for num in valid_numbers:
        if num in seen:
            duplicates.append(num)
        else:
            seen.add(num)
    
    if duplicates:
        print(f'[DEBUG] 重複した番号: {duplicates}')
        # 重複を除去
        valid_numbers = list(seen)
    
    return valid_numbers, invalid_reasons, duplicates

def smart_number_extraction(text):
    """AI技術を活用したスマートな数字抽出"""
    # 基本的な数字抽出
    numbers = extract_numbers_from_text(text)
    
    # 文脈を考慮した数字抽出
    # 「1番目」「2番目」などの表現に対応
    import re
    ordinal_patterns = [
        r'(\d+)番目',
        r'(\d+)つ目',
        r'(\d+)個目',
        r'(\d+)つめ',
        r'(\d+)個め'
    ]
    
    for pattern in ordinal_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if match not in numbers:
                numbers.append(match)
    
    # 「最初」「二番目」などの表現に対応
    ordinal_japanese = {
        '最初': '1', '一番目': '1', '一つ目': '1', '一個目': '1',
        '二番目': '2', '二つ目': '2', '二個目': '2',
        '三番目': '3', '三つ目': '3', '三個目': '3',
        '四番目': '4', '四つ目': '4', '四個目': '4',
        '五番目': '5', '五つ目': '5', '五個目': '5'
    }
    
    for japanese, arabic in ordinal_japanese.items():
        if japanese in text and arabic not in numbers:
            numbers.append(arabic)
    
    # 重複を除去してソート
    unique_numbers = list(set(numbers))
    unique_numbers.sort(key=lambda x: int(x))
    
    return unique_numbers

def process_pending_charges(user_id_db, stripe_subscription_id):
    """1週間後に課金予定のコンテンツを実際に課金する"""
    try:
        import datetime
        
        # 1週間前の日時を計算
        one_week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        
        # データベースから1週間前に追加された課金予定のコンテンツを取得
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            SELECT id, content_type, created_at 
            FROM usage_logs 
            WHERE user_id = %s AND pending_charge = TRUE AND created_at <= %s
            ORDER BY created_at ASC
        ''', (user_id_db, one_week_ago))
        pending_charges = c.fetchall()
        conn.close()
        
        if not pending_charges:
            return {"status": "no_pending", "message": "課金予定のコンテンツがありません"}
        
        print(f'[DEBUG] 実際の課金対象: {len(pending_charges)}個のコンテンツ')
        for charge in pending_charges:
            print(f'[DEBUG] 課金実行: {charge[1]}')
        
        # Stripeで課金処理
        try:
            # stripe.api_keyはapp.pyで既に設定済み
            
            subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            
            # 従量課金アイテムを取得（¥1,500の従量課金）
            usage_item = None
            for item in subscription['items']['data']:
                if item['price']['id'] == 'price_1Rog1nIxg6C5hAVdnqB5MJiT':  # ¥1,500の従量課金Price ID
                    usage_item = item
                    break
            
            # 従量課金アイテムが見つからない場合は、使用量が記録されているアイテムを使用
            if not usage_item:
                for item in subscription['items']['data']:
                    usage_records = stripe.SubscriptionItem.list_usage_record_summaries(
                        item['id'],
                        limit=1
                    )
                    if usage_records.data and usage_records.data[0].total_usage > 0:
                        usage_item = item
                        print(f'[WARN] 従量課金アイテムが見つからないため、使用量が記録されているアイテムを使用: {item["id"]}')
                        break
            
            if not usage_item:
                return {"status": "error", "message": "従量課金アイテムが見つかりません"}
            
            # 各コンテンツに対して課金
            total_charged = 0
            charged_details = []
            conn = get_db_connection()
            c = conn.cursor()
            
            for charge in pending_charges:
                log_id, content_type, created_at = charge
                try:
                    # Stripeの使用量記録を作成
                    usage_record = stripe.SubscriptionItem.create_usage_record(
                        usage_item['id'],
                        quantity=1,
                        timestamp=int(created_at.timestamp()),
                        action='increment'
                    )
                    
                    # データベースを更新
                    c.execute('''
                        UPDATE usage_logs 
                        SET is_free = FALSE, pending_charge = FALSE, stripe_usage_record_id = %s 
                        WHERE id = %s
                    ''', (usage_record.id, log_id))
                    
                    total_charged += 1
                    charged_details.append(content_type)
                    print(f'[DEBUG] 課金完了: {content_type}, usage_record_id={usage_record.id}')
                    
                except Exception as e:
                    print(f'[DEBUG] 課金エラー: {content_type}, error={e}')
                    continue
            
            conn.commit()
            conn.close()
            
            return {
                "status": "success", 
                "message": f"{total_charged}個のコンテンツを課金しました",
                "charged_count": total_charged,
                "charged_details": charged_details
            }
            
        except Exception as e:
            print(f'[DEBUG] Stripe課金エラー: {e}')
            return {"status": "stripe_error", "message": f"Stripe課金エラー: {str(e)}"}
            
    except Exception as e:
        print(f'[DEBUG] 課金処理エラー: {e}')
        return {"status": "error", "message": f"課金処理でエラーが発生しました: {e}"}