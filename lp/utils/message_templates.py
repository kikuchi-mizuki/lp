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
        "type": "text",
                        "text": "📖 AIコレクションズ 使い方ガイド\n\n🔧 基本操作：\n• 「追加」：コンテンツを追加（1個目無料）\n• 「状態」：利用状況と料金を確認\n• 「解約」：解約メニューを表示\n• 「メニュー」：メニューに戻る\n\n📱 コンテンツ追加の流れ：\n1. 「追加」を選択\n2. 追加したいコンテンツを選択（1-3）\n3. 料金を確認して「はい」で確定\n4. アクセスURLが送信されます\n\n🔚 解約について：\n• 「サブスクリプション解約」：全てのサービスを解約\n• 「コンテンツ解約」：個別のコンテンツを選択して解約\n\n💰 料金について：\n• 月額基本料金：3,900円\n• 追加コンテンツ：1個目無料\n• 2個目以降：1,500円/件（次回請求時）\n\n❓ お困りの際は：\n• メニューから各機能をお試しください\n• エラーが発生した場合は時間をおいて再試行してください"
    } 