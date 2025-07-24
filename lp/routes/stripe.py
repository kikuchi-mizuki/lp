from flask import Blueprint, request, jsonify

stripe_bp = Blueprint('stripe', __name__)

@stripe_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    # ここにapp.pyからstripe_webhookのロジックを移動予定
    # 例: 支払い成功/失敗、サブスクリプション作成、従量課金処理など
    return jsonify({'status': 'ok'}) 