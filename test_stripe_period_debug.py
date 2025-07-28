#!/usr/bin/env python3
"""
Stripeの期間計算デバッグテスト
"""

import os
import stripe
from dotenv import load_dotenv
from datetime import datetime, timedelta

# 環境変数を読み込み
load_dotenv()
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def test_period_calculation():
    """期間計算のテスト"""
    
    # 実際のサブスクリプションIDを使用
    subscription_id = "sub_1RpVU2Ixg6C5hAVdeyAz8Tjk"  # 実際のIDに変更
    
    try:
        # サブスクリプションを取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        print(f"=== サブスクリプション情報 ===")
        print(f"ID: {subscription.id}")
        print(f"Status: {subscription.status}")
        print(f"Current Period Start: {datetime.fromtimestamp(subscription.current_period_start)}")
        print(f"Current Period End: {datetime.fromtimestamp(subscription.current_period_end)}")
        
        if subscription.status == 'trialing':
            print(f"Trial End: {datetime.fromtimestamp(subscription.trial_end)}")
            
            # 現在の期間計算
            trial_end = subscription.trial_end
            if isinstance(trial_end, int):
                trial_end_dt = datetime.fromtimestamp(trial_end)
            else:
                trial_end_dt = trial_end
            
            # 次の月額期間の開始日（トライアル終了日の翌日）
            current_period_start = int((trial_end_dt + timedelta(days=1)).timestamp())
            
            # 次の月額期間の終了日（開始日から1ヶ月後）
            next_period_end = trial_end_dt + timedelta(days=1) + timedelta(days=30)
            current_period_end = int(next_period_end.timestamp())
            
            print(f"\n=== 計算された期間 ===")
            print(f"Trial End: {trial_end_dt}")
            print(f"Next Period Start: {datetime.fromtimestamp(current_period_start)}")
            print(f"Next Period End: {datetime.fromtimestamp(current_period_end)}")
            
            # 実際のInvoice Itemを作成してテスト
            print(f"\n=== Invoice Item作成テスト ===")
            try:
                invoice_item = stripe.InvoiceItem.create(
                    customer=subscription.customer,
                    amount=1500,  # ¥1,500
                    currency='jpy',
                    description="テスト: コンテンツ追加 (期間計算テスト)",
                    subscription=subscription_id,
                    period={
                        'start': current_period_start,
                        'end': current_period_end
                    }
                )
                print(f"Invoice Item作成成功: {invoice_item.id}")
                print(f"Period Start: {datetime.fromtimestamp(invoice_item.period.start)}")
                print(f"Period End: {datetime.fromtimestamp(invoice_item.period.end)}")
                
                # 作成したInvoice Itemを削除
                invoice_item.delete()
                print(f"Invoice Item削除成功: {invoice_item.id}")
                
            except Exception as e:
                print(f"Invoice Item作成エラー: {e}")
        
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    test_period_calculation() 