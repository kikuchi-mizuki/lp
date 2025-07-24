import requests
import sqlite3
import psycopg2
import os
import stripe

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

# LINE関連のサービス層

def send_line_message(reply_token, message):
    """LINEメッセージ送信（実装はapp.pyから移動予定）"""
    pass

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
    headers = {
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
        'Content-Type': 'image/png'
    }
    with open(image_path, 'rb') as f:
        response = requests.post(f'https://api.line.me/v2/bot/richmenu/{rich_menu_id}/content', headers=headers, data=f)
    response.raise_for_status()

def set_default_rich_menu(rich_menu_id):
    headers = {
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
    }
    response = requests.post(f'https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}', headers=headers)
    response.raise_for_status()

def delete_all_rich_menus():
    headers = {
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
    }
    response = requests.get('https://api.line.me/v2/bot/richmenu/list', headers=headers)
    response.raise_for_status()
    for rm in response.json().get('richmenus', []):
        requests.delete(f'https://api.line.me/v2/bot/richmenu/{rm["richMenuId"]}', headers=headers)

def setup_rich_menu():
    delete_all_rich_menus()
    rich_menu_id = create_rich_menu()
    set_rich_menu_image(rich_menu_id)
    set_default_rich_menu(rich_menu_id)
    return rich_menu_id 

def get_db_connection():
    DATABASE_URL = os.getenv('DATABASE_URL', 'database.db')
    if DATABASE_URL.startswith('postgresql://'):
        return psycopg2.connect(DATABASE_URL)
    else:
        return sqlite3.connect(DATABASE_URL)

def handle_add_content(reply_token, user_id_db, stripe_subscription_id):
    try:
        content_menu = """📚 コンテンツ選択メニュー

利用可能なコンテンツを選択してください：

1️⃣ **AI秘書機能**
   💰 料金：1,500円（1個目は無料）
   📝 内容：24時間対応のAI秘書

2️⃣ **会計管理ツール**
   💰 料金：1,500円（1個目は無料）
   📝 内容：自動会計・経費管理

3️⃣ **スケジュール管理**
   💰 料金：1,500円（1個目は無料）
   📝 内容：AIによる最適スケジュール

4️⃣ **タスク管理**
   💰 料金：1,500円（1個目は無料）
   📝 内容：プロジェクト管理・進捗追跡

選択するには：
• 「1」- AI秘書機能
• 「2」- 会計管理ツール
• 「3」- スケジュール管理
• 「4」- タスク管理

または、番号を直接入力してください。"""
        send_line_message(reply_token, content_menu)
    except Exception as e:
        print(f'コンテンツ選択メニューエラー: {e}')
        send_line_message(reply_token, "❌ エラーが発生しました。しばらく時間をおいて再度お試しください。")

def handle_content_selection(reply_token, user_id_db, stripe_subscription_id, content_number):
    try:
        content_info = {
            '1': {
                'name': 'AI秘書機能',
                'price': 1500,
                'description': '24時間対応のAI秘書',
                'usage': 'LINEで直接メッセージを送るだけで、予定管理、メール作成、リマインダー設定などができます。',
                'url': 'https://lp-production-9e2c.up.railway.app/secretary'
            },
            '2': {
                'name': '会計管理ツール',
                'price': 1500,
                'description': '自動会計・経費管理',
                'usage': 'レシートを撮影するだけで自動で経費を記録し、月次レポートを自動生成します。',
                'url': 'https://lp-production-9e2c.up.railway.app/accounting'
            },
            '3': {
                'name': 'スケジュール管理',
                'price': 1500,
                'description': 'AIによる最適スケジュール',
                'usage': '予定を入力すると、AIが最適なスケジュールを提案し、効率的な時間管理をサポートします。',
                'url': 'https://lp-production-9e2c.up.railway.app/schedule'
            },
            '4': {
                'name': 'タスク管理',
                'price': 1500,
                'description': 'プロジェクト管理・進捗追跡',
                'usage': 'プロジェクトのタスクを管理し、進捗状況を自動で追跡・報告します。',
                'url': 'https://lp-production-9e2c.up.railway.app/task'
            }
        }
        if content_number not in content_info:
            send_line_message(reply_token, "❌ 無効な選択です。1-4の数字で選択してください。")
            return
        content = content_info[content_number]
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM usage_logs WHERE user_id = ?', (user_id_db,))
        usage_count = c.fetchone()[0]
        conn.close()
        is_free = usage_count == 0
        price_message = "🎉 **1個目は無料です！**" if is_free else f"💰 料金：{content['price']:,}円"
        confirm_message = f"""📋 選択内容の確認

📚 コンテンツ：{content['name']}
📝 内容：{content['description']}
{price_message}

このコンテンツを追加しますか？

✅ 追加する場合は「はい」と入力
❌ キャンセルする場合は「いいえ」と入力"""
        send_line_message(reply_token, confirm_message)
    except Exception as e:
        print(f'コンテンツ選択エラー: {e}')
        send_line_message(reply_token, "❌ エラーが発生しました。しばらく時間をおいて再度お試しください。")

def handle_content_confirmation(reply_token, user_id_db, stripe_subscription_id, content_number, confirmed):
    try:
        if not confirmed:
            send_line_message(reply_token, "❌ キャンセルしました。\n\n何か他にお手伝いできることはありますか？")
            return
        content_info = {
            '1': {
                'name': 'AI秘書機能',
                'price': 1500,
                'description': '24時間対応のAI秘書',
                'usage': 'LINEで直接メッセージを送るだけで、予定管理、メール作成、リマインダー設定などができます。',
                'url': 'https://lp-production-9e2c.up.railway.app/secretary'
            },
            '2': {
                'name': '会計管理ツール',
                'price': 1500,
                'description': '自動会計・経費管理',
                'usage': 'レシートを撮影するだけで自動で経費を記録し、月次レポートを自動生成します。',
                'url': 'https://lp-production-9e2c.up.railway.app/accounting'
            },
            '3': {
                'name': 'スケジュール管理',
                'price': 1500,
                'description': 'AIによる最適スケジュール',
                'usage': '予定を入力すると、AIが最適なスケジュールを提案し、効率的な時間管理をサポートします。',
                'url': 'https://lp-production-9e2c.up.railway.app/schedule'
            },
            '4': {
                'name': 'タスク管理',
                'price': 1500,
                'description': 'プロジェクト管理・進捗追跡',
                'usage': 'プロジェクトのタスクを管理し、進捗状況を自動で追跡・報告します。',
                'url': 'https://lp-production-9e2c.up.railway.app/task'
            }
        }
        content = content_info[content_number]
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM usage_logs WHERE user_id = ?', (user_id_db,))
        usage_count = c.fetchone()[0]
        conn.close()
        is_free = usage_count == 0
        usage_record = None
        if not is_free:
            subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            usage_item = None
            for item in subscription['items']['data']:
                if item['price']['id'] == os.getenv('STRIPE_USAGE_PRICE_ID'):
                    usage_item = item
                    break
            if not usage_item:
                send_line_message(reply_token, f"❌ 従量課金アイテムが見つかりません。\n\n設定されている価格ID: {os.getenv('STRIPE_USAGE_PRICE_ID')}\n\nサポートにお問い合わせください。")
                return
            subscription_item_id = usage_item['id']
            try:
                usage_record = stripe.UsageRecord.create(
                    subscription_item=subscription_item_id,
                    quantity=1,
                    timestamp=int(__import__('time').time()),
                    action='increment',
                )
            except Exception as usage_error:
                send_line_message(reply_token, f"❌ 使用量記録の作成に失敗しました。\n\nエラー: {str(usage_error)}")
                return
        try:
            conn = get_db_connection()
            c = conn.cursor()
            if is_free:
                c.execute('INSERT INTO usage_logs (user_id, usage_quantity, stripe_usage_record_id, is_free, content_type) VALUES (?, ?, ?, ?, ?)',
                          (user_id_db, 1, None, True, content['name']))
            else:
                c.execute('INSERT INTO usage_logs (user_id, usage_quantity, stripe_usage_record_id, is_free, content_type) VALUES (?, ?, ?, ?, ?)',
                          (user_id_db, 1, usage_record.id if usage_record else None, False, content['name']))
            conn.commit()
            conn.close()
        except Exception as db_error:
            pass
        if is_free:
            success_message = f"""🎉 コンテンツ追加完了！

📚 追加内容：
• {content['name']} 1件追加

💰 料金：
• 🎉 **無料で追加されました！**

📖 使用方法：
{content['usage']}

🔗 アクセスURL：
{content['url']}

何か他にお手伝いできることはありますか？"""
        else:
            success_message = f"""✅ コンテンツ追加完了！

📚 追加内容：
• {content['name']} 1件追加

💰 料金：
• 追加料金：{content['price']:,}円（次回請求時に反映）

📖 使用方法：
{content['usage']}

🔗 アクセスURL：
{content['url']}

何か他にお手伝いできることはありますか？"""
        send_line_message(reply_token, success_message)
    except Exception as e:
        send_line_message(reply_token, "❌ エラーが発生しました。しばらく時間をおいて再度お試しください。")

def handle_status_check(reply_token, user_id_db):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT content_type, is_free, created_at FROM usage_logs WHERE user_id = ? ORDER BY created_at DESC', (user_id_db,))
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
        send_line_message(reply_token, status_message)
    except Exception as e:
        send_line_message(reply_token, "❌ 利用状況の取得に失敗しました。しばらく時間をおいて再度お試しください。")

def handle_cancel_request(reply_token, user_id_db, stripe_subscription_id):
    try:
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        items = subscription['items']['data']
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT content_type, is_free FROM usage_logs WHERE user_id = ?', (user_id_db,))
        usage_free_map = {}
        for row in c.fetchall():
            usage_free_map[row[0]] = usage_free_map.get(row[0], False) or row[1]
        conn.close()
        content_choices = []
        for idx, item in enumerate(items, 1):
            price = item['price']
            name = price.get('nickname') or price.get('id')
            if 'AI秘書' in name or 'secretary' in name or 'prod_SgSj7btk61lSNI' in price.get('product',''):
                jp_name = 'AI秘書機能'
            elif '会計' in name or 'accounting' in name or 'prod_SgSnVeUB5DAihu' in price.get('product',''):
                jp_name = '会計管理ツール'
            elif 'スケジュール' in name or 'schedule' in name:
                jp_name = 'スケジュール管理'
            elif 'タスク' in name or 'task' in name:
                jp_name = 'タスク管理'
            elif price.get('unit_amount',0) >= 500000:
                jp_name = '月額基本料金'
            else:
                jp_name = name
            amount = price.get('unit_amount', 0)
            amount_jpy = int(amount) // 100 if amount else 0
            is_free = usage_free_map.get(jp_name, False)
            display_price = '0円' if is_free else f'{amount_jpy:,}円'
            content_choices.append(f"{idx}. {jp_name}（{display_price}/月）")
        if not content_choices:
            send_line_message(reply_token, "現在契約中のコンテンツはありません。")
            return
        choice_message = "\n".join(content_choices)
        send_line_message(reply_token, f"解約したいコンテンツを選んでください（カンマ区切りで複数選択可）:\n{choice_message}\n\n例: 1,2")
    except Exception as e:
        send_line_message(reply_token, "❌ 契約中コンテンツの取得に失敗しました。しばらく時間をおいて再度お試しください。")

def handle_cancel_selection(reply_token, user_id_db, stripe_subscription_id, selection_text):
    try:
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        items = subscription['items']['data']
        indices = [int(x.strip())-1 for x in selection_text.split(',') if x.strip().isdigit()]
        cancelled = []
        for idx in indices:
            if 0 <= idx < len(items):
                item = items[idx]
                stripe.SubscriptionItem.delete(item['id'], proration_behavior='none')
                price = item['price']
                name = price.get('nickname') or price.get('id')
                if 'AI秘書' in name or 'secretary' in name or 'prod_SgSj7btk61lSNI' in price.get('product',''):
                    jp_name = 'AI秘書機能'
                elif '会計' in name or 'accounting' in name or 'prod_SgSnVeUB5DAihu' in price.get('product',''):
                    jp_name = '会計管理ツール'
                elif 'スケジュール' in name or 'schedule' in name:
                    jp_name = 'スケジュール管理'
                elif 'タスク' in name or 'task' in name:
                    jp_name = 'タスク管理'
                elif price.get('unit_amount',0) >= 500000:
                    jp_name = '月額基本料金'
                else:
                    jp_name = name
                cancelled.append(jp_name)
        if cancelled:
            send_line_message(reply_token, f"以下のコンテンツの解約を受け付けました（請求期間終了まで利用可能です）：\n" + "\n".join(cancelled))
        else:
            send_line_message(reply_token, "有効な番号が選択されませんでした。もう一度お試しください。")
    except Exception as e:
        send_line_message(reply_token, "❌ 解約処理に失敗しました。しばらく時間をおいて再度お試しください。")

def get_welcome_message():
    return "ようこそ！LINE連携が完了しました。"

def get_not_registered_message():
    return "ご登録情報が見つかりません。LPからご登録ください。" 