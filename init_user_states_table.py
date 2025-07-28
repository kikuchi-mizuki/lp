#!/usr/bin/env python3
"""
user_statesテーブル初期化スクリプト
"""
import os
from dotenv import load_dotenv
from models.user_state import init_user_states_table

load_dotenv()

def main():
    print("=== user_statesテーブル初期化 ===")
    try:
        init_user_states_table()
        print("✅ user_statesテーブルの初期化が完了しました")
    except Exception as e:
        print(f"❌ 初期化エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 