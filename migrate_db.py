#!/usr/bin/env python3
"""
データベースマイグレーションスクリプト
"""

import os
import sys
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db import migrate_add_pending_charge

def main():
    print("🔄 データベースマイグレーションを開始します...")
    
    try:
        migrate_add_pending_charge()
        print("✅ マイグレーションが完了しました")
    except Exception as e:
        print(f"❌ マイグレーションエラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 