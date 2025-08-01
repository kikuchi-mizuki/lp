#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
環境変数読み込みスクリプト
"""

import os
from dotenv import load_dotenv

def load_environment_variables():
    """環境変数を読み込み"""
    try:
        # .envファイルを読み込み
        env_file = '.env'
        if os.path.exists(env_file):
            load_dotenv(env_file)
            print(f"✅ .envファイルを読み込みました: {env_file}")
        else:
            print(f"⚠️ .envファイルが見つかりません: {env_file}")
        
        # Railway関連の環境変数を確認
        railway_token = os.getenv('RAILWAY_TOKEN')
        railway_project_id = os.getenv('RAILWAY_PROJECT_ID')
        base_domain = os.getenv('BASE_DOMAIN')
        default_token = os.getenv('DEFAULT_RAILWAY_TOKEN')
        default_project_id = os.getenv('DEFAULT_RAILWAY_PROJECT_ID')
        
        print(f"\n📊 環境変数確認:")
        print(f"  RAILWAY_TOKEN: {'設定済み' if railway_token else '未設定'}")
        print(f"  RAILWAY_PROJECT_ID: {railway_project_id or '未設定'}")
        print(f"  BASE_DOMAIN: {base_domain or '未設定'}")
        print(f"  DEFAULT_RAILWAY_TOKEN: {'設定済み' if default_token else '未設定'}")
        print(f"  DEFAULT_RAILWAY_PROJECT_ID: {default_project_id or '未設定'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 環境変数読み込みエラー: {e}")
        return False

if __name__ == "__main__":
    load_environment_variables() 