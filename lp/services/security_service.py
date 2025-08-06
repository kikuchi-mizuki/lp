import os
import json
import hashlib
import hmac
import base64
import logging
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from lp.utils.db import get_db_connection

class SecurityService:
    """セキュリティサービス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
        self.jwt_secret = os.getenv('JWT_SECRET', 'your-jwt-secret-change-this')
        
        # セキュリティ設定
        self.security_config = {
            'max_login_attempts': 5,
            'lockout_duration': 30,  # 分
            'session_timeout': 60,   # 分
            'password_min_length': 8,
            'require_special_chars': True,
            'require_numbers': True,
            'require_uppercase': True,
            'max_session_age': 24 * 60,  # 時間
            'rate_limit_requests': 100,  # リクエスト数
            'rate_limit_window': 60,     # 秒
        }
    
    def hash_password(self, password):
        """パスワードをハッシュ化"""
        try:
            salt = os.urandom(32)
            key = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt,
                100000  # イテレーション回数
            )
            return base64.b64encode(salt + key).decode('utf-8')
        except Exception as e:
            self.logger.error(f"パスワードハッシュ化エラー: {e}")
            return None
    
    def verify_password(self, password, hashed_password):
        """パスワードを検証"""
        try:
            decoded = base64.b64decode(hashed_password.encode('utf-8'))
            salt = decoded[:32]
            key = decoded[32:]
            
            new_key = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt,
                100000
            )
            
            return hmac.compare_digest(key, new_key)
        except Exception as e:
            self.logger.error(f"パスワード検証エラー: {e}")
            return False
    
    def validate_password_strength(self, password):
        """パスワード強度を検証"""
        try:
            errors = []
            
            if len(password) < self.security_config['password_min_length']:
                errors.append(f"パスワードは{self.security_config['password_min_length']}文字以上である必要があります")
            
            if self.security_config['require_uppercase'] and not any(c.isupper() for c in password):
                errors.append("大文字を含む必要があります")
            
            if self.security_config['require_numbers'] and not any(c.isdigit() for c in password):
                errors.append("数字を含む必要があります")
            
            if self.security_config['require_special_chars'] and not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
                errors.append("特殊文字を含む必要があります")
            
            return {
                'valid': len(errors) == 0,
                'errors': errors
            }
        except Exception as e:
            self.logger.error(f"パスワード強度検証エラー: {e}")
            return {
                'valid': False,
                'errors': ['パスワード検証中にエラーが発生しました']
            }
    
    def generate_jwt_token(self, user_id, user_type='admin', expires_in=None):
        """JWTトークンを生成"""
        try:
            if expires_in is None:
                expires_in = self.security_config['session_timeout'] * 60  # 秒
            
            payload = {
                'user_id': user_id,
                'user_type': user_type,
                'exp': datetime.utcnow() + timedelta(seconds=expires_in),
                'iat': datetime.utcnow(),
                'iss': 'ai-collections-api'
            }
            
            token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
            return token
        except Exception as e:
            self.logger.error(f"JWTトークン生成エラー: {e}")
            return None
    
    def verify_jwt_token(self, token):
        """JWTトークンを検証"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return {
                'valid': True,
                'payload': payload
            }
        except jwt.ExpiredSignatureError:
            return {
                'valid': False,
                'error': 'トークンの有効期限が切れています'
            }
        except jwt.InvalidTokenError as e:
            return {
                'valid': False,
                'error': f'無効なトークン: {str(e)}'
            }
        except Exception as e:
            self.logger.error(f"JWTトークン検証エラー: {e}")
            return {
                'valid': False,
                'error': 'トークン検証中にエラーが発生しました'
            }
    
    def create_user_session(self, user_id, user_type='admin'):
        """ユーザーセッションを作成"""
        try:
            token = self.generate_jwt_token(user_id, user_type)
            if not token:
                return {
                    'success': False,
                    'error': 'トークン生成に失敗しました'
                }
            
            # セッション情報をデータベースに保存
            conn = get_db_connection()
            c = conn.cursor()
            
            session_data = {
                'user_id': user_id,
                'user_type': user_type,
                'token_hash': hashlib.sha256(token.encode()).hexdigest(),
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(minutes=self.security_config['session_timeout'])).isoformat(),
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            }
            
            c.execute('''
                INSERT INTO user_sessions 
                (user_id, user_type, token_hash, created_at, expires_at, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                session_data['user_id'],
                session_data['user_type'],
                session_data['token_hash'],
                session_data['created_at'],
                session_data['expires_at'],
                session_data['ip_address'],
                session_data['user_agent']
            ))
            
            session_id = c.fetchone()[0]
            conn.commit()
            conn.close()
            
            self.logger.info(f"ユーザーセッション作成: user_id={user_id}, session_id={session_id}")
            
            return {
                'success': True,
                'token': token,
                'session_id': session_id,
                'expires_at': session_data['expires_at']
            }
            
        except Exception as e:
            self.logger.error(f"ユーザーセッション作成エラー: {e}")
            return {
                'success': False,
                'error': f'セッション作成エラー: {str(e)}'
            }
    
    def validate_session(self, token):
        """セッションを検証"""
        try:
            # JWTトークンを検証
            jwt_result = self.verify_jwt_token(token)
            if not jwt_result['valid']:
                return jwt_result
            
            payload = jwt_result['payload']
            
            # データベースでセッションを確認
            conn = get_db_connection()
            c = conn.cursor()
            
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            c.execute('''
                SELECT id, user_id, user_type, created_at, expires_at, ip_address, is_active
                FROM user_sessions 
                WHERE token_hash = %s AND is_active = true
            ''', (token_hash,))
            
            session = c.fetchone()
            conn.close()
            
            if not session:
                return {
                    'valid': False,
                    'error': 'セッションが見つかりません'
                }
            
            session_id, user_id, user_type, created_at, expires_at, ip_address, is_active = session
            
            # セッションの有効期限をチェック
            if datetime.fromisoformat(expires_at) < datetime.now():
                return {
                    'valid': False,
                    'error': 'セッションの有効期限が切れています'
                }
            
            return {
                'valid': True,
                'session_id': session_id,
                'user_id': user_id,
                'user_type': user_type,
                'payload': payload
            }
            
        except Exception as e:
            self.logger.error(f"セッション検証エラー: {e}")
            return {
                'valid': False,
                'error': f'セッション検証エラー: {str(e)}'
            }
    
    def revoke_session(self, token):
        """セッションを無効化"""
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                UPDATE user_sessions 
                SET is_active = false, revoked_at = %s
                WHERE token_hash = %s
            ''', (datetime.now().isoformat(), token_hash))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"セッション無効化: token_hash={token_hash}")
            
            return {
                'success': True,
                'message': 'セッションを無効化しました'
            }
            
        except Exception as e:
            self.logger.error(f"セッション無効化エラー: {e}")
            return {
                'success': False,
                'error': f'セッション無効化エラー: {str(e)}'
            }
    
    def track_login_attempt(self, user_id, success=True, ip_address=None):
        """ログイン試行を記録"""
        try:
            if ip_address is None:
                ip_address = request.remote_addr
            
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO login_attempts 
                (user_id, ip_address, success, attempted_at)
                VALUES (%s, %s, %s, %s)
            ''', (
                user_id,
                ip_address,
                success,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"ログイン試行記録: user_id={user_id}, success={success}, ip={ip_address}")
            
            return {
                'success': True,
                'message': 'ログイン試行を記録しました'
            }
            
        except Exception as e:
            self.logger.error(f"ログイン試行記録エラー: {e}")
            return {
                'success': False,
                'error': f'ログイン試行記録エラー: {str(e)}'
            }
    
    def check_account_lockout(self, user_id, ip_address=None):
        """アカウントロックアウトをチェック"""
        try:
            if ip_address is None:
                ip_address = request.remote_addr
            
            conn = get_db_connection()
            c = conn.cursor()
            
            # 最近の失敗したログイン試行をチェック
            lockout_threshold = datetime.now() - timedelta(minutes=self.security_config['lockout_duration'])
            
            c.execute('''
                SELECT COUNT(*) 
                FROM login_attempts 
                WHERE user_id = %s AND success = false AND attempted_at > %s
            ''', (user_id, lockout_threshold.isoformat()))
            
            failed_attempts = c.fetchone()[0]
            conn.close()
            
            is_locked = failed_attempts >= self.security_config['max_login_attempts']
            
            return {
                'is_locked': is_locked,
                'failed_attempts': failed_attempts,
                'max_attempts': self.security_config['max_login_attempts'],
                'lockout_duration': self.security_config['lockout_duration']
            }
            
        except Exception as e:
            self.logger.error(f"アカウントロックアウトチェックエラー: {e}")
            return {
                'is_locked': False,
                'error': f'ロックアウトチェックエラー: {str(e)}'
            }
    
    def create_audit_log(self, user_id, action, details=None, ip_address=None):
        """監査ログを作成"""
        try:
            if ip_address is None:
                ip_address = request.remote_addr
            
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO audit_logs 
                (user_id, action, details, ip_address, created_at)
                VALUES (%s, %s, %s, %s, %s)
            ''', (
                user_id,
                action,
                json.dumps(details) if details else None,
                ip_address,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"監査ログ作成: user_id={user_id}, action={action}")
            
            return {
                'success': True,
                'message': '監査ログを作成しました'
            }
            
        except Exception as e:
            self.logger.error(f"監査ログ作成エラー: {e}")
            return {
                'success': False,
                'error': f'監査ログ作成エラー: {str(e)}'
            }
    
    def get_audit_logs(self, user_id=None, action=None, start_date=None, end_date=None, limit=100):
        """監査ログを取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            query = '''
                SELECT id, user_id, action, details, ip_address, created_at
                FROM audit_logs
                WHERE 1=1
            '''
            params = []
            
            if user_id:
                query += ' AND user_id = %s'
                params.append(user_id)
            
            if action:
                query += ' AND action = %s'
                params.append(action)
            
            if start_date:
                query += ' AND created_at >= %s'
                params.append(start_date)
            
            if end_date:
                query += ' AND created_at <= %s'
                params.append(end_date)
            
            query += ' ORDER BY created_at DESC LIMIT %s'
            params.append(limit)
            
            c.execute(query, params)
            rows = c.fetchall()
            conn.close()
            
            logs = []
            for row in rows:
                logs.append({
                    'id': row[0],
                    'user_id': row[1],
                    'action': row[2],
                    'details': json.loads(row[3]) if row[3] else None,
                    'ip_address': row[4],
                    'created_at': row[5]
                })
            
            return {
                'success': True,
                'logs': logs,
                'total_count': len(logs)
            }
            
        except Exception as e:
            self.logger.error(f"監査ログ取得エラー: {e}")
            return {
                'success': False,
                'error': f'監査ログ取得エラー: {str(e)}'
            }
    
    def encrypt_data(self, data):
        """データを暗号化"""
        try:
            # 簡易的な暗号化（本番環境ではより強固な暗号化を使用）
            import base64
            encoded = base64.b64encode(str(data).encode()).decode()
            return encoded
        except Exception as e:
            self.logger.error(f"データ暗号化エラー: {e}")
            return None
    
    def decrypt_data(self, encrypted_data):
        """データを復号化"""
        try:
            # 簡易的な復号化
            import base64
            decoded = base64.b64decode(encrypted_data.encode()).decode()
            return decoded
        except Exception as e:
            self.logger.error(f"データ復号化エラー: {e}")
            return None
    
    def validate_api_key(self, api_key):
        """APIキーを検証"""
        try:
            # 環境変数から有効なAPIキーを取得
            valid_api_keys = os.getenv('VALID_API_KEYS', '').split(',')
            
            if api_key in valid_api_keys:
                return {
                    'valid': True,
                    'message': 'APIキーが有効です'
                }
            else:
                return {
                    'valid': False,
                    'error': '無効なAPIキーです'
                }
        except Exception as e:
            self.logger.error(f"APIキー検証エラー: {e}")
            return {
                'valid': False,
                'error': f'APIキー検証エラー: {str(e)}'
            }
    
    def get_security_statistics(self):
        """セキュリティ統計を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # アクティブセッション数
            c.execute('SELECT COUNT(*) FROM user_sessions WHERE is_active = true')
            active_sessions = c.fetchone()[0]
            
            # 今日のログイン試行数
            today = datetime.now().date().isoformat()
            c.execute('SELECT COUNT(*) FROM login_attempts WHERE DATE(attempted_at) = %s', (today,))
            today_login_attempts = c.fetchone()[0]
            
            # 失敗したログイン試行数
            c.execute('SELECT COUNT(*) FROM login_attempts WHERE DATE(attempted_at) = %s AND success = false', (today,))
            failed_login_attempts = c.fetchone()[0]
            
            # 今日の監査ログ数
            c.execute('SELECT COUNT(*) FROM audit_logs WHERE DATE(created_at) = %s', (today,))
            today_audit_logs = c.fetchone()[0]
            
            conn.close()
            
            return {
                'success': True,
                'statistics': {
                    'active_sessions': active_sessions,
                    'today_login_attempts': today_login_attempts,
                    'failed_login_attempts': failed_login_attempts,
                    'today_audit_logs': today_audit_logs,
                    'security_level': 'high' if failed_login_attempts < 10 else 'medium' if failed_login_attempts < 50 else 'low'
                }
            }
            
        except Exception as e:
            self.logger.error(f"セキュリティ統計取得エラー: {e}")
            return {
                'success': False,
                'error': f'セキュリティ統計取得エラー: {str(e)}'
            }

# インスタンスを作成
security_service = SecurityService()

# 認証デコレータ
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'success': False,
                'error': '認証ヘッダーがありません'
            }), 401
        
        try:
            token = auth_header.split(' ')[1]  # Bearer token
        except IndexError:
            return jsonify({
                'success': False,
                'error': '無効な認証ヘッダー形式です'
            }), 401
        
        # セッションを検証
        session_result = security_service.validate_session(token)
        if not session_result['valid']:
            return jsonify({
                'success': False,
                'error': session_result['error']
            }), 401
        
        # リクエストにユーザー情報を追加
        request.user_id = session_result['user_id']
        request.user_type = session_result['user_type']
        
        return f(*args, **kwargs)
    
    return decorated_function

# 管理者権限デコレータ
def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'success': False,
                'error': '認証ヘッダーがありません'
            }), 401
        
        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            return jsonify({
                'success': False,
                'error': '無効な認証ヘッダー形式です'
            }), 401
        
        # セッションを検証
        session_result = security_service.validate_session(token)
        if not session_result['valid']:
            return jsonify({
                'success': False,
                'error': session_result['error']
            }), 401
        
        # 管理者権限をチェック
        if session_result['user_type'] != 'admin':
            return jsonify({
                'success': False,
                'error': '管理者権限が必要です'
            }), 403
        
        # リクエストにユーザー情報を追加
        request.user_id = session_result['user_id']
        request.user_type = session_result['user_type']
        
        return f(*args, **kwargs)
    
    return decorated_function 