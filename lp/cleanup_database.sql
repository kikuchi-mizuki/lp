-- データベースクリーンアップSQL
-- Railway Postgresダッシュボードで実行してください

-- company_line_accountsのデータを削除
DELETE FROM company_line_accounts;

-- company_monthly_subscriptionsのデータを削除
DELETE FROM company_monthly_subscriptions;

-- company_content_additions（古いテーブル）のデータを削除
DELETE FROM company_content_additions WHERE EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_name = 'company_content_additions'
);

-- company_subscriptions（古いテーブル）のデータを削除
DELETE FROM company_subscriptions WHERE EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_name = 'company_subscriptions'
);
