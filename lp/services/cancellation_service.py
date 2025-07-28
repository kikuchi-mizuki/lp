import os
from dotenv import load_dotenv
from utils.db import get_db_connection

load_dotenv()

def record_cancellation(user_id, content_type):
    """
    解約履歴を記録
    
    Args:
        user_id (int): ユーザーID
        content_type (str): 解約されたコンテンツタイプ
    """
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO cancellation_history (user_id, content_type)
            VALUES (%s, %s)
        ''', (user_id, content_type))
        
        conn.commit()
        conn.close()
        print(f'[DEBUG] 解約履歴記録: user_id={user_id}, content_type={content_type}')
        
    except Exception as e:
        print(f'[ERROR] 解約履歴記録エラー: {e}')
        if conn:
            conn.close()

def is_content_cancelled(user_id, content_type):
    """
    コンテンツが解約されているかチェック
    
    Args:
        user_id (int): ユーザーID
        content_type (str): チェックするコンテンツタイプ
        
    Returns:
        bool: 解約されている場合はTrue
    """
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT COUNT(*) FROM cancellation_history 
            WHERE user_id = %s AND content_type = %s
        ''', (user_id, content_type))
        
        count = c.fetchone()[0]
        conn.close()
        
        is_cancelled = count > 0
        print(f'[DEBUG] 解約チェック: user_id={user_id}, content_type={content_type}, is_cancelled={is_cancelled}')
        
        return is_cancelled
        
    except Exception as e:
        print(f'[ERROR] 解約チェックエラー: {e}')
        if conn:
            conn.close()
        return False

def get_cancelled_contents(user_id):
    """
    ユーザーが解約したコンテンツのリストを取得
    
    Args:
        user_id (int): ユーザーID
        
    Returns:
        list: 解約されたコンテンツタイプのリスト
    """
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT content_type FROM cancellation_history 
            WHERE user_id = %s
            ORDER BY cancelled_at DESC
        ''', (user_id,))
        
        results = c.fetchall()
        conn.close()
        
        cancelled_contents = [row[0] for row in results]
        print(f'[DEBUG] 解約コンテンツ取得: user_id={user_id}, cancelled_contents={cancelled_contents}')
        
        return cancelled_contents
        
    except Exception as e:
        print(f'[ERROR] 解約コンテンツ取得エラー: {e}')
        if conn:
            conn.close()
        return []

def get_content_line_url(content_type):
    """
    コンテンツタイプに対応する公式LINEのURLを取得
    
    Args:
        content_type (str): コンテンツタイプ
        
    Returns:
        str: 公式LINEのURL
    """
    line_urls = {
        'AI予定秘書': 'https://line.me/R/ti/p/@ai_schedule_secretary',
        'AI経理秘書': 'https://line.me/R/ti/p/@ai_accounting_secretary',
        'AIタスクコンシェルジュ': 'https://line.me/R/ti/p/@ai_task_concierge'
    }
    
    return line_urls.get(content_type, '')

def get_restriction_message_for_content(content_type):
    """
    特定のコンテンツの利用制限メッセージを取得
    
    Args:
        content_type (str): コンテンツタイプ
        
    Returns:
        dict: LINEメッセージ形式の制限メッセージ
    """
    line_url = get_content_line_url(content_type)
    
    return {
        "type": "template",
        "altText": f"{content_type}の利用制限",
        "template": {
            "type": "buttons",
            "title": f"{content_type}の利用制限",
            "text": f"{content_type}は解約されているため、公式LINEを利用できません。\n\nAIコレクションズの公式LINEで再度ご登録いただき、サービスをご利用ください。",
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