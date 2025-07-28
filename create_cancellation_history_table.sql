-- cancellation_historyテーブル作成スクリプト
-- Railway PostgreSQLデータベースで実行してください

-- 解約履歴テーブルの作成
CREATE TABLE IF NOT EXISTS cancellation_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    content_type VARCHAR(255) NOT NULL,
    cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- インデックスの作成（パフォーマンス向上のため）
CREATE INDEX IF NOT EXISTS idx_cancellation_history_user_id ON cancellation_history(user_id);
CREATE INDEX IF NOT EXISTS idx_cancellation_history_content_type ON cancellation_history(content_type);
CREATE INDEX IF NOT EXISTS idx_cancellation_history_user_content ON cancellation_history(user_id, content_type);

-- テーブル作成確認
SELECT 'cancellation_history table created successfully' as status;

-- テーブル構造確認
\d cancellation_history; 