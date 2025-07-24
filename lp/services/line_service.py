import requests
import sqlite3
import psycopg2
import os

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
    pass

def handle_content_selection(reply_token, user_id_db, stripe_subscription_id, content_number):
    pass

def handle_content_confirmation(reply_token, user_id_db, stripe_subscription_id, content_number, confirmed):
    pass

def handle_status_check(reply_token, user_id_db):
    pass

def handle_cancel_request(reply_token, user_id_db, stripe_subscription_id):
    pass

def handle_cancel_selection(reply_token, user_id_db, stripe_subscription_id, selection_text):
    pass

def get_welcome_message():
    return "ようこそ！LINE連携が完了しました。"

def get_not_registered_message():
    return "ご登録情報が見つかりません。LPからご登録ください。" 