#!/usr/bin/env python3
"""
スプレッドシート連携コンテンツ管理サービス
Google Sheets APIを使用してコンテンツ情報を動的に管理
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import gspread
from google.oauth2.service_account import Credentials
from utils.db import get_db_connection

class SpreadsheetContentService:
    """スプレッドシート連携コンテンツ管理サービス"""
    
    def __init__(self):
        self.spreadsheet_id = os.getenv('CONTENT_SPREADSHEET_ID')
        self.credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        self.cache_duration = 300  # 5分間キャッシュ
        self.last_cache_update = 0
        self.cached_contents = {}
        
    def _get_google_sheets_client(self):
        """Google Sheets APIクライアントを取得"""
        try:
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            if os.path.exists(self.credentials_file):
                creds = Credentials.from_service_account_file(
                    self.credentials_file, scopes=scope
                )
            else:
                # 環境変数から認証情報を取得
                creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
                if creds_json:
                    creds = Credentials.from_service_account_info(
                        json.loads(creds_json), scopes=scope
                    )
                else:
                    raise Exception("Google認証情報が見つかりません")
            
            return gspread.authorize(creds)
        except Exception as e:
            print(f"Google Sheets API接続エラー: {e}")
            return None
    
    def _fetch_contents_from_spreadsheet(self) -> Dict:
        """スプレッドシートからコンテンツ情報を取得"""
        try:
            client = self._get_google_sheets_client()
            if not client:
                return {}
            
            spreadsheet = client.open_by_key(self.spreadsheet_id)
            worksheet = spreadsheet.get_worksheet(0)  # 最初のシート
            
            # ヘッダー行を除いてデータを取得
            all_values = worksheet.get_all_values()
            if len(all_values) < 2:
                return {}
            
            headers = all_values[0]
            data_rows = all_values[1:]
            
            contents = {}
            for row in data_rows:
                if len(row) >= 6:  # 最低限必要な列数
                    content_id = row[0].strip()
                    if content_id and row[5].lower() == 'active':  # ステータスがactive
                        contents[content_id] = {
                            'name': row[1].strip(),
                            'description': row[2].strip(),
                            'url': row[3].strip(),
                            'price': int(row[4]) if row[4].isdigit() else 0,
                            'status': row[5].strip(),
                            'created_at': row[6] if len(row) > 6 else datetime.now().strftime('%Y-%m-%d'),
                            'features': self._parse_features(row[7]) if len(row) > 7 else []
                        }
            
            return contents
            
        except Exception as e:
            print(f"スプレッドシート取得エラー: {e}")
            return {}
    
    def _parse_features(self, features_str: str) -> List[str]:
        """機能リストをパース"""
        if not features_str:
            return []
        return [f.strip() for f in features_str.split(',') if f.strip()]
    
    def get_available_contents(self, force_refresh=False) -> Dict:
        """利用可能なコンテンツ一覧を取得（キャッシュ付き）"""
        current_time = time.time()
        
        # キャッシュが有効で、強制更新でない場合はキャッシュを返す
        if (not force_refresh and 
            current_time - self.last_cache_update < self.cache_duration and 
            self.cached_contents):
            return {
                'success': True,
                'contents': self.cached_contents,
                'cached': True
            }
        
        # スプレッドシートから最新データを取得
        contents = self._fetch_contents_from_spreadsheet()
        
        if contents:
            self.cached_contents = contents
            self.last_cache_update = current_time
            
            return {
                'success': True,
                'contents': contents,
                'cached': False
            }
        else:
            # スプレッドシートが利用できない場合はデフォルトコンテンツを返す
            return {
                'success': True,
                'contents': self._get_default_contents(),
                'cached': False,
                'fallback': True
            }
    
    def _get_default_contents(self) -> Dict:
        """デフォルトのコンテンツ情報（フォールバック用）"""
        return {
            'ai_accounting': {
                'name': 'AI経理秘書',
                'description': '経理作業をAIが効率化',
                'url': 'https://lp-production-9e2c.up.railway.app/accounting',
                'price': 2980,
                'status': 'active',
                'created_at': '2024-01-01',
                'features': ['自動仕訳', '帳簿作成', '税務申告', '経営分析']
            },
            'ai_schedule': {
                'name': 'AI予定秘書',
                'description': 'スケジュール管理をAIがサポート',
                'url': 'https://lp-production-9e2c.up.railway.app/schedule',
                'price': 1980,
                'status': 'active',
                'created_at': '2024-01-01',
                'features': ['スケジュール管理', '会議調整', 'リマインダー', 'タスク管理']
            },
            'ai_task': {
                'name': 'AIタスクコンシェルジュ',
                'description': 'タスク管理をAIが最適化',
                'url': 'https://lp-production-9e2c.up.railway.app/task',
                'price': 2480,
                'status': 'active',
                'created_at': '2024-01-01',
                'features': ['タスク管理', 'プロジェクト管理', '進捗追跡', 'チーム連携']
            }
        }
    
    def get_content_by_id(self, content_id: str) -> Optional[Dict]:
        """特定のコンテンツ情報を取得"""
        contents = self.get_available_contents()
        if contents['success']:
            return contents['contents'].get(content_id)
        return None
    
    def refresh_cache(self):
        """キャッシュを強制更新"""
        self.last_cache_update = 0
        self.cached_contents = {}
        return self.get_available_contents(force_refresh=True)
    
    def add_content_to_spreadsheet(self, content_data: Dict) -> Dict:
        """スプレッドシートに新しいコンテンツを追加"""
        try:
            client = self._get_google_sheets_client()
            if not client:
                return {'success': False, 'error': 'Google Sheets API接続エラー'}
            
            spreadsheet = client.open_by_key(self.spreadsheet_id)
            worksheet = spreadsheet.get_worksheet(0)
            
            # 新しい行を追加
            new_row = [
                content_data.get('id', ''),
                content_data.get('name', ''),
                content_data.get('description', ''),
                content_data.get('url', ''),
                str(content_data.get('price', 0)),
                content_data.get('status', 'active'),
                datetime.now().strftime('%Y-%m-%d'),
                ','.join(content_data.get('features', []))
            ]
            
            worksheet.append_row(new_row)
            
            # キャッシュを更新
            self.refresh_cache()
            
            return {
                'success': True,
                'message': f'コンテンツ「{content_data.get("name")}」が追加されました'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'スプレッドシート追加エラー: {str(e)}'
            }
    
    def update_content_status(self, content_id: str, status: str) -> Dict:
        """コンテンツのステータスを更新"""
        try:
            client = self._get_google_sheets_client()
            if not client:
                return {'success': False, 'error': 'Google Sheets API接続エラー'}
            
            spreadsheet = client.open_by_key(self.spreadsheet_id)
            worksheet = spreadsheet.get_worksheet(0)
            
            # コンテンツIDで行を検索
            all_values = worksheet.get_all_values()
            for i, row in enumerate(all_values[1:], start=2):  # ヘッダー行を除く
                if row[0] == content_id:
                    # ステータス列（5番目）を更新
                    worksheet.update_cell(i, 6, status)
                    
                    # キャッシュを更新
                    self.refresh_cache()
                    
                    return {
                        'success': True,
                        'message': f'コンテンツ「{content_id}」のステータスを{status}に更新しました'
                    }
            
            return {
                'success': False,
                'error': f'コンテンツID「{content_id}」が見つかりません'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'ステータス更新エラー: {str(e)}'
            }

# グローバルインスタンス
spreadsheet_content_service = SpreadsheetContentService()
