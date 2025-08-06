import sys
import traceback
from flask import Flask, jsonify

def create_app():
    """アプリケーション作成のテスト"""
    try:
        print("1. Flaskアプリケーション作成開始...")
        app = Flask(__name__)
        print("✅ Flaskアプリケーション作成成功")
        
        print("2. ルート定義開始...")
        @app.route('/')
        def hello():
            return 'Hello, World!'
        
        @app.route('/health')
        def health():
            return jsonify({'status': 'ok'})
        
        print("✅ ルート定義成功")
        
        print("3. アプリケーション設定確認...")
        print(f"   - アプリケーション名: {app.name}")
        print(f"   - テンプレートフォルダ: {app.template_folder}")
        print(f"   - 静的ファイルフォルダ: {app.static_folder}")
        print("✅ アプリケーション設定確認完了")
        
        return app
        
    except Exception as e:
        print(f"❌ アプリケーション作成エラー: {e}")
        traceback.print_exc()
        return None

def run_app():
    """アプリケーション実行のテスト"""
    try:
        print("🚀 デバッグアプリケーション起動開始...")
        
        app = create_app()
        if app is None:
            print("❌ アプリケーション作成に失敗しました")
            return
        
        print("4. アプリケーション起動開始...")
        print("📡 ポート 5004 で起動します")
        
        app.run(debug=False, host='0.0.0.0', port=5004)
        
    except Exception as e:
        print(f"❌ アプリケーション起動エラー: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    run_app() 