# 案内文・メニュー・ヘルプなどのテンプレート

def get_default_message():
    return {
        "type": "template",
        "altText": "何かお手伝いできることはありますか？",
        "template": {
            "type": "buttons",
            "title": "AIコレクションズ",
            "text": "何かお手伝いできることはありますか？\n\n下のボタンからお選びください。",
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

def get_menu_message():
    return {
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

def get_help_message():
    return {
        "type": "template",
        "altText": "ヘルプ",
        "template": {
            "type": "buttons",
            "title": "ヘルプ",
            "text": "各機能の説明です。\n\n• 追加：利用したいコンテンツを選んで追加（1個目は無料、2個目以降は1,500円/件）\n• 解約：契約中のコンテンツや月額を選んで解約（請求期間終了まで利用可）\n• 状態：現在の利用状況や料金を確認\n\n下のボタンから操作してください。",
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
                    "label": "メニューに戻る",
                    "text": "メニュー"
                }
            ]
        }
    } 