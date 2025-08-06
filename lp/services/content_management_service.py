#!/usr/bin/env python3
"""
企業コンテンツ管理サービス
企業ごとのコンテンツ選択・管理・自動配信機能
"""

import os
import json
import time
from datetime import datetime, timedelta
from lp.utils.db import get_db_connection
from lp.services.line_api_service import line_api_service

class ContentManagementService:
    """企業コンテンツ管理サービス"""
    
    def __init__(self):
        self.available_contents = {
            'ai_accounting': {
                'name': 'AI経理秘書',
                'description': '自動経理処理・帳簿作成・税務申告サポート',
                'price': 2980,
                'features': ['自動仕訳', '帳簿作成', '税務申告', '経営分析']
            },
            'ai_schedule': {
                'name': 'AI予定秘書',
                'description': 'スケジュール管理・会議調整・リマインダー機能',
                'price': 1980,
                'features': ['スケジュール管理', '会議調整', 'リマインダー', 'タスク管理']
            },
            'ai_task': {
                'name': 'AIタスクコンシェルジュ',
                'description': 'タスク管理・プロジェクト管理・進捗追跡',
                'price': 2480,
                'features': ['タスク管理', 'プロジェクト管理', '進捗追跡', 'チーム連携']
            }
        }
    
    def get_available_contents(self):
        """利用可能なコンテンツ一覧を取得"""
        return {
            'success': True,
            'contents': self.available_contents
        }
    
    def add_company_content(self, company_id, content_type, status='active'):
        """企業にコンテンツを追加"""
        try:
            if content_type not in self.available_contents:
                return {
                    'success': False,
                    'error': f'無効なコンテンツタイプ: {content_type}'
                }
            
            conn = get_db_connection()
            c = conn.cursor()
            
            # 既存のコンテンツをチェック
            c.execute('''
                SELECT id FROM company_contents
                WHERE company_id = %s AND content_type = %s
            ''', (company_id, content_type))
            
            if c.fetchone():
                return {
                    'success': False,
                    'error': f'コンテンツ {content_type} は既に追加されています'
                }
            
            # コンテンツを追加
            c.execute('''
                INSERT INTO company_contents (
                    company_id, content_type, content_name, content_description,
                    status, features, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                company_id, content_type,
                self.available_contents[content_type]['name'],
                self.available_contents[content_type]['description'],
                status,
                json.dumps(self.available_contents[content_type]['features']),
                datetime.now(), datetime.now()
            ))
            
            conn.commit()
            conn.close()
            
            # LINE通知を送信
            content_name = self.available_contents[content_type]['name']
            line_api_service.send_notification_to_company(
                company_id,
                'content_added',
                f'コンテンツ「{content_name}」が追加されました。'
            )
            
            return {
                'success': True,
                'message': f'コンテンツ {content_type} が正常に追加されました',
                'content_name': self.available_contents[content_type]['name']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def remove_company_content(self, company_id, content_type):
        """企業からコンテンツを削除"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # コンテンツ情報を取得
            c.execute('''
                SELECT content_name FROM company_contents
                WHERE company_id = %s AND content_type = %s
            ''', (company_id, content_type))
            
            result = c.fetchone()
            if not result:
                return {
                    'success': False,
                    'error': f'コンテンツ {content_type} が見つかりません'
                }
            
            content_name = result[0]
            
            # コンテンツを削除
            c.execute('''
                DELETE FROM company_contents
                WHERE company_id = %s AND content_type = %s
            ''', (company_id, content_type))
            
            conn.commit()
            conn.close()
            
            # LINE通知を送信
            line_api_service.send_notification_to_company(
                company_id,
                'content_removed',
                f'コンテンツ「{content_name}」が削除されました。'
            )
            
            return {
                'success': True,
                'message': f'コンテンツ {content_type} が正常に削除されました',
                'content_name': content_name
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_content_status(self, company_id, content_type, status):
        """コンテンツのステータスを更新"""
        try:
            valid_statuses = ['active', 'inactive', 'suspended']
            if status not in valid_statuses:
                return {
                    'success': False,
                    'error': f'無効なステータス: {status}'
                }
            
            conn = get_db_connection()
            c = conn.cursor()
            
            # コンテンツ情報を取得
            c.execute('''
                SELECT content_name FROM company_contents
                WHERE company_id = %s AND content_type = %s
            ''', (company_id, content_type))
            
            result = c.fetchone()
            if not result:
                return {
                    'success': False,
                    'error': f'コンテンツ {content_type} が見つかりません'
                }
            
            content_name = result[0]
            
            # ステータスを更新
            c.execute('''
                UPDATE company_contents
                SET status = %s, updated_at = %s
                WHERE company_id = %s AND content_type = %s
            ''', (status, datetime.now(), company_id, content_type))
            
            conn.commit()
            conn.close()
            
            # LINE通知を送信
            status_text = {
                'active': '有効化',
                'inactive': '無効化',
                'suspended': '一時停止'
            }.get(status, status)
            
            line_api_service.send_notification_to_company(
                company_id,
                'content_status_changed',
                f'コンテンツ「{content_name}」が{status_text}されました。'
            )
            
            return {
                'success': True,
                'message': f'コンテンツ {content_type} のステータスが {status} に更新されました',
                'content_name': content_name,
                'status': status
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_company_contents(self, company_id):
        """企業のコンテンツ一覧を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT 
                    content_type, content_name, content_description,
                    status, features, created_at, updated_at
                FROM company_contents
                WHERE company_id = %s
                ORDER BY created_at DESC
            ''', (company_id,))
            
            contents = []
            for row in c.fetchall():
                contents.append({
                    'content_type': row[0],
                    'content_name': row[1],
                    'content_description': row[2],
                    'status': row[3],
                    'features': json.loads(row[4]) if row[4] else [],
                    'created_at': row[5].isoformat() if row[5] else None,
                    'updated_at': row[6].isoformat() if row[6] else None
                })
            
            conn.close()
            
            return {
                'success': True,
                'contents': contents,
                'total_count': len(contents)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_all_company_contents(self):
        """全企業のコンテンツ一覧を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT 
                    cc.company_id,
                    c.company_name,
                    cc.content_type,
                    cc.content_name,
                    cc.status,
                    cc.created_at
                FROM company_contents cc
                JOIN companies c ON cc.company_id = c.id
                ORDER BY cc.created_at DESC
            ''')
            
            contents = []
            for row in c.fetchall():
                contents.append({
                    'company_id': row[0],
                    'company_name': row[1],
                    'content_type': row[2],
                    'content_name': row[3],
                    'status': row[4],
                    'created_at': row[5].isoformat() if row[5] else None
                })
            
            conn.close()
            
            return {
                'success': True,
                'contents': contents,
                'total_count': len(contents)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_content_notification(self, company_id, content_type, message_type, custom_message=None):
        """コンテンツ関連の通知を送信"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # コンテンツ情報を取得
            c.execute('''
                SELECT content_name FROM company_contents
                WHERE company_id = %s AND content_type = %s
            ''', (company_id, content_type))
            
            result = c.fetchone()
            if not result:
                return {
                    'success': False,
                    'error': f'コンテンツ {content_type} が見つかりません'
                }
            
            content_name = result[0]
            
            # デフォルトメッセージ
            default_messages = {
                'usage_reminder': f'{content_name}の利用状況をお知らせします。',
                'feature_update': f'{content_name}に新機能が追加されました。',
                'maintenance': f'{content_name}のメンテナンスを実施します。',
                'custom': custom_message or f'{content_name}からのお知らせです。'
            }
            
            message = default_messages.get(message_type, default_messages['custom'])
            
            # LINE通知を送信
            result = line_api_service.send_notification_to_company(
                company_id,
                'content_notification',
                message
            )
            
            conn.close()
            
            return {
                'success': True,
                'message': f'コンテンツ通知が送信されました: {content_name}',
                'details': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_content_statistics(self, company_id=None):
        """コンテンツ利用統計を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            if company_id:
                # 特定企業の統計
                c.execute('''
                    SELECT 
                        content_type,
                        content_name,
                        status,
                        created_at
                    FROM company_contents
                    WHERE company_id = %s
                ''', (company_id,))
                
                contents = c.fetchall()
                stats = {
                    'total_contents': len(contents),
                    'active_contents': len([c for c in contents if c[2] == 'active']),
                    'inactive_contents': len([c for c in contents if c[2] == 'inactive']),
                    'suspended_contents': len([c for c in contents if c[2] == 'suspended']),
                    'contents': [
                        {
                            'content_type': row[0],
                            'content_name': row[1],
                            'status': row[2],
                            'created_at': row[3].isoformat() if row[3] else None
                        }
                        for row in contents
                    ]
                }
            else:
                # 全体の統計
                c.execute('''
                    SELECT 
                        content_type,
                        COUNT(*) as count,
                        COUNT(CASE WHEN status = 'active' THEN 1 END) as active_count
                    FROM company_contents
                    GROUP BY content_type
                ''')
                
                content_stats = c.fetchall()
                stats = {
                    'total_contents': sum(row[1] for row in content_stats),
                    'total_active': sum(row[2] for row in content_stats),
                    'content_breakdown': [
                        {
                            'content_type': row[0],
                            'total_count': row[1],
                            'active_count': row[2]
                        }
                        for row in content_stats
                    ]
                }
            
            conn.close()
            
            return {
                'success': True,
                'statistics': stats
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# シングルトンインスタンス
content_management_service = ContentManagementService() 