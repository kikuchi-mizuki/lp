#!/usr/bin/env python3
"""
ユーザー状態管理モデル
"""

from utils.db import get_db_connection
import datetime

def get_user_state(line_user_id):
    """ユーザーの状態を取得"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT state FROM user_states WHERE line_user_id = %s', (line_user_id,))
        result = c.fetchone()
        conn.close()
        
        if result:
            return result[0]
        else:
            return 'welcome_sent'  # デフォルト状態
    except Exception as e:
        print(f'[DEBUG] ユーザー状態取得エラー: {e}')
        return 'welcome_sent'

def set_user_state(line_user_id, state):
    """ユーザーの状態を設定"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 既存の状態を更新、なければ新規作成
        c.execute('''
            INSERT INTO user_states (line_user_id, state, updated_at) 
            VALUES (%s, %s, %s)
            ON CONFLICT (line_user_id) 
            DO UPDATE SET state = %s, updated_at = %s
        ''', (line_user_id, state, datetime.datetime.now(), state, datetime.datetime.now()))
        
        conn.commit()
        conn.close()
        print(f'[DEBUG] ユーザー状態設定: line_user_id={line_user_id}, state={state}')
    except Exception as e:
        print(f'[DEBUG] ユーザー状態設定エラー: {e}')

def clear_user_state(line_user_id):
    """ユーザーの状態をクリア"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('DELETE FROM user_states WHERE line_user_id = %s', (line_user_id,))
        conn.commit()
        conn.close()
        print(f'[DEBUG] ユーザー状態クリア: line_user_id={line_user_id}')
    except Exception as e:
        print(f'[DEBUG] ユーザー状態クリアエラー: {e}')

def init_user_states_table():
    """user_statesテーブルを初期化"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # user_statesテーブルが存在しない場合は作成
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_states (
                id SERIAL PRIMARY KEY,
                line_user_id VARCHAR(255) UNIQUE NOT NULL,
                state VARCHAR(100) NOT NULL DEFAULT 'welcome_sent',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print('[DEBUG] user_statesテーブル初期化完了')
    except Exception as e:
        print(f'[DEBUG] user_statesテーブル初期化エラー: {e}') 