#!/usr/bin/env python3
"""
スプレッドシート連携コンテンツ管理サービス
Google Sheets APIを使用してコンテンツ情報を動的に管理
"""

import os
import json
import time
import threading
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
        self.cache_duration = 60  # 1分間キャッシュ（5分から短縮）
        self.last_cache_update = 0
        self.cached_contents = {}
        self.auto_refresh_enabled = True
        self.auto_refresh_interval = 300  # 5分ごとに自動更新
        self._start_auto_refresh()
        
    def _start_auto_refresh(self):
        """自動更新スレッドを開始"""
        if self.auto_refresh_enabled:
            def auto_refresh_worker():
                while self.auto_refresh_enabled:
                    try:
                        time.sleep(self.auto_refresh_interval)
                        self.refresh_cache()
                        print(f"[AUTO_REFRESH] スプレッドシートの自動更新を実行しました: {datetime.now()}")
                    except Exception as e:
                        print(f"[AUTO_REFRESH_ERROR] 自動更新エラー: {e}")
            
            refresh_thread = threading.Thread(target=auto_refresh_worker, daemon=True)
            refresh_thread.start()
            print(f"[AUTO_REFRESH] 自動更新スレッドを開始しました（{self.auto_refresh_interval}秒間隔）")
    
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
                # 期待される列: [id, name, description, url, price, (optional) status, (optional) created_at, (optional) features]
                if len(row) >= 5:
                    content_id = (row[0] or '').strip()
                    if not content_id:
                        continue

                    name = (row[1] or '').strip()
                    description = (row[2] or '').strip()
                    url = (row[3] or '').strip()
                    price_raw = (row[4] or '').strip()
                    try:
                        price = int(price_raw)
                    except Exception:
                        price = 0

                    status = (row[5] or 'active').strip().lower() if len(row) > 5 else 'active'
                    created_at = row[6] if len(row) > 6 and row[6] else datetime.now().strftime('%Y-%m-%d')
                    features = self._parse_features(row[7]) if len(row) > 7 else []

                    # ステータスがinactiveのものは除外
                    if status and status.lower() not in ['inactive', 'disabled', 'off']:
                        # 画像URLを判定（statusフィールドが画像URLの場合）
                        image_url = None
                        if status and (status.startswith('http') and any(ext in status.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg'])):
                            image_url = status
                            status = 'active'  # 画像URLの場合はステータスをactiveに設定
                        
                        contents[content_id] = {
                            'name': name,
                            'description': description,
                            'url': url,
                            'price': price,
                            'status': status,
                            'image': image_url,  # 画像URLを追加
                            'created_at': created_at,
                            'features': features,
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
                'price': 1500,
                'status': 'active',
                'image': '/static/images/line_accounting_optimized.jpg',
                'created_at': '2024-01-01',
                'features': ['自動仕訳', '帳簿作成', '税務申告', '経営分析']
            },
            'ai_schedule': {
                'name': 'AI予定秘書',
                'description': 'スケジュール管理をAIがサポート',
                'url': 'https://lp-production-9e2c.up.railway.app/schedule',
                'price': 1500,
                'status': 'active',
                'image': '/static/images/line_schedule_optimized.jpg',
                'created_at': '2024-01-01',
                'features': ['スケジュール管理', '会議調整', 'リマインダー', 'タスク管理']
            },
            'ai_task': {
                'name': 'AIタスクコンシェルジュ',
                'description': 'タスク管理をAIが最適化',
                'url': 'https://lp-production-9e2c.up.railway.app/task',
                'price': 1500,
                'status': 'active',
                'image': '/static/images/line_task_optimized.jpg',
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
