from flask import Flask, request, jsonify, render_template
import os
import psycopg2
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)

# 共有PostgreSQLデータベースに接続
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    """データベース接続を取得"""
    return psycopg2.connect(DATABASE_URL)

def check_user_restriction(line_user_id):
    """ユーザーの利用制限をチェック"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # ユーザーIDを取得
        cursor.execute('SELECT id FROM users WHERE line_user_id = %s', (line_user_id,))
        user_result = cursor.fetchone()
        
        if not user_result:
            return {
                'restricted': False, 
                'message': 'ユーザーが見つかりません',
                'error': 'user_not_found'
            }
        
        user_id = user_result[0]
        
        # 解約履歴をチェック
        cursor.execute('''
            SELECT COUNT(*) FROM cancellation_history 
            WHERE user_id = %s AND content_type = 'AI経理秘書'
        ''', (user_id,))
        
        is_cancelled = cursor.fetchone()[0] > 0
        
        conn.close()
        
        return {
            'restricted': is_cancelled,
            'message': 'AI経理秘書は解約されているため利用できません。' if is_cancelled else '利用可能です。',
            'user_id': user_id,
            'content_type': 'AI経理秘書'
        }
        
    except Exception as e:
        print(f'[ERROR] 利用制限チェックエラー: {e}')
        return {
            'restricted': False,
            'message': 'システムエラーが発生しました。',
            'error': str(e)
        }

@app.route('/')
def index():
    """メインページ"""
    return render_template('index.html')

@app.route('/check_restriction', methods=['POST'])
def check_restriction():
    """利用制限チェックAPI"""
    try:
        data = request.get_json()
        line_user_id = data.get('line_user_id')
        
        if not line_user_id:
            return jsonify({
                'error': 'line_user_id is required',
                'restricted': False
            }), 400
        
        result = check_user_restriction(line_user_id)
        return jsonify(result)
        
    except Exception as e:
        print(f'[ERROR] API エラー: {e}')
        return jsonify({
            'error': str(e),
            'restricted': False
        }), 500

@app.route('/restriction_message', methods=['POST'])
def get_restriction_message():
    """制限メッセージ取得API"""
    try:
        data = request.get_json()
        line_user_id = data.get('line_user_id')
        
        if not line_user_id:
            return jsonify({
                'error': 'line_user_id is required'
            }), 400
        
        result = check_user_restriction(line_user_id)
        
        if result.get('restricted'):
            # 制限メッセージを生成
            restriction_message = {
                "type": "template",
                "altText": "AI経理秘書の利用制限",
                "template": {
                    "type": "buttons",
                    "title": "AI経理秘書の利用制限",
                    "text": "AI経理秘書は解約されているため、公式LINEを利用できません。\n\nAIコレクションズの公式LINEで再度ご登録いただき、サービスをご利用ください。",
                    "thumbnailImageUrl": "https://ai-collections.herokuapp.com/static/images/logo.png",
                    "imageAspectRatio": "rectangle",
                    "imageSize": "cover",
                    "imageBackgroundColor": "#FFFFFF",
                    "actions": [
                        {
                            "type": "uri",
                            "label": "AIコレクションズ公式LINE",
                            "uri": "https://line.me/R/ti/p/@ai_collections"
                        },
                        {
                            "type": "uri",
                            "label": "サービス詳細",
                            "uri": "https://ai-collections.herokuapp.com"
                        }
                    ]
                }
            }
            
            return jsonify({
                'line_user_id': line_user_id,
                'user_id': result.get('user_id'),
                'content_type': 'AI経理秘書',
                'restricted': True,
                'message': restriction_message
            })
        else:
            return jsonify({
                'line_user_id': line_user_id,
                'user_id': result.get('user_id'),
                'content_type': 'AI経理秘書',
                'restricted': False,
                'message': 'AI経理秘書は利用可能です。'
            })
        
    except Exception as e:
        print(f'[ERROR] 制限メッセージ取得エラー: {e}')
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/health')
def health_check():
    """ヘルスチェック"""
    return jsonify({
        'status': 'healthy',
        'service': 'ai-accounting-secretary',
        'database_connected': bool(DATABASE_URL)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 