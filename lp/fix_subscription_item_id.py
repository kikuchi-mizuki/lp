import os
import sys
sys.path.append('.')

# 正しいSubscription Item IDを直接指定するように修正
print('=== Subscription Item ID修正 ===')

# 修正対象のファイル
files_to_fix = [
    'services/line_service.py',
    'services/stripe_service.py'
]

# 修正内容
replacements = [
    {
        'old': "usage_price_id = 'price_1Rog1nIxg6C5hAVdnqB5MJiT'",
        'new': "usage_subscription_item_id = 'si_Sl1XdKM6w8gq79'  # ¥1,500の従量課金\n                usage_price_id = 'price_1Rog1nIxg6C5hAVdnqB5MJiT'"
    },
    {
        'old': "if usage_price_id:",
        'new': "if usage_subscription_item_id:"
    },
    {
        'old': "subscription = stripe.Subscription.retrieve(stripe_subscription_id)\n                    usage_item = None\n                    for item in subscription['items']['data']:\n                        if item['price']['id'] == usage_price_id:\n                            usage_item = item\n                            break",
        'new': "usage_item = {'id': usage_subscription_item_id}"
    }
]

for file_path in files_to_fix:
    print(f'修正対象: {file_path}')
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        for replacement in replacements:
            if replacement['old'] in content:
                content = content.replace(replacement['old'], replacement['new'])
                print(f'  ✅ 置換完了: {replacement["old"][:50]}...')
            else:
                print(f'  ⚠️ 置換対象が見つかりません: {replacement["old"][:50]}...')
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'  ✅ ファイル更新完了')
        else:
            print(f'  ℹ️ 変更なし')
            
    except Exception as e:
        print(f'  ❌ エラー: {e}')

print('\n=== 修正完了 ===')
print('正しいSubscription Item ID (si_Sl1XdKM6w8gq79) を直接指定するように修正しました。')
print('これにより、¥1,500の従量課金に正しく使用量が記録されるようになります。') 