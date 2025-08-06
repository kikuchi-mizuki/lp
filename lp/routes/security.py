from flask import Blueprint, request, jsonify
from lp.services.security_service import security_service, require_auth, require_admin
import json
from datetime import datetime

security_bp = Blueprint('security', __name__, url_prefix='/api/v1/security')

@security_bp.route('/login', methods=['POST'])
def login():
    """ユーザーログイン"""
    try:
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'ユーザー名とパスワードは必須です'
            }), 400
        
        # アカウントロックアウトをチェック
        lockout_result = security_service.check_account_lockout(username)
        if lockout_result['is_locked']:
            return jsonify({
                'success': False,
                'error': f'アカウントがロックされています。{lockout_result["lockout_duration"]}分後に再試行してください。'
            }), 423
        
        # ユーザー認証（簡易的な実装）
        # 本番環境ではデータベースからユーザー情報を取得して認証
        if username == 'admin' and password == 'admin123':
            # ログイン成功を記録
            security_service.track_login_attempt(username, success=True)
            
            # セッションを作成
            session_result = security_service.create_user_session(username, 'admin')
            
            if session_result['success']:
                # 監査ログを作成
                security_service.create_audit_log(username, 'login', {
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', '')
                })
                
                return jsonify({
                    'success': True,
                    'message': 'ログインに成功しました',
                    'token': session_result['token'],
                    'expires_at': session_result['expires_at']
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'セッション作成に失敗しました'
                }), 500
        else:
            # ログイン失敗を記録
            security_service.track_login_attempt(username, success=False)
            
            return jsonify({
                'success': False,
                'error': 'ユーザー名またはパスワードが正しくありません'
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'ログインエラー: {str(e)}'
        }), 500

@security_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """ユーザーログアウト"""
    try:
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1]
        
        # セッションを無効化
        revoke_result = security_service.revoke_session(token)
        
        if revoke_result['success']:
            # 監査ログを作成
            security_service.create_audit_log(request.user_id, 'logout', {
                'ip_address': request.remote_addr
            })
            
            return jsonify({
                'success': True,
                'message': 'ログアウトしました'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'ログアウトに失敗しました'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'ログアウトエラー: {str(e)}'
        }), 500

@security_bp.route('/validate', methods=['POST'])
def validate_token():
    """トークンを検証"""
    try:
        data = request.get_json() or {}
        token = data.get('token')
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'トークンは必須です'
            }), 400
        
        # セッションを検証
        session_result = security_service.validate_session(token)
        
        if session_result['valid']:
            return jsonify({
                'success': True,
                'message': 'トークンが有効です',
                'user_id': session_result['user_id'],
                'user_type': session_result['user_type']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': session_result['error']
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'トークン検証エラー: {str(e)}'
        }), 500

@security_bp.route('/password/validate', methods=['POST'])
def validate_password_strength():
    """パスワード強度を検証"""
    try:
        data = request.get_json() or {}
        password = data.get('password')
        
        if not password:
            return jsonify({
                'success': False,
                'error': 'パスワードは必須です'
            }), 400
        
        # パスワード強度を検証
        validation_result = security_service.validate_password_strength(password)
        
        return jsonify({
            'success': True,
            'valid': validation_result['valid'],
            'errors': validation_result['errors']
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'パスワード検証エラー: {str(e)}'
        }), 500

@security_bp.route('/password/hash', methods=['POST'])
@require_admin
def hash_password():
    """パスワードをハッシュ化"""
    try:
        data = request.get_json() or {}
        password = data.get('password')
        
        if not password:
            return jsonify({
                'success': False,
                'error': 'パスワードは必須です'
            }), 400
        
        # パスワードをハッシュ化
        hashed_password = security_service.hash_password(password)
        
        if hashed_password:
            return jsonify({
                'success': True,
                'hashed_password': hashed_password
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'パスワードハッシュ化に失敗しました'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'パスワードハッシュ化エラー: {str(e)}'
        }), 500

@security_bp.route('/audit-logs', methods=['GET'])
@require_admin
def get_audit_logs():
    """監査ログを取得"""
    try:
        user_id = request.args.get('user_id')
        action = request.args.get('action')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 100, type=int)
        
        result = security_service.get_audit_logs(
            user_id, action, start_date, end_date, limit
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'監査ログ取得エラー: {str(e)}'
        }), 500

@security_bp.route('/audit-logs', methods=['POST'])
@require_auth
def create_audit_log():
    """監査ログを作成"""
    try:
        data = request.get_json() or {}
        action = data.get('action')
        details = data.get('details')
        
        if not action:
            return jsonify({
                'success': False,
                'error': 'アクションは必須です'
            }), 400
        
        result = security_service.create_audit_log(
            request.user_id, action, details
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'監査ログ作成エラー: {str(e)}'
        }), 500

@security_bp.route('/sessions', methods=['GET'])
@require_admin
def get_active_sessions():
    """アクティブセッション一覧を取得"""
    try:
        conn = security_service.get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT id, user_id, user_type, created_at, expires_at, ip_address, user_agent
            FROM user_sessions 
            WHERE is_active = true
            ORDER BY created_at DESC
        ''')
        
        rows = c.fetchall()
        conn.close()
        
        sessions = []
        for row in rows:
            sessions.append({
                'id': row[0],
                'user_id': row[1],
                'user_type': row[2],
                'created_at': row[3],
                'expires_at': row[4],
                'ip_address': row[5],
                'user_agent': row[6]
            })
        
        return jsonify({
            'success': True,
            'sessions': sessions,
            'total_count': len(sessions)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'セッション取得エラー: {str(e)}'
        }), 500

@security_bp.route('/sessions/<int:session_id>/revoke', methods=['POST'])
@require_admin
def revoke_session(session_id):
    """セッションを無効化"""
    try:
        conn = security_service.get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            UPDATE user_sessions 
            SET is_active = false, revoked_at = %s
            WHERE id = %s
        ''', (datetime.now().isoformat(), session_id))
        
        conn.commit()
        conn.close()
        
        # 監査ログを作成
        security_service.create_audit_log(request.user_id, 'revoke_session', {
            'session_id': session_id,
            'revoked_by': request.user_id
        })
        
        return jsonify({
            'success': True,
            'message': f'セッション {session_id} を無効化しました'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'セッション無効化エラー: {str(e)}'
        }), 500

@security_bp.route('/login-attempts', methods=['GET'])
@require_admin
def get_login_attempts():
    """ログイン試行履歴を取得"""
    try:
        user_id = request.args.get('user_id')
        success = request.args.get('success')
        limit = request.args.get('limit', 100, type=int)
        
        conn = security_service.get_db_connection()
        c = conn.cursor()
        
        query = '''
            SELECT id, user_id, ip_address, success, attempted_at
            FROM login_attempts
            WHERE 1=1
        '''
        params = []
        
        if user_id:
            query += ' AND user_id = %s'
            params.append(user_id)
        
        if success is not None:
            query += ' AND success = %s'
            params.append(success.lower() == 'true')
        
        query += ' ORDER BY attempted_at DESC LIMIT %s'
        params.append(limit)
        
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        
        attempts = []
        for row in rows:
            attempts.append({
                'id': row[0],
                'user_id': row[1],
                'ip_address': row[2],
                'success': row[3],
                'attempted_at': row[4]
            })
        
        return jsonify({
            'success': True,
            'attempts': attempts,
            'total_count': len(attempts)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'ログイン試行履歴取得エラー: {str(e)}'
        }), 500

@security_bp.route('/statistics', methods=['GET'])
@require_admin
def get_security_statistics():
    """セキュリティ統計を取得"""
    try:
        result = security_service.get_security_statistics()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'セキュリティ統計取得エラー: {str(e)}'
        }), 500

@security_bp.route('/encrypt', methods=['POST'])
@require_admin
def encrypt_data():
    """データを暗号化"""
    try:
        data = request.get_json() or {}
        text = data.get('text')
        
        if not text:
            return jsonify({
                'success': False,
                'error': '暗号化するテキストは必須です'
            }), 400
        
        encrypted = security_service.encrypt_data(text)
        
        if encrypted:
            return jsonify({
                'success': True,
                'encrypted_data': encrypted
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'データ暗号化に失敗しました'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'データ暗号化エラー: {str(e)}'
        }), 500

@security_bp.route('/decrypt', methods=['POST'])
@require_admin
def decrypt_data():
    """データを復号化"""
    try:
        data = request.get_json() or {}
        encrypted_data = data.get('encrypted_data')
        
        if not encrypted_data:
            return jsonify({
                'success': False,
                'error': '復号化するデータは必須です'
            }), 400
        
        decrypted = security_service.decrypt_data(encrypted_data)
        
        if decrypted:
            return jsonify({
                'success': True,
                'decrypted_data': decrypted
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'データ復号化に失敗しました'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'データ復号化エラー: {str(e)}'
        }), 500

@security_bp.route('/api-key/validate', methods=['POST'])
def validate_api_key():
    """APIキーを検証"""
    try:
        data = request.get_json() or {}
        api_key = data.get('api_key')
        
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'APIキーは必須です'
            }), 400
        
        result = security_service.validate_api_key(api_key)
        
        return jsonify(result), 200 if result['valid'] else 401
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'APIキー検証エラー: {str(e)}'
        }), 500

@security_bp.route('/config', methods=['GET'])
@require_admin
def get_security_config():
    """セキュリティ設定を取得"""
    try:
        return jsonify({
            'success': True,
            'config': security_service.security_config
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'セキュリティ設定取得エラー: {str(e)}'
        }), 500

@security_bp.route('/config', methods=['PUT'])
@require_admin
def update_security_config():
    """セキュリティ設定を更新"""
    try:
        data = request.get_json() or {}
        
        # 更新可能な設定のみを抽出
        allowed_configs = [
            'max_login_attempts', 'lockout_duration', 'session_timeout',
            'password_min_length', 'require_special_chars', 'require_numbers',
            'require_uppercase', 'max_session_age', 'rate_limit_requests',
            'rate_limit_window'
        ]
        
        updated_configs = {}
        for key in allowed_configs:
            if key in data:
                updated_configs[key] = data[key]
        
        if not updated_configs:
            return jsonify({
                'success': False,
                'error': '更新する設定が指定されていません'
            }), 400
        
        # 設定を更新
        security_service.security_config.update(updated_configs)
        
        # 監査ログを作成
        security_service.create_audit_log(request.user_id, 'update_security_config', {
            'updated_configs': updated_configs
        })
        
        return jsonify({
            'success': True,
            'message': 'セキュリティ設定を更新しました',
            'updated_configs': updated_configs
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'セキュリティ設定更新エラー: {str(e)}'
        }), 500

@security_bp.route('/health', methods=['GET'])
def health_check():
    """ヘルスチェック"""
    try:
        # 基本的なセキュリティ機能をチェック
        test_password = "TestPassword123!"
        hashed = security_service.hash_password(test_password)
        verified = security_service.verify_password(test_password, hashed)
        
        if hashed and verified:
            return jsonify({
                'success': True,
                'message': 'セキュリティサービスは正常に動作しています',
                'service_status': 'healthy',
                'timestamp': '2024-07-30T12:00:00Z'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'セキュリティサービスに問題があります',
                'service_status': 'error'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'セキュリティサービスに問題があります',
            'service_status': 'error',
            'error': str(e)
        }), 500 