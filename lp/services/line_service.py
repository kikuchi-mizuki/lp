import requests
import sqlite3
import psycopg2
import os
import stripe
import traceback
import time
from utils.db import get_db_connection

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
                "text": "ようこそ！AIコレクションズへ\n\nAIコレクションズサービスをご利用いただき、ありがとうございます。\n\n📋 サービス内容：\n• AI予定秘書：スケジュール管理\n• AI経理秘書：請求書作成\n• AIタスクコンシェルジュ：タスク管理\n\n💰 料金体系：\n• 月額基本料金：3,900円\n• 追加コンテンツ：1個目無料、2個目以降1,500円/件\n\n下のボタンからお選びください。"
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
                            "label": "使い方を見る",
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

def handle_add_content(reply_token, user_id_db, stripe_subscription_id):
    try:
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
        send_line_message(reply_token, [{"type": "text", "text": "エラーが発生しました。しばらく時間をおいて再度お試しください。"}])

def handle_content_selection(reply_token, user_id_db, stripe_subscription_id, content_number):
    try:
        content_info = {
            '1': {
                'name': 'AI予定秘書',
                'price': 1500,
                'description': '日程調整のストレスから解放される、スケジュール管理の相棒',
                'usage': 'Googleカレンダーと連携し、LINEで予定の追加・確認・空き時間の提案まで。調整のやりとりに追われる時間を、もっとクリエイティブに使えるように。',
                'url': 'https://lp-production-9e2c.up.railway.app/schedule'
            },
            '2': {
                'name': 'AI経理秘書',
                'price': 1500,
                'description': '打合せ後すぐ送れる、スマートな請求書作成アシスタント',
                'usage': 'LINEで項目を送るだけで、見積書や請求書を即作成。営業から事務処理までを一気通貫でスムーズに。',
                'url': 'https://lp-production-9e2c.up.railway.app/accounting'
            },
            '3': {
                'name': 'AIタスクコンシェルジュ',
                'price': 1500,
                'description': '今日やるべきことを、ベストなタイミングで',
                'usage': '登録したタスクを空き時間に自動で配置し、理想的な1日をAIが提案。「やりたいのにできない」を、「自然にこなせる」毎日に。',
                'url': 'https://lp-production-9e2c.up.railway.app/task'
            }
        }
        if content_number not in content_info:
            send_line_message(reply_token, [{"type": "text", "text": "無効な選択です。1-3の数字で選択してください。"}])
            return
        content = content_info[content_number]
        # 全コンテンツの合計数を取得
        conn_count = get_db_connection()
        c_count = conn_count.cursor()
        c_count.execute('SELECT COUNT(*) FROM usage_logs WHERE user_id = %s', (user_id_db,))
        total_usage_count = c_count.fetchone()[0]
        # 同じコンテンツの追加回数を確認
        c_count.execute('SELECT COUNT(*) FROM usage_logs WHERE user_id = %s AND content_type = %s', (user_id_db, content['name']))
        same_content_count = c_count.fetchone()[0]
        conn_count.close()
        
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
        
        is_free = total_usage_count == 0
        price_message = "料金：無料（1個目）" if is_free else f"料金：1,500円（{total_usage_count + 1}個目）"
        confirm_message = {
            "type": "template",
            "altText": "選択内容の確認",
            "template": {
                "type": "buttons",
                "title": "選択内容の確認",
                "text": f"コンテンツ：{content['name']}\n{price_message}\n\nこのコンテンツを追加しますか？",
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
        content_info = {
            '1': {
                'name': 'AI予定秘書',
                'price': 1500,
                'description': '日程調整のストレスから解放される、スケジュール管理の相棒',
                'usage': 'Googleカレンダーと連携し、LINEで予定の追加・確認・空き時間の提案まで。調整のやりとりに追われる時間を、もっとクリエイティブに使えるように。',
                'url': 'https://lp-production-9e2c.up.railway.app/schedule'
            },
            '2': {
                'name': 'AI経理秘書',
                'price': 1500,
                'description': '打合せ後すぐ送れる、スマートな請求書作成アシスタント',
                'usage': 'LINEで項目を送るだけで、見積書や請求書を即作成。営業から事務処理までを一気通貫でスムーズに。',
                'url': 'https://lp-production-9e2c.up.railway.app/accounting'
            },
            '3': {
                'name': 'AIタスクコンシェルジュ',
                'price': 1500,
                'description': '今日やるべきことを、ベストなタイミングで',
                'usage': '登録したタスクを空き時間に自動で配置し、理想的な1日をAIが提案。「やりたいのにできない」を、「自然にこなせる」毎日に。',
                'url': 'https://lp-production-9e2c.up.railway.app/task'
            }
        }
        content = content_info[content_number]
        # usage_logsから再度カウントしてis_freeを決定
        conn_count = get_db_connection()
        c_count = conn_count.cursor()
        # 全コンテンツの合計数を取得
        c_count.execute('SELECT COUNT(*) FROM usage_logs WHERE user_id = %s', (user_id_db,))
        total_usage_count = c_count.fetchone()[0]
        # 同じコンテンツの追加回数を確認
        c_count.execute('SELECT COUNT(*) FROM usage_logs WHERE user_id = %s AND content_type = %s', (user_id_db, content['name']))
        same_content_count = c_count.fetchone()[0]
        conn_count.close()
        
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
        
        is_free = total_usage_count == 0
        price_message = "料金：無料（1個目）" if is_free else f"料金：1,500円（{total_usage_count + 1}個目）"
        print(f"[DEBUG] content_type: {content['name']}")
        print(f"[DEBUG] DATABASE_URL: {os.getenv('DATABASE_URL')}")
        print(f"[DEBUG] total_usage_count: {total_usage_count}")
        print(f"[DEBUG] is_free: {is_free}")
        
        # 無料の場合はデータベースにのみ記録
        if is_free:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('''
                INSERT INTO usage_logs (user_id, usage_quantity, stripe_usage_record_id, is_free, content_type)
                VALUES (%s, %s, %s, %s, %s)
            ''', (user_id_db, 1, None, is_free, content['name']))
            conn.commit()
            conn.close()
            print(f'DB登録成功: user_id={user_id_db}, is_free={is_free}, usage_record_id=None')
        else:
            # 有料の場合はStripeの使用量記録も作成
            print('[DEBUG] Stripe課金API呼び出し開始')
            try:
                subscription = stripe.Subscription.retrieve(stripe_subscription_id)
                
                # サブスクリプションの状態をチェック
                if subscription['status'] == 'canceled':
                    cancel_message = {
                        "type": "template",
                        "altText": "サブスクリプション更新が必要です",
                        "template": {
                            "type": "buttons",
                            "title": "サブスクリプション更新が必要です",
                            "text": "現在のサブスクリプションがキャンセルされています。新しいサブスクリプションを作成するか、既存のものを復活させてください。",
                            "actions": [
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
                    send_line_message(reply_token, [cancel_message])
                    return
                
                usage_item = None
                for item in subscription['items']['data']:
                    print(f'[DEBUG] Stripe item: {item}')
                    if item['price']['id'] == os.getenv('STRIPE_USAGE_PRICE_ID'):
                        usage_item = item
                        break
                if not usage_item:
                    print('[DEBUG] usage_itemが見つからずreturn')
                    send_line_message(reply_token, [{"type": "text", "text": f"❌ 従量課金アイテムが見つかりません。\n\n設定されている価格ID: {os.getenv('STRIPE_USAGE_PRICE_ID')}\n\nサポートにお問い合わせください。"}])
                    return
            except Exception as subscription_error:
                print(f'[DEBUG] サブスクリプション取得エラー: {subscription_error}')
                error_str = str(subscription_error)
                if "subscription has been canceled" in error_str or "No such subscription" in error_str:
                    cancel_message = {
                        "type": "template",
                        "altText": "サブスクリプション更新が必要です",
                        "template": {
                            "type": "buttons",
                            "title": "サブスクリプション更新が必要です",
                            "text": "現在のサブスクリプションがキャンセルされています。新しいサブスクリプションを作成してください。",
                            "actions": [
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
                    send_line_message(reply_token, [cancel_message])
                else:
                    send_line_message(reply_token, [{"type": "text", "text": f"❌ サブスクリプションの取得に失敗しました。\n\nエラー: {error_str}"}])
                return
            subscription_item_id = usage_item['id']
            try:
                # 従量課金の使用量を記録
                try:
                    # 既存のSubscription Itemを使用して使用量を記録
                    usage_record = stripe.UsageRecord.create(
                        subscription_item=subscription_item_id,
                        quantity=1,
                        timestamp=int(time.time()),
                        action='increment'
                    )
                    print(f"使用量記録作成成功: {usage_record.id}")
                    
                    # usage_logsに記録
                    conn = get_db_connection()
                    c = conn.cursor()
                    c.execute('''
                        INSERT INTO usage_logs (user_id, usage_quantity, stripe_usage_record_id, is_free, content_type)
                        VALUES (%s, %s, %s, %s, %s)
                    ''', (user_id_db, 1, usage_record.id, is_free, content['name']))
                    conn.commit()
                    conn.close()
                    print(f'DB登録成功: user_id={user_id_db}, is_free={is_free}, usage_record_id={usage_record.id}')
                except stripe.error.StripeError as e:
                    print(f"使用量記録作成エラー: {e}")
                    # エラーが発生してもusage_logsには記録
                    conn = get_db_connection()
                    c = conn.cursor()
                    c.execute('''
                        INSERT INTO usage_logs (user_id, usage_quantity, stripe_usage_record_id, is_free, content_type)
                        VALUES (%s, %s, %s, %s, %s)
                    ''', (user_id_db, 1, None, is_free, content['name']))
                    conn.commit()
                    conn.close()
                    print(f'DB登録成功（エラー時）: user_id={user_id_db}, is_free={is_free}, usage_record_id=None')
            except Exception as usage_error:
                print(f'[DEBUG] 使用量記録作成例外: {usage_error}')
                import traceback
                print(traceback.format_exc())
                
                # エラーが発生してもusage_logsには記録
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('''
                    INSERT INTO usage_logs (user_id, usage_quantity, stripe_usage_record_id, is_free, content_type)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (user_id_db, 1, None, is_free, content['name']))
                conn.commit()
                conn.close()
                print(f'DB登録成功（例外時）: user_id={user_id_db}, is_free={is_free}, usage_record_id=None')
        # usage_logsの全件を出力
        try:
            conn_debug = get_db_connection()
            c_debug = conn_debug.cursor()
            c_debug.execute('SELECT id, user_id, is_free, content_type, created_at FROM usage_logs ORDER BY created_at DESC LIMIT 10')
            logs = c_debug.fetchall()
            print('[DEBUG] usage_logs 最新10件:')
            for log in logs:
                print(log)
            # 追加: 同じuser_id・content_typeの全レコードを出力
            c_debug.execute('SELECT id, user_id, is_free, content_type, created_at FROM usage_logs WHERE user_id = %s AND content_type = %s ORDER BY created_at DESC', (user_id_db, content['name']))
            same_content_logs = c_debug.fetchall()
            print(f'[DEBUG] user_id={user_id_db}, content_type={content["name"]} のusage_logs:')
            for log in same_content_logs:
                print(log)
            conn_debug.close()
        except Exception as e:
            print(f'[DEBUG] usage_logs全件取得エラー: {e}')
        if is_free:
            success_message = {
                "type": "text",
                "text": f"コンテンツ追加完了！\n\n追加内容：{content['name']}\n料金：無料（1個目）\n\nアクセスURL：\n{content['url']}\n\n他のコンテンツも追加できます。"
            }
        else:
            success_message = {
                "type": "text",
                "text": f"コンテンツ追加完了！\n\n追加内容：{content['name']}\n料金：1,500円（{total_usage_count + 1}個目、次回請求時に反映）\n\nアクセスURL：\n{content['url']}\n\n他のコンテンツも追加できます。"
            }
        send_line_message(reply_token, [success_message])
    except Exception as e:
        send_line_message(reply_token, [{"type": "text", "text": "❌ エラーが発生しました。しばらく時間をおいて再度お試しください。"}])

def handle_status_check(reply_token, user_id_db):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT content_type, is_free, created_at FROM usage_logs WHERE user_id = %s ORDER BY created_at DESC', (user_id_db,))
        usage_logs = c.fetchall()
        conn.close()
        if not usage_logs:
            status_message = """📊 利用状況

📈 今月の追加回数：0回
💰 追加料金：0円

💡 ヒント：
• 「追加」でコンテンツを追加
• 「メニュー」で機能一覧を確認"""
        else:
            total_cost = 0
            content_list = []
            for log in usage_logs:
                content_type = log[0] or "不明"
                is_free = log[1]
                created_at = log[2]
                if not is_free:
                    total_cost += 1500
                content_list.append(f"• {content_type} ({'無料' if is_free else '1,500円'}) - {created_at}")
            status_message = f"""📊 利用状況

📈 今月の追加回数：{len(usage_logs)}回
💰 追加料金：{total_cost:,}円

📚 追加済みコンテンツ：
{chr(10).join(content_list[:5])}  # 最新5件まで表示

💡 ヒント：
• 「追加」でコンテンツを追加
• 「メニュー」で機能一覧を確認"""
        send_line_message(reply_token, [{"type": "text", "text": status_message}])
    except Exception as e:
        send_line_message(reply_token, [{"type": "text", "text": "❌ 利用状況の取得に失敗しました。しばらく時間をおいて再度お試しください。"}])

def handle_cancel_request(reply_token, user_id_db, stripe_subscription_id):
    try:
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        items = subscription['items']['data']
        conn = get_db_connection()
        c = conn.cursor()
        
        # 実際に追加されたコンテンツを取得
        c.execute('SELECT content_type, is_free FROM usage_logs WHERE user_id = %s ORDER BY created_at', (user_id_db,))
        added_contents = c.fetchall()
        conn.close()
        
        content_choices = []
        choice_index = 1
        
        # 実際に追加されたコンテンツのみを表示
        for content_type, is_free in added_contents:
            if content_type in ['AI予定秘書', 'AI経理秘書', 'AIタスクコンシェルジュ']:
                display_price = '0円' if is_free else '1,500円'
                content_choices.append(f"{choice_index}. {content_type}（{display_price}/件）")
                print(f'[DEBUG] 解約選択肢: {choice_index}. {content_type}（{display_price}/件）')
                choice_index += 1
        
        if not content_choices:
            send_line_message(reply_token, [{"type": "text", "text": "現在契約中のコンテンツはありません。"}])
            return
        
        choice_message = "\n".join(content_choices)
        send_line_message(reply_token, [{"type": "text", "text": f"解約したいコンテンツを選んでください（カンマ区切りで複数選択可）:\n{choice_message}\n\n例: 1,2"}])
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
        
        # 選択された番号を解析
        selected_indices = [int(x.strip()) for x in selection_text.split(',') if x.strip().isdigit()]
        
        cancelled = []
        choice_index = 1
        
        # 実際に追加されたコンテンツの処理
        for usage_id, content_type, is_free in added_contents:
            if content_type in ['AI予定秘書', 'AI経理秘書', 'AIタスクコンシェルジュ']:
                if choice_index in selected_indices:
                    # データベースからusage_logsを削除
                    c.execute('DELETE FROM usage_logs WHERE id = %s', (usage_id,))
                    cancelled.append(content_type)
                    print(f'[DEBUG] 解約処理: content_type={content_type}, usage_id={usage_id}')
                choice_index += 1
        
        # データベースの変更をコミット
        conn.commit()
        conn.close()
        
        if cancelled:
            send_line_message(reply_token, [{"type": "text", "text": f"以下のコンテンツの解約を受け付けました（請求期間終了まで利用可能です）：\n" + "\n".join(cancelled)}])
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
        # サブスクリプションをキャンセル
        subscription = stripe.Subscription.modify(
            stripe_subscription_id,
            cancel_at_period_end=True
        )
        
        # 解約確認メッセージを送信
        cancel_message = {
            "type": "template",
            "altText": "サブスクリプション解約完了",
            "template": {
                "type": "buttons",
                "title": "サブスクリプション解約完了",
                "text": "サブスクリプション全体の解約を受け付けました。\n\n請求期間終了まで全てのサービスをご利用いただけます。\n\n解約をキャンセルする場合は、お問い合わせください。",
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
        send_line_message(reply_token, [{"type": "text", "text": "❌ サブスクリプション解約に失敗しました。しばらく時間をおいて再度お試しください。"}])

def handle_cancel_menu(reply_token, user_id_db, stripe_subscription_id):
    """解約メニューを表示"""
    try:
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
        send_line_message(reply_token, [{"type": "text", "text": "❌ 解約メニューの表示に失敗しました。しばらく時間をおいて再度お試しください。"}])

def get_welcome_message():
    return "ようこそ！LINE連携が完了しました。"

def get_not_registered_message():
    return "ご登録情報が見つかりません。LPからご登録ください。" 