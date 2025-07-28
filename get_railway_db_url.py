#!/usr/bin/env python3
"""
Railway CLIを使ってDATABASE_URLを取得するスクリプト
"""

import subprocess
import json
import os
import sys

def get_railway_variables():
    """Railway CLIを使って変数を取得"""
    
    try:
        print("🔍 Railway CLIで変数を取得中...")
        result = subprocess.run(['railway', 'variables'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Railway CLIで変数を取得しました")
            return result.stdout
        else:
            print(f"❌ Railway CLIエラー: {result.stderr}")
            return None
            
    except FileNotFoundError:
        print("❌ Railway CLIがインストールされていません")
        print("以下のコマンドでインストールしてください：")
        print("npm install -g @railway/cli")
        return None
    except subprocess.TimeoutExpired:
        print("❌ Railway CLIの実行がタイムアウトしました")
        return None
    except Exception as e:
        print(f"❌ Railway CLI実行エラー: {e}")
        return None

def parse_railway_output(output):
    """Railway CLIの出力を解析"""
    
    lines = output.strip().split('\n')
    variables = {}
    
    for line in lines:
        if '=' in line:
            key, value = line.split('=', 1)
            variables[key.strip()] = value.strip()
    
    return variables

def main():
    """メイン関数"""
    
    print("🚀 Railway DATABASE_URL取得スクリプト")
    print("=" * 50)
    
    # Railway CLIで変数を取得
    output = get_railway_variables()
    
    if not output:
        print("\n📋 手動でDATABASE_URLを設定してください：")
        print("1. RailwayダッシュボードでPostgreSQLサービスを開く")
        print("2. 'Connect'タブを選択")
        print("3. 'External'接続のDATABASE_URLをコピー")
        print("4. .envファイルに設定")
        return
    
    # 変数を解析
    variables = parse_railway_output(output)
    
    if 'DATABASE_URL' in variables:
        database_url = variables['DATABASE_URL']
        print(f"✅ DATABASE_URLを取得しました: {database_url[:50]}...")
        
        # .envファイルに保存
        with open('.env', 'w') as f:
            f.write(f"DATABASE_URL={database_url}\n")
        
        print("✅ .envファイルに保存しました")
        
        # 環境変数として設定
        os.environ['DATABASE_URL'] = database_url
        
        print("\n🎉 DATABASE_URLの設定が完了しました！")
        print("次に 'python create_cancellation_table.py' を実行してください")
        
    else:
        print("❌ DATABASE_URLが見つかりません")
        print("Railwayダッシュボードで手動で確認してください")

if __name__ == "__main__":
    main() 