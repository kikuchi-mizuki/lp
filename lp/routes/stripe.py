from flask import Blueprint, request, jsonify
import stripe
import os

stripe_bp = Blueprint('stripe', __name__)

@stripe_bp.route('/stripe_webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except Exception as e:
        print(f"[Stripe Webhook] 検証エラー: {e}")
        return '', 400
    try:
        # ここにapp.pyからstripe_webhookのロジックを移動予定
        # 例: 支払い成功/失敗、サブスクリプション作成、従量課金処理など
        pass  # 既存の処理をここに
    except Exception as e:
        import traceback
        print(f"[Stripe Webhook] イベント処理エラー: {e}")
        print(traceback.format_exc())
        return '', 500
    return '', 200 