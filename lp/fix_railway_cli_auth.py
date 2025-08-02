#!/usr/bin/env python3
"""
Railway CLI認証問題解決スクリプト
"""

import os
import subprocess
import json
import time

def fix_railway_cli_auth():
    """Railway CLIの認証問題を解決"""
    try:
        print("=== Railway CLI認証問題解決 ===")
        
        railway_token = os.getenv('RAILWAY_TOKEN')
        if not railway_token:
            print("❌ RAILWAY_TOKENが設定されていません")
            return False
        
        print(f"✅ Railway Token確認: {railway_token[:8]}...")
        
        # 1. 既存の設定をクリア
        print("\n1. 既存の設定をクリア中...")
        railway_config_dir = os.path.expanduser("~/.railway")
        
        if os.path.exists(railway_config_dir):
            import shutil
            shutil.rmtree(railway_config_dir)
            print("✅ 既存の設定ディレクトリを削除")
        
        # 2. 新しい設定ディレクトリを作成
        os.makedirs(railway_config_dir, exist_ok=True)
        print("✅ 新しい設定ディレクトリを作成")
        
        # 3. 正しい形式で設定ファイルを作成
        config_file = os.path.join(railway_config_dir, "config.json")
        
        # Railway CLIの正しい設定形式
        config_data = {
            "token": railway_token,
            "user": {
                "id": "auto-login",
                "email": "auto@railway.app"
            },
            "projects": {}
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        print("✅ 設定ファイルを作成")
        
        # 4. Railway CLIの動作確認
        print("\n2. Railway CLIの動作確認...")
        
        # バージョン確認
        result = subprocess.run(['railway', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Railway CLI確認: {result.stdout.strip()}")
        else:
            print("❌ Railway CLIが利用できません")
            return False
        
        # ログイン確認
        result = subprocess.run(['railway', 'whoami'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Railway CLI認証成功")
            print(f"   ユーザー情報: {result.stdout.strip()}")
        else:
            print("⚠️ Railway CLI認証に問題があります")
            print(f"   エラー: {result.stderr}")
            
            # 代替方法: 環境変数でログイン
            print("\n3. 環境変数方式でログインを試行...")
            env = os.environ.copy()
            env['RAILWAY_TOKEN'] = railway_token
            
            result = subprocess.run(['railway', 'login'], input=railway_token, text=True, capture_output=True, env=env, timeout=30)
            
            if result.returncode == 0:
                print("✅ 環境変数方式でログイン成功")
            else:
                print("❌ 環境変数方式でもログイン失敗")
                print(f"   エラー: {result.stderr}")
                return False
        
        # 5. プロジェクト一覧確認
        print("\n4. プロジェクト一覧確認...")
        result = subprocess.run(['railway', 'projects'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ プロジェクト一覧取得成功")
            print("   プロジェクト一覧:")
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # ヘッダーをスキップ
                if line.strip():
                    print(f"     {line}")
        else:
            print("⚠️ プロジェクト一覧取得に失敗")
            print(f"   エラー: {result.stderr}")
        
        print("\n🎉 Railway CLI認証問題解決完了！")
        return True
        
    except Exception as e:
        print(f"❌ Railway CLI認証問題解決エラー: {e}")
        return False

def test_service_addition_with_cli():
    """Railway CLIを使用したサービス追加テスト"""
    try:
        print("\n=== Railway CLIサービス追加テスト ===")
        
        # テスト用プロジェクトを作成
        project_name = f"test-cli-auth-{int(time.time())}"
        
        print(f"1. テストプロジェクト作成: {project_name}")
        
        # プロジェクト作成
        result = subprocess.run(['railway', 'init', '--name', project_name], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ プロジェクト作成成功")
            
            # プロジェクトIDを取得
            result = subprocess.run(['railway', 'status'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ プロジェクト情報取得成功")
                print(f"   プロジェクト情報: {result.stdout.strip()}")
                
                # サービス追加テスト
                print("\n2. サービス追加テスト...")
                result = subprocess.run(['railway', 'service', 'add', 'https://github.com/kikuchi-mizuki/task-bot'], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ サービス追加成功！")
                    print(f"   結果: {result.stdout.strip()}")
                    return True
                else:
                    print("❌ サービス追加失敗")
                    print(f"   エラー: {result.stderr}")
                    return False
            else:
                print("❌ プロジェクト情報取得失敗")
                return False
        else:
            print("❌ プロジェクト作成失敗")
            print(f"   エラー: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Railway CLIサービス追加テストエラー: {e}")
        return False

def main():
    """メイン関数"""
    print("🚀 Railway CLI認証問題解決を開始します...")
    
    # 1. 認証問題解決
    if fix_railway_cli_auth():
        print("\n✅ Railway CLI認証問題が解決されました")
        
        # 2. サービス追加テスト
        if test_service_addition_with_cli():
            print("\n🎉 Railway CLIを使用したサービス追加が成功しました！")
            print("これで、サービス追加の自動化が完全に動作します。")
        else:
            print("\n⚠️ Railway CLIサービス追加テストに失敗しました")
            print("GitHub Actions方式を使用してください。")
    else:
        print("\n❌ Railway CLI認証問題の解決に失敗しました")
        print("GitHub Actions方式を使用してください。")

if __name__ == "__main__":
    main() 