# 案内文・メニュー・ヘルプなどのテンプレート

def get_default_message():
    return {
        "type": "template",
        "altText": "何かお手伝いできることはありますか？",
        "template": {
            "type": "buttons",
            "title": "AIコレクションズ",
            "text": "何かお手伝いできることはありますか？",
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
    return [
        {
            "type": "text",
            "text": "📖 AIコレクションズ 使い方ガイド\n\n🎯 基本操作：\n• 「追加」：コンテンツを追加（1個目無料）\n• 「状態」：利用状況と料金を確認\n• 「解約」：解約メニューを表示\n• 「メニュー」：メインメニューに戻る\n• 「ヘルプ」：このガイドを表示\n\n📱 コンテンツ追加の流れ：\n1️⃣ 「追加」を選択\n2️⃣ 追加したいコンテンツを選択（1-3）\n3️⃣ 料金を確認して「はい」で確定\n4️⃣ アクセスURLが送信されます\n\n🔚 解約について：\n• 「サブスクリプション解約」：全てのサービスを解約\n• 「コンテンツ解約」：個別のコンテンツを選択して解約\n\n💰 料金について：\n• 月額基本料金：3,900円\n• 追加コンテンツ：1個目無料\n• 2個目以降：1,500円/件（次回請求時）\n\n✨ 各サービスの特徴：\n📅 AI予定秘書：スケジュール管理・会議調整\n💰 AI経理秘書：見積書・請求書作成\n📝 AIタスクコンシェルジュ：タスク管理・優先順位設定\n\n❓ お困りの際は：\n• メニューから各機能をお試しください\n• エラーが発生した場合は時間をおいて再試行してください\n• 何かわからないことがあれば「ヘルプ」と入力してください"
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

def get_help_message_company():
    """企業ユーザー専用：ヘルプメッセージ"""
    return [
        {
            "type": "text",
            "text": "🏢 AIコレクションズ 企業向け使い方ガイド\n\n🎯 基本操作：\n• 「追加」：新しいコンテンツを追加\n• 「状態」：企業の利用状況と料金を確認\n• 「解約」：解約メニューを表示\n• 「メニュー」：メインメニューに戻る\n• 「ヘルプ」：このガイドを表示\n\n📱 コンテンツ追加の流れ：\n1️⃣ 「追加」を選択\n2️⃣ 追加したいコンテンツを選択\n3️⃣ 料金を確認して確定\n4️⃣ 新しいLINEアカウントが作成されます\n\n🔚 解約について：\n• 「解約」を選択して解約メニューを表示\n• 「サブスクリプション解約」：全てのサービスを解約\n• 「コンテンツ解約」：個別のコンテンツを選択して解約\n• 解約後は料金が調整されます\n\n💰 料金体系：\n• 基本料金：月額3,900円\n• 追加コンテンツ：1件1,500円/月\n• 例：2件利用の場合 3,900円 + 1,500円 = 5,400円/月\n\n✨ 各サービスの特徴：\n📅 AI予定秘書：企業のスケジュール管理・会議調整\n💰 AI経理秘書：経理作業の効率化・書類作成\n📝 AIタスクコンシェルジュ：タスク管理・優先順位設定\n\n❓ お困りの際は：\n• メニューから各機能をお試しください\n• エラーが発生した場合は時間をおいて再試行してください\n• 何かわからないことがあれば「ヘルプ」と入力してください"
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

def get_menu_message_company():
    """企業ユーザー専用：メニューメッセージ"""
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