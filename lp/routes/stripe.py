from flask import Blueprint, request, jsonify
import stripe
import os
import traceback
from datetime import datetime, timedelta
from utils.db import get_db_connection
from services.stripe_payment_service import stripe_payment_service

stripe_bp = Blueprint('stripe', __name__)

@stripe_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    # 委譲（正規URL: /api/v1/stripe/webhook）
    try:
        payload = request.get_data()
        signature = request.headers.get('Stripe-Signature', '')
        if not signature:
            return jsonify({'success': False, 'error': 'Stripe-Signatureヘッダーが見つかりません'}), 400
        result = stripe_payment_service.process_webhook(payload, signature)
        return (jsonify(result), 200) if result.get('success') else (jsonify(result), 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    print(f"[Stripe Webhook] リクエスト受信: {request.method}")
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
        # invoice.payment_succeeded, customer.subscription.created など
        import unicodedata
        def normalize_email(email):
            if not email:
                return email
            email = email.strip().lower()
            email = unicodedata.normalize('NFKC', email)
            return email
        # ここから下は既存のイベント処理の中で、DB登録時に
        # email = normalize_email(email)
        # としてからDBに保存するようにしてください。
        # 例:
        # email = normalize_email(email)
        # c.execute('INSERT INTO users (email, ...) VALUES (?, ...)', (email, ...))
        event_type = event['type']
        print(f"[Stripe Webhook] イベント受信: {event_type}")
        if event_type == 'checkout.session.completed':
            session = event['data']['object']
            customer_id = session.get('customer')
            subscription_id = session.get('subscription')
            customer_email = session.get('customer_email')
            
            if not subscription_id:
                print('subscription_idが存在しません。スキップします。')
                return jsonify({'status': 'skipped'})
            
            email = normalize_email(customer_email)
            conn = get_db_connection()
            c = conn.cursor()
            
            # メールアドレスで既存ユーザーを検索
            c.execute('SELECT id, line_user_id FROM users WHERE email = %s', (email,))
            existing_user_by_email = c.fetchone()
            
            if existing_user_by_email:
                user_id, line_user_id = existing_user_by_email
                # 既存ユーザーの決済情報を更新
                c.execute('UPDATE users SET stripe_customer_id = %s, stripe_subscription_id = %s WHERE id = %s', (customer_id, subscription_id, user_id))
                
                # companiesテーブルに企業データが存在するかチェック
                c.execute('SELECT id FROM companies WHERE stripe_subscription_id = %s', (subscription_id,))
                existing_company = c.fetchone()
                
                if not existing_company:
                    # 企業データが存在しない場合は作成（line_user_idはNULLのまま）
                    company_name = f"企業_{email.split('@')[0]}"
                    c.execute('''
                        INSERT INTO companies (company_name, company_code, email, stripe_subscription_id, status, created_at)
                        VALUES (%s, %s, %s, %s, 'active', CURRENT_TIMESTAMP)
                        RETURNING id
                    ''', (company_name, f"company_{user_id}", email, subscription_id))
                    company_id = c.fetchone()[0]
                    print(f'[DEBUG] 企業データ作成: company_id={company_id}, company_name={company_name}')
                    
                    # company_paymentsテーブルにも決済データを作成
                    c.execute('''
                        INSERT INTO company_payments (company_id, stripe_customer_id, stripe_subscription_id, subscription_status, created_at)
                        VALUES (%s, %s, %s, 'active', CURRENT_TIMESTAMP)
                    ''', (company_id, customer_id, subscription_id))
                    
                    # company_subscriptionsテーブルにサブスクリプション情報を保存
                    try:
                        # Stripeからサブスクリプション情報を取得
                        subscription = stripe.Subscription.retrieve(subscription_id)
                        
                        # UTCタイムスタンプをJSTに変換
                        from datetime import timezone, timedelta
                        jst = timezone(timedelta(hours=9))
                        
                        # current_period_endをJSTに変換
                        current_period_end_utc = datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc)
                        current_period_end = current_period_end_utc.astimezone(jst)
                        
                        # トライアル期間の確認
                        trial_end = None
                        if subscription.trial_end:
                            trial_end_utc = datetime.fromtimestamp(subscription.trial_end, tz=timezone.utc)
                            trial_end = trial_end_utc.astimezone(jst)
                            print(f'[DEBUG] トライアル期間終了: {trial_end}')
                        
                        c.execute('''
                            INSERT INTO company_subscriptions 
                            (company_id, content_type, subscription_status, stripe_subscription_id, current_period_end, created_at)
                            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ''', (
                            company_id,
                            '月額基本料金',  # 初期は月額基本料金のみ
                            subscription.status,
                            subscription_id,
                            current_period_end
                        ))
                        print(f'[DEBUG] company_subscriptionsテーブルにサブスクリプション情報を保存: company_id={company_id}, subscription_id={subscription_id}')
                        
                        # companiesテーブルにトライアル期間情報を更新
                        if trial_end:
                            c.execute('''
                                UPDATE companies 
                                SET trial_end = %s 
                                WHERE id = %s
                            ''', (trial_end, company_id))
                            print(f'[DEBUG] トライアル期間情報を更新: company_id={company_id}, trial_end={trial_end}')
                        
                        # 月額基本サブスクリプションテーブルをUPSERT
                        try:
                            c.execute('''
                                INSERT INTO company_monthly_subscriptions 
                                (company_id, stripe_subscription_id, subscription_status, monthly_base_price, current_period_end)
                                VALUES (%s, %s, %s, %s, %s)
                                ON CONFLICT (company_id) DO UPDATE SET
                                    stripe_subscription_id = EXCLUDED.stripe_subscription_id,
                                    subscription_status = EXCLUDED.subscription_status,
                                    current_period_end = EXCLUDED.current_period_end,
                                    updated_at = CURRENT_TIMESTAMP
                            ''', (company_id, subscription_id, subscription.status, 3900, current_period_end))
                            print(f"[DEBUG] company_monthly_subscriptions をUPSERT: company_id={company_id}")
                        except Exception as e:
                            print(f"[WARN] company_monthly_subscriptions UPSERT失敗: {e}")
                        
                    except Exception as e:
                        print(f'[ERROR] company_subscriptionsテーブル保存エラー: {e}')
                        import traceback
                        traceback.print_exc()
                    
                    print(f'企業データ作成完了: company_id={company_id}, company_name={company_name}')
                
                # 月額基本サブスクリプションテーブルをUPSERT（既存企業にも必ず実行）
                try:
                    subscription = stripe.Subscription.retrieve(subscription_id)
                    from datetime import timezone, timedelta
                    jst = timezone(timedelta(hours=9))
                    current_period_end_utc = datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc)
                    current_period_end = current_period_end_utc.astimezone(jst)

                    c.execute('''
                        INSERT INTO company_monthly_subscriptions 
                        (company_id, stripe_subscription_id, subscription_status, monthly_base_price, current_period_end)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (company_id) DO UPDATE SET
                            stripe_subscription_id = EXCLUDED.stripe_subscription_id,
                            subscription_status = EXCLUDED.subscription_status,
                            current_period_end = EXCLUDED.current_period_end,
                            updated_at = CURRENT_TIMESTAMP
                    ''', (company_id, subscription_id, subscription.status, 3900, current_period_end))
                    print(f"[DEBUG] company_monthly_subscriptions をUPSERT(既存含む): company_id={company_id}")
                except Exception as e:
                    print(f"[WARN] company_monthly_subscriptions UPSERT失敗(既存含む): {e}")

                conn.commit()
                print(f'既存ユーザーの決済情報を更新: id={user_id}, subscription_id={subscription_id}')
                
                # LINE連携済みの場合、案内メッセージを送信
                if line_user_id:
                    try:
                        from services.line_service import send_company_welcome_message
                        # 企業情報を取得
                        c.execute('SELECT company_name FROM companies WHERE id = %s', (company_id,))
                        company_result = c.fetchone()
                        company_name = company_result[0] if company_result else '企業'
                        
                        send_company_welcome_message(line_user_id, company_name, email)
                        print(f'[DEBUG] 決済完了時の企業向け案内文送信完了: line_user_id={line_user_id}')
                    except Exception as e:
                        print(f'[DEBUG] 決済完了時の企業向け案内文送信エラー: {e}')
                        import traceback
                        traceback.print_exc()
                else:
                    print(f'[DEBUG] LINE連携未完了のため案内文送信をスキップ: email={email}')
                    
                    # 未紐付け企業データがある場合は自動で更新を試行
                    print(f'[DEBUG] 未紐付け企業データの自動更新を試行: email={email}')
                    c.execute('SELECT id FROM companies WHERE email = %s AND line_user_id IS NULL', (email,))
                    unlinked_company = c.fetchone()
                    
                    if unlinked_company:
                        company_id = unlinked_company[0]
                        print(f'[DEBUG] 未紐付け企業データ発見: company_id={company_id}')
                        
                        # 企業データにLINEユーザーIDを設定（user_idではなく、後でLINE連携時に設定）
                        # ここでは企業データを準備するだけ
                        print(f'[DEBUG] 企業データ準備完了: company_id={company_id}, email={email}')
                        
                        # 案内メッセージはLINE連携時に送信
                        print(f'[DEBUG] LINE連携待ち状態: email={email}')
                    else:
                        print(f'[DEBUG] 未紐付け企業データが見つかりません: email={email}')
            else:
                # 新規ユーザーとして登録
                c.execute('INSERT INTO users (email, stripe_customer_id, stripe_subscription_id) VALUES (%s, %s, %s)', (email, customer_id, subscription_id))
                user_id = c.lastrowid
                
                # companiesテーブルにも企業データを作成（line_user_idはNULLのまま）
                company_name = f"企業_{email.split('@')[0]}"
                c.execute('''
                    INSERT INTO companies (company_name, company_code, email, stripe_subscription_id, status, created_at)
                    VALUES (%s, %s, %s, %s, 'active', CURRENT_TIMESTAMP)
                    RETURNING id
                ''', (company_name, f"company_{user_id}", email, subscription_id))
                company_id = c.fetchone()[0]
                print(f'[DEBUG] 企業データ作成: company_id={company_id}, company_name={company_name}, email={email}')
                
                # company_paymentsテーブルにも決済データを作成
                c.execute('''
                    INSERT INTO company_payments (company_id, stripe_customer_id, stripe_subscription_id, subscription_status, created_at)
                    VALUES (%s, %s, %s, 'active', CURRENT_TIMESTAMP)
                ''', (company_id, customer_id, subscription_id))
                
                # company_subscriptionsテーブルにサブスクリプション情報を保存
                try:
                    # Stripeからサブスクリプション情報を取得
                    subscription = stripe.Subscription.retrieve(subscription_id)
                    
                    # UTCタイムスタンプをJSTに変換
                    from datetime import timezone, timedelta
                    jst = timezone(timedelta(hours=9))
                    
                    # current_period_endをJSTに変換
                    current_period_end_utc = datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc)
                    current_period_end = current_period_end_utc.astimezone(jst)
                    
                    # トライアル期間の確認
                    trial_end = None
                    if subscription.trial_end:
                        trial_end_utc = datetime.fromtimestamp(subscription.trial_end, tz=timezone.utc)
                        trial_end = trial_end_utc.astimezone(jst)
                        print(f'[DEBUG] トライアル期間終了: {trial_end}')
                    
                    c.execute('''
                        INSERT INTO company_subscriptions 
                        (company_id, content_type, subscription_status, stripe_subscription_id, current_period_end, created_at)
                        VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ''', (
                        company_id,
                        '月額基本料金',  # 初期は月額基本料金のみ
                        subscription.status,
                        subscription_id,
                        current_period_end
                    ))
                    print(f'[DEBUG] company_subscriptionsテーブルにサブスクリプション情報を保存: company_id={company_id}, subscription_id={subscription_id}')
                    
                    # companiesテーブルにトライアル期間情報を更新
                    if trial_end:
                        c.execute('''
                            UPDATE companies 
                            SET trial_end = %s 
                            WHERE id = %s
                        ''', (trial_end, company_id))
                        print(f'[DEBUG] トライアル期間情報を更新: company_id={company_id}, trial_end={trial_end}')
                    
                    # 月額基本サブスクリプションテーブルをUPSERT
                    try:
                        c.execute('''
                            INSERT INTO company_monthly_subscriptions 
                            (company_id, stripe_subscription_id, subscription_status, monthly_base_price, current_period_end)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (company_id) DO UPDATE SET
                                stripe_subscription_id = EXCLUDED.stripe_subscription_id,
                                subscription_status = EXCLUDED.subscription_status,
                                current_period_end = EXCLUDED.current_period_end,
                                updated_at = CURRENT_TIMESTAMP
                        ''', (company_id, subscription_id, subscription.status, 3900, current_period_end))
                        print(f"[DEBUG] company_monthly_subscriptions をUPSERT: company_id={company_id}")
                    except Exception as e:
                        print(f"[WARN] company_monthly_subscriptions UPSERT失敗: {e}")
                    
                except Exception as e:
                    print(f'[ERROR] company_subscriptionsテーブル保存エラー: {e}')
                    import traceback
                    traceback.print_exc()
                
                # 月額基本サブスクリプションテーブルをUPSERT
                try:
                    from datetime import timezone, timedelta
                    jst = timezone(timedelta(hours=9))
                    current_period_end_utc = datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc)
                    current_period_end = current_period_end_utc.astimezone(jst)

                    c.execute('''
                        INSERT INTO company_monthly_subscriptions 
                        (company_id, stripe_subscription_id, subscription_status, monthly_base_price, current_period_end)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (company_id) DO UPDATE SET
                            stripe_subscription_id = EXCLUDED.stripe_subscription_id,
                            subscription_status = EXCLUDED.subscription_status,
                            current_period_end = EXCLUDED.current_period_end,
                            updated_at = CURRENT_TIMESTAMP
                    ''', (company_id, subscription_id, subscription.status, 3900, current_period_end))
                    print(f"[DEBUG] company_monthly_subscriptions をUPSERT: company_id={company_id}")
                except Exception as e:
                    print(f"[WARN] company_monthly_subscriptions UPSERT失敗: {e}")

                conn.commit()
                print(f'新規ユーザー登録完了: email={email}, customer_id={customer_id}, subscription_id={subscription_id}')
                print(f'企業データ作成完了: company_id={company_id}, company_name={company_name}')
                print(f'[IMPORTANT] 企業データ準備完了 - LINE連携待ち: email={email}, company_id={company_id}')
            
            # 従量課金アイテムの自動追加を削除 - ユーザーが手動で追加するまで待機
            print(f'[DEBUG] サブスクリプション情報保存完了: subscription_id={subscription_id}')
            print(f'[INFO] 従量課金アイテムは手動追加まで待機中')
            
            conn.close()
        elif event_type == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            customer_id = invoice.get('customer')
            subscription_id = invoice.get('subscription')
            email = invoice.get('customer_email')
            email = normalize_email(email)
            if not subscription_id:
                print('subscription_idが存在しません。スキップします。')
                return jsonify({'status': 'skipped'})
            
            conn = get_db_connection()
            c = conn.cursor()
            
            # メールアドレスで既存ユーザーを検索
            c.execute('SELECT id, line_user_id FROM users WHERE email = %s', (email,))
            existing_user_by_email = c.fetchone()
            
            if existing_user_by_email:
                user_id, line_user_id = existing_user_by_email
                # 既存ユーザーの決済情報を更新
                c.execute('UPDATE users SET stripe_customer_id = %s, stripe_subscription_id = %s WHERE id = %s', (customer_id, subscription_id, user_id))
                
                # companiesテーブルに企業データが存在するかチェック
                c.execute('SELECT id FROM companies WHERE stripe_subscription_id = %s', (subscription_id,))
                existing_company = c.fetchone()
                
                if not existing_company:
                    # 企業データが存在しない場合は作成（line_user_idはNULLのまま）
                    company_name = f"企業_{email.split('@')[0]}"
                    c.execute('''
                        INSERT INTO companies (company_name, company_code, email, stripe_subscription_id, status, created_at)
                        VALUES (%s, %s, %s, %s, 'active', CURRENT_TIMESTAMP)
                        RETURNING id
                    ''', (company_name, f"company_{user_id}", email, subscription_id))
                    company_id = c.fetchone()[0]
                    print(f'[DEBUG] 企業データ作成: company_id={company_id}, company_name={company_name}')
                    
                    # company_paymentsテーブルにも決済データを作成
                    c.execute('''
                        INSERT INTO company_payments (company_id, stripe_customer_id, stripe_subscription_id, subscription_status, created_at)
                        VALUES (%s, %s, %s, 'active', CURRENT_TIMESTAMP)
                    ''', (company_id, customer_id, subscription_id))
                    
                    # company_subscriptionsテーブルにサブスクリプション情報を保存
                    try:
                        # Stripeからサブスクリプション情報を取得
                        subscription = stripe.Subscription.retrieve(subscription_id)
                        
                        # UTCタイムスタンプをJSTに変換
                        from datetime import timezone, timedelta
                        jst = timezone(timedelta(hours=9))
                        
                        # current_period_endをJSTに変換
                        current_period_end_utc = datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc)
                        current_period_end = current_period_end_utc.astimezone(jst)
                        
                        # トライアル期間の確認
                        trial_end = None
                        if subscription.trial_end:
                            trial_end_utc = datetime.fromtimestamp(subscription.trial_end, tz=timezone.utc)
                            trial_end = trial_end_utc.astimezone(jst)
                            print(f'[DEBUG] トライアル期間終了: {trial_end}')
                        
                        c.execute('''
                            INSERT INTO company_subscriptions 
                            (company_id, content_type, subscription_status, stripe_subscription_id, current_period_end, created_at)
                            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ''', (
                            company_id,
                            '月額基本料金',  # 初期は月額基本料金のみ
                            subscription.status,
                            subscription_id,
                            current_period_end
                        ))
                        print(f'[DEBUG] company_subscriptionsテーブルにサブスクリプション情報を保存: company_id={company_id}, subscription_id={subscription_id}')
                        
                        # companiesテーブルにトライアル期間情報を更新
                        if trial_end:
                            c.execute('''
                                UPDATE companies 
                                SET trial_end = %s 
                                WHERE id = %s
                            ''', (trial_end, company_id))
                            print(f'[DEBUG] トライアル期間情報を更新: company_id={company_id}, trial_end={trial_end}')
                        
                    except Exception as e:
                        print(f'[ERROR] company_subscriptionsテーブル保存エラー: {e}')
                        import traceback
                        traceback.print_exc()
                    
                    print(f'企業データ作成完了: company_id={company_id}, company_name={company_name}')
                
                conn.commit()
                print(f'既存ユーザーの決済情報を更新: id={user_id}, subscription_id={subscription_id}')
                
                # 課金予定のコンテンツ処理を削除 - ユーザーが手動で追加するまで待機
                print(f'[DEBUG] サブスクリプション情報保存完了: subscription_id={subscription_id}')
                print(f'[INFO] コンテンツ追加は手動追加まで待機中')
                
                # LINE連携済みの場合、案内メッセージを送信
                if line_user_id:
                    try:
                        from services.line_service import send_company_welcome_message
                        # 企業情報を取得
                        c.execute('SELECT company_name FROM companies WHERE id = %s', (company_id,))
                        company_result = c.fetchone()
                        company_name = company_result[0] if company_result else '企業'
                        
                        send_company_welcome_message(line_user_id, company_name, email)
                        print(f'[DEBUG] 決済完了時の企業向け案内文送信完了: line_user_id={line_user_id}')
                    except Exception as e:
                        print(f'[DEBUG] 決済完了時の企業向け案内文送信エラー: {e}')
                        import traceback
                        traceback.print_exc()
                else:
                    print(f'[DEBUG] LINE連携未完了のため案内文送信をスキップ: email={email}')
                    
                    # 未紐付け企業データがある場合は自動で更新を試行
                    print(f'[DEBUG] 未紐付け企業データの自動更新を試行: email={email}')
                    c.execute('SELECT id FROM companies WHERE email = %s AND line_user_id IS NULL', (email,))
                    unlinked_company = c.fetchone()
                    
                    if unlinked_company:
                        company_id = unlinked_company[0]
                        print(f'[DEBUG] 未紐付け企業データ発見: company_id={company_id}')
                        
                        # 既存のLINEユーザーIDをクリア（重複回避）
                        c.execute('UPDATE companies SET line_user_id = NULL WHERE line_user_id IS NOT NULL')
                        
                        # 企業データにLINEユーザーIDを設定
                        c.execute('UPDATE companies SET line_user_id = %s WHERE id = %s', (user_id, company_id))
                        conn.commit()
                        print(f'[DEBUG] 企業データ自動更新完了: user_id={user_id}, company_id={company_id}')
                        
                        # 案内メッセージを送信
                        try:
                            from services.line_service import send_company_welcome_message
                            # 企業情報を取得
                            c.execute('SELECT company_name FROM companies WHERE id = %s', (company_id,))
                            company_result = c.fetchone()
                            company_name = company_result[0] if company_result else '企業'
                            
                            send_company_welcome_message(user_id, company_name, email)
                            print(f'[DEBUG] 決済完了時の自動企業向け案内文送信完了: user_id={user_id}')
                        except Exception as e:
                            print(f'[DEBUG] 決済完了時の自動企業向け案内文送信エラー: {e}')
                            import traceback
                            traceback.print_exc()
                    else:
                        print(f'[DEBUG] 未紐付け企業データが見つかりません: email={email}')
            else:
                # 新規ユーザーとして登録
                c.execute('INSERT INTO users (email, stripe_customer_id, stripe_subscription_id) VALUES (%s, %s, %s)', (email, customer_id, subscription_id))
                user_id = c.lastrowid
                
                # companiesテーブルにも企業データを作成（line_user_idはNULLのまま）
                company_name = f"企業_{email.split('@')[0]}"
                c.execute('''
                    INSERT INTO companies (company_name, company_code, email, stripe_subscription_id, status, created_at)
                    VALUES (%s, %s, %s, %s, 'active', CURRENT_TIMESTAMP)
                    RETURNING id
                ''', (company_name, f"company_{user_id}", email, subscription_id))
                company_id = c.fetchone()[0]
                print(f'[DEBUG] 企業データ作成: company_id={company_id}, company_name={company_name}')
                
                # company_paymentsテーブルにも決済データを作成
                c.execute('''
                    INSERT INTO company_payments (company_id, stripe_customer_id, stripe_subscription_id, subscription_status, created_at)
                    VALUES (%s, %s, %s, 'active', CURRENT_TIMESTAMP)
                ''', (company_id, customer_id, subscription_id))
                
                # company_subscriptionsテーブルにサブスクリプション情報を保存
                try:
                    # Stripeからサブスクリプション情報を取得
                    subscription = stripe.Subscription.retrieve(subscription_id)
                    current_period_end = datetime.fromtimestamp(subscription.current_period_end)
                    
                    c.execute('''
                        INSERT INTO company_subscriptions 
                        (company_id, content_type, subscription_status, stripe_subscription_id, current_period_end, created_at)
                        VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ''', (
                        company_id,
                        '月額基本料金',  # 初期は月額基本料金のみ
                        subscription.status,
                        subscription_id,
                        current_period_end
                    ))
                    print(f'[DEBUG] company_subscriptionsテーブルにサブスクリプション情報を保存: company_id={company_id}, subscription_id={subscription_id}')
                except Exception as e:
                    print(f'[ERROR] company_subscriptionsテーブル保存エラー: {e}')
                    import traceback
                    traceback.print_exc()
                
                # 月額料金決済時はコンテンツを自動追加しない
                # ユーザーが手動でコンテンツを追加するまで待機
                
                conn.commit()
                print(f'新規ユーザー登録完了: email={email}, customer_id={customer_id}, subscription_id={subscription_id}')
                print(f'企業データ作成完了: company_id={company_id}, company_name={company_name}')
            
            # 従量課金アイテムの自動追加を削除 - ユーザーが手動で追加するまで待機
            print(f'[DEBUG] サブスクリプション情報保存完了: subscription_id={subscription_id}')
            print(f'[INFO] 従量課金アイテムは手動追加まで待機中')
            
            conn.close()
        elif event_type == 'customer.subscription.created':
            subscription = event['data']['object']
            customer_id = subscription['customer']
            subscription_id = subscription['id']
            customer = stripe.Customer.retrieve(customer_id)
            email = customer.get('email')
            if not email:
                print(f'[Stripe Webhook] メールアドレスが取得できません: customer_id={customer_id}')
                return jsonify({'status': 'skipped_no_email'})
            email = normalize_email(email)
            conn = get_db_connection()
            c = conn.cursor()
            
            # メールアドレスで既存企業を検索（企業ユーザー専用）
            c.execute('SELECT id, line_user_id FROM companies WHERE email = %s', (email,))
            existing_company_by_email = c.fetchone()
            
            if existing_company_by_email:
                company_id, line_user_id = existing_company_by_email
                # 既存企業の決済情報を更新
                c.execute('UPDATE companies SET stripe_subscription_id = %s WHERE id = %s', (subscription_id, company_id))
                
                # company_subscriptionsテーブルにサブスクリプション情報を保存
                try:
                    # Stripeからサブスクリプション情報を取得
                    subscription = stripe.Subscription.retrieve(subscription_id)
                    current_period_end = datetime.fromtimestamp(subscription.current_period_end)
                    
                    c.execute('''
                        INSERT INTO company_subscriptions 
                        (company_id, content_type, subscription_status, stripe_subscription_id, current_period_end, created_at)
                        VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ''', (
                        company_id,
                        '月額基本料金',  # 初期は月額基本料金のみ
                        subscription.status,
                        subscription_id,
                        current_period_end
                    ))
                    print(f'[DEBUG] company_subscriptionsテーブルにサブスクリプション情報を保存: company_id={company_id}, subscription_id={subscription_id}')
                except Exception as e:
                    print(f'[ERROR] company_subscriptionsテーブル保存エラー: {e}')
                    import traceback
                    traceback.print_exc()
                
                # 企業データは既に存在するため、サブスクリプション情報を更新
                print(f'[DEBUG] 既存企業データのサブスクリプション更新: company_id={company_id}')
                
                # 月額料金決済時はコンテンツを自動追加しない
                # ユーザーが手動でコンテンツを追加するまで待機
                
                print(f'[DEBUG] サブスクリプション情報保存完了: company_id={company_id}')
                
                # 月額基本サブスクリプションテーブルをUPSERT
                try:
                    from datetime import timezone, timedelta
                    jst = timezone(timedelta(hours=9))
                    current_period_end_utc = datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc)
                    current_period_end_jst = current_period_end_utc.astimezone(jst)

                    c.execute('''
                        INSERT INTO company_monthly_subscriptions 
                        (company_id, stripe_subscription_id, subscription_status, monthly_base_price, current_period_end)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (company_id) DO UPDATE SET
                            stripe_subscription_id = EXCLUDED.stripe_subscription_id,
                            subscription_status = EXCLUDED.subscription_status,
                            current_period_end = EXCLUDED.current_period_end,
                            updated_at = CURRENT_TIMESTAMP
                    ''', (company_id, subscription_id, subscription.status, 3900, current_period_end_jst))
                    print(f"[DEBUG] company_monthly_subscriptions をUPSERT: company_id={company_id}")
                except Exception as e:
                    print(f"[WARN] company_monthly_subscriptions UPSERT失敗: {e}")

                conn.commit()
                print(f'既存企業の決済情報を更新: company_id={company_id}, subscription_id={subscription_id}')
                
                # LINE連携済みの場合、案内メッセージを送信
                if line_user_id:
                    try:
                        from services.line_service import send_welcome_with_buttons_push
                        send_welcome_with_buttons_push(line_user_id)
                        print(f'[DEBUG] サブスクリプション作成時の案内文送信完了: line_user_id={line_user_id}')
                    except Exception as e:
                        print(f'[DEBUG] サブスクリプション作成時の案内文送信エラー: {e}')
                        traceback.print_exc()
                else:
                    print(f'[DEBUG] LINE連携未完了のため案内文送信をスキップ: email={email}')
                    
                    # 未紐付け企業データがある場合は自動で更新を試行
                    print(f'[DEBUG] 未紐付け企業データの自動更新を試行: email={email}')
                    c.execute('SELECT id FROM companies WHERE email = %s AND line_user_id IS NULL', (email,))
                    unlinked_company = c.fetchone()
                    
                    if unlinked_company:
                        company_id = unlinked_company[0]
                        print(f'[DEBUG] 未紐付け企業データ発見: company_id={company_id}')
                        
                        # 既存のLINEユーザーIDをクリア（重複回避）
                        c.execute('UPDATE companies SET line_user_id = NULL WHERE line_user_id IS NOT NULL')
                        
                        # 企業データにLINEユーザーIDを設定
                        c.execute('UPDATE companies SET line_user_id = %s WHERE id = %s', (line_user_id, company_id))
                        conn.commit()
                        print(f'[DEBUG] 企業データ自動更新完了: line_user_id={line_user_id}, company_id={company_id}')
                        
                        # 案内メッセージを送信
                        try:
                            from services.line_service import send_welcome_with_buttons_push
                            send_welcome_with_buttons_push(line_user_id)
                            print(f'[DEBUG] サブスクリプション作成時の自動案内文送信完了: line_user_id={line_user_id}')
                        except Exception as e:
                            print(f'[DEBUG] サブスクリプション作成時の自動案内文送信エラー: {e}')
                            import traceback
                            traceback.print_exc()
                    else:
                        print(f'[DEBUG] 未紐付け企業データが見つかりません: email={email}')
            else:
                # 新規企業として登録（企業ユーザー専用）
                company_name = f"企業_{email.split('@')[0]}"
                c.execute('''
                    INSERT INTO companies (company_name, email, stripe_subscription_id, status, created_at)
                    VALUES (%s, %s, %s, 'active', CURRENT_TIMESTAMP)
                    RETURNING id
                ''', (company_name, email, subscription_id))
                company_id = c.fetchone()[0]
                print(f'[DEBUG] 新規企業データ作成: company_id={company_id}, company_name={company_name}')
                
                # company_paymentsテーブルにも決済データを作成
                c.execute('''
                    INSERT INTO company_payments (company_id, stripe_customer_id, stripe_subscription_id, subscription_status, created_at)
                    VALUES (%s, %s, %s, 'active', CURRENT_TIMESTAMP)
                ''', (company_id, customer_id, subscription_id))
                
                # company_subscriptionsテーブルにサブスクリプション情報を保存
                try:
                    # Stripeからサブスクリプション情報を取得
                    subscription = stripe.Subscription.retrieve(subscription_id)
                    current_period_end = datetime.fromtimestamp(subscription.current_period_end)
                    
                    c.execute('''
                        INSERT INTO company_subscriptions 
                        (company_id, content_type, subscription_status, stripe_subscription_id, current_period_end, created_at)
                        VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ''', (
                        company_id,
                        '月額基本料金',  # 初期は月額基本料金のみ
                        subscription.status,
                        subscription_id,
                        current_period_end
                    ))
                    print(f'[DEBUG] company_subscriptionsテーブルにサブスクリプション情報を保存: company_id={company_id}, subscription_id={subscription_id}')
                except Exception as e:
                    print(f'[ERROR] company_subscriptionsテーブル保存エラー: {e}')
                    import traceback
                    traceback.print_exc()
                
                conn.commit()
                print(f'新規ユーザー登録完了: email={email}, customer_id={customer_id}, subscription_id={subscription_id}')
                print(f'企業データ作成完了: company_id={company_id}, company_name={company_name}')
            
            # 従量課金アイテムを追加
            try:
                USAGE_PRICE_ID = os.getenv('STRIPE_USAGE_PRICE_ID')
                result = stripe.SubscriptionItem.create(
                    subscription=subscription_id,
                    price=USAGE_PRICE_ID
                )
                print(f'従量課金アイテム追加完了: subscription_id={subscription_id}, usage_price_id={USAGE_PRICE_ID}, result={result}')
            except Exception as e:
                import traceback
                print(f'従量課金アイテム追加エラー: {e}')
                print(traceback.format_exc())
            
            conn.close()
    except Exception as e:
        print(f"[Stripe Webhook] イベント処理エラー: {e}")
        import traceback
        print(traceback.format_exc())
        return '', 500
    return '', 200 