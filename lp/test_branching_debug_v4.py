#!/usr/bin/env python3
"""
分岐処理デバッグv4テスト
"""

import os
from dotenv import load_dotenv
from utils.db import get_db_connection

# 環境変数を読み込み
load_dotenv()

def test_branching_debug_v4():
    """分岐処理デバッグv4テスト"""
    print("=== 分岐処理デバッグv4テスト ===")
    
    # 問題の分析
    print("\n=== 問題の分析 ===")
    print("❌ 現在の問題:")
    print("  - 「追加」→「1」で再度初回案内文が送信される")
    print("  - user_statesの更新が正しく反映されていない")
    print("  - add_select状態の処理が実行されていない")
    
    print("\n🔍 問題の可能性:")
    print("  1. 複数のLINE Botインスタンスが動作している")
    print("  2. user_statesがリセットされている")
    print("  3. 状態の競合が発生している")
    print("  4. 条件分岐の順序に問題がある")
    
    print("\n✅ 追加したデバッグログ:")
    print("  - ユーザー状態設定時の詳細ログ")
    print("  - add_select状態処理時の詳細ログ")
    print("  - user_states全体の状態表示")
    
    print("\n📋 期待されるログ:")
    print("  [DEBUG] 追加コマンド受信: user_id=xxx, state=welcome_sent")
    print("  [DEBUG] ユーザー状態をadd_selectに設定: user_id=xxx, user_states={'xxx': 'add_select'}")
    print("  [DEBUG] テキストメッセージ受信: user_id=xxx, text=1")
    print("  [DEBUG] add_select状態での処理: user_id=xxx, text=1, user_states={'xxx': 'add_select'}")
    print("  [DEBUG] コンテンツ選択: text=1")
    
    print("\n🔧 次のステップ:")
    print("  1. 実際のLINE Botで「追加」→「1」をテスト")
    print("  2. 新しいデバッグログを確認")
    print("  3. user_statesの状態変化を追跡")
    print("  4. 問題の根本原因を特定")

if __name__ == "__main__":
    test_branching_debug_v4() 