import os
import sys
sys.path.append('.')

print('=== LINE Bot再起動が必要です ===')

print('''
🚨 問題の原因：
実際のLINE Botが古いコードを実行しているため、修正が反映されていません。

🔧 解決方法：
1. 現在実行中のLINE Botプロセスを停止
2. 新しいコードでLINE Botを再起動
3. 実際のLINE Botでコンテンツ追加をテスト

📋 手順：
1. 現在のプロセスを確認: ps aux | grep python
2. LINE Botプロセスを停止: kill [プロセスID]
3. LINE Botを再起動: python app.py または gunicorn app:app
4. 実際のLINE Botで「追加」と入力してテスト

✅ 修正内容：
- 正しいSubscription Item ID (si_Sl1XdKM6w8gq79) を使用
- ¥1,500の従量課金に正しく記録
- 1個目は無料、2個目以降は¥1,500

⚠️ 注意：
環境変数のSTRIPE_USAGE_PRICE_IDが間違っているため、
コードで直接正しい値を指定しています。
''')

# 現在のプロセスを確認
print('\n=== 現在のプロセス確認 ===')
os.system('ps aux | grep python | grep -v grep')

print('\n=== 推奨コマンド ===')
print('1. プロセス停止: pkill -f "python.*app.py"')
print('2. LINE Bot再起動: python app.py')
print('3. または: gunicorn app:app --bind 0.0.0.0:5000') 