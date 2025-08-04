from flask import Blueprint, request, jsonify, render_template
import os
import requests
import json
import re
from datetime import datetime

railway_setup_bp = Blueprint('railway_setup', __name__)

class RailwaySetupService:
    """Railway自動設定サービス"""
    
    def __init__(self):
        self.railway_api_base = "https://backboard.railway.app/graphql/v2"
    
    def get_railway_headers(self, token):
        """Railway API用ヘッダーを取得"""
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def validate_token(self, token):
        """Railwayトークンの有効性を検証"""
        try:
            headers = self.get_railway_headers(token)
            
            # ユーザー情報を取得してトークンの有効性を確認
            query = """
            query {
                me {
                    id
                    email
                    name
                }
            }
            """
            
            response = requests.post(
                self.railway_api_base,
                headers=headers,
                json={'query': query},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'me' in data['data']:
                    return {
                        'success': True,
                        'user': data['data']['me']
                    }
                else:
                    return {
                        'success': False,
                        'error': 'トークンが無効です'
                    }
            else:
                return {
                    'success': False,
                    'error': f'APIエラー: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'トークン検証エラー: {str(e)}'
            }
    
    def validate_project(self, token, project_id):
        """プロジェクトIDの有効性を検証"""
        try:
            headers = self.get_railway_headers(token)
            
            # プロジェクト情報を取得
            query = """
            query($id: ID!) {
                project(id: $id) {
                    id
                    name
                    description
                    createdAt
                }
            }
            """
            
            response = requests.post(
                self.railway_api_base,
                headers=headers,
                json={
                    'query': query,
                    'variables': {'id': project_id}
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'project' in data['data']:
                    return {
                        'success': True,
                        'project': data['data']['project']
                    }
                else:
                    return {
                        'success': False,
                        'error': 'プロジェクトが見つかりません'
                    }
            else:
                return {
                    'success': False,
                    'error': f'プロジェクト検証エラー: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'プロジェクト検証エラー: {str(e)}'
            }
    
    def setup_environment_variables(self, token, project_id, base_domain):
        """環境変数を自動設定"""
        try:
            headers = self.get_railway_headers(token)
            
            # 環境変数を設定
            variables = [
                {
                    'name': 'RAILWAY_TOKEN',
                    'value': token
                },
                {
                    'name': 'RAILWAY_PROJECT_ID',
                    'value': project_id
                },
                {
                    'name': 'BASE_DOMAIN',
                    'value': base_domain
                }
            ]
            
            results = []
            
            for var in variables:
                mutation = """
                mutation($projectId: ID!, $name: String!, $value: String!) {
                    variableCreate(
                        input: {
                            projectId: $projectId,
                            name: $name,
                            value: $value
                        }
                    ) {
                        id
                        name
                        value
                    }
                }
                """
                
                response = requests.post(
                    self.railway_api_base,
                    headers=headers,
                    json={
                        'query': mutation,
                        'variables': {
                            'projectId': project_id,
                            'name': var['name'],
                            'value': var['value']
                        }
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and 'variableCreate' in data['data']:
                        results.append({
                            'success': True,
                            'variable': var['name'],
                            'data': data['data']['variableCreate']
                        })
                    else:
                        results.append({
                            'success': False,
                            'variable': var['name'],
                            'error': '環境変数の設定に失敗しました'
                        })
                else:
                    results.append({
                        'success': False,
                        'variable': var['name'],
                        'error': f'APIエラー: {response.status_code}'
                    })
            
            # 結果をまとめる
            success_count = sum(1 for r in results if r['success'])
            total_count = len(results)
            
            if success_count == total_count:
                return {
                    'success': True,
                    'message': f'{total_count}個の環境変数を設定しました',
                    'results': results
                }
            else:
                failed_vars = [r['variable'] for r in results if not r['success']]
                return {
                    'success': False,
                    'error': f'一部の環境変数設定に失敗: {", ".join(failed_vars)}',
                    'results': results
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'環境変数設定エラー: {str(e)}'
            }

# サービスインスタンスを作成
railway_setup_service = RailwaySetupService()

@railway_setup_bp.route('/railway-token-setup')
def railway_token_setup_page():
    """Railwayトークン設定ページ"""
    return render_template('railway_token_setup.html')

@railway_setup_bp.route('/api/v1/railway/validate-token', methods=['POST'])
def validate_token():
    """Railwayトークンの検証"""
    try:
        data = request.get_json()
        if not data or 'token' not in data:
            return jsonify({
                'success': False,
                'error': 'トークンが提供されていません'
            }), 400
        
        token = data['token'].strip()
        
        if not token.startswith('railway_'):
            return jsonify({
                'success': False,
                'error': '有効なRailwayトークンを入力してください'
            }), 400
        
        result = railway_setup_service.validate_token(token)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'トークンが有効です',
                'user': result['user']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'トークン検証エラー: {str(e)}'
        }), 500

@railway_setup_bp.route('/api/v1/railway/validate-project', methods=['POST'])
def validate_project():
    """プロジェクトIDの検証"""
    try:
        data = request.get_json()
        if not data or 'token' not in data or 'project_id' not in data:
            return jsonify({
                'success': False,
                'error': 'トークンとプロジェクトIDが必要です'
            }), 400
        
        token = data['token'].strip()
        project_id = data['project_id'].strip()
        
        # UUID形式の検証
        if not re.match(r'^[a-f0-9-]{36}$', project_id):
            return jsonify({
                'success': False,
                'error': '有効なプロジェクトIDを入力してください'
            }), 400
        
        result = railway_setup_service.validate_project(token, project_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'プロジェクトIDが有効です',
                'project': result['project']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'プロジェクト検証エラー: {str(e)}'
        }), 500

@railway_setup_bp.route('/api/v1/railway/setup-environment', methods=['POST'])
def setup_environment():
    """環境変数の自動設定"""
    try:
        data = request.get_json()
        required_fields = ['token', 'project_id', 'base_domain']
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'必須フィールド "{field}" が不足しています'
                }), 400
        
        token = data['token'].strip()
        project_id = data['project_id'].strip()
        base_domain = data['base_domain'].strip()
        
        result = railway_setup_service.setup_environment_variables(
            token, project_id, base_domain
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'results': result['results']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'results': result.get('results', [])
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'環境変数設定エラー: {str(e)}'
        }), 500 