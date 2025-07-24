from flask import Blueprint, request, jsonify

line_bp = Blueprint('line', __name__)

@line_bp.route('/line/webhook', methods=['POST'])
def line_webhook():
    # ここにapp.pyからline_webhookのロジックを移動予定
    # 例: ユーザー認証、コマンド分岐、状態管理、LINEメッセージ送信など
    return jsonify({'status': 'ok'}) 