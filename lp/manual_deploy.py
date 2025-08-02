#!/usr/bin/env python3
"""
Railway CLIを使用した手動デプロイスクリプト
"""

import os
import subprocess
import time

def run_command(command, description):
    """コマンドを実行"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description}成功")
            return True
        else:
            print(f"❌ {description}失敗: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description}エラー: {e}")
        return False

def manual_deploy():
    """手動デプロイを実行"""
    print("=== Railway手動デプロイ ===")
    
    # 1. Railway CLIの確認
    if not run_command("railway --version", "Railway CLI確認"):
        print("❌ Railway CLIがインストールされていません")
        return False
    
    # 2. Railwayにログイン
    if not run_command("railway login", "Railwayログイン"):
        print("❌ Railwayログインに失敗しました")
        return False
    
    # 3. プロジェクトの確認
    if not run_command("railway list", "プロジェクト一覧確認"):
        print("❌ プロジェクト一覧の取得に失敗しました")
        return False
    
    # 4. デプロイの実行
    print("🚀 デプロイを開始します...")
    if run_command("railway up", "Railwayデプロイ"):
        print("✅ デプロイが完了しました")
        return True
    else:
        print("❌ デプロイに失敗しました")
        return False

def main():
    """メイン関数"""
    print("Railway手動デプロイを開始します...")
    
    if manual_deploy():
        print("\n🎉 手動デプロイが完了しました！")
        print("\n📝 次のステップ:")
        print("1. Railwayダッシュボードでデプロイ状況を確認")
        print("2. Webhookエンドポイントのテスト")
        print("3. LINE Developers ConsoleでWebhook URLを更新")
    else:
        print("\n❌ 手動デプロイに失敗しました")
        print("\n💡 代替案:")
        print("1. Railwayダッシュボードから手動でデプロイ")
        print("2. GitHub Actionsの再実行")
        print("3. ネットワーク接続の確認")

if __name__ == "__main__":
    main() 