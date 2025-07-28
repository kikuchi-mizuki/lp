#!/bin/bash

# 異なるプロジェクト間でのPostgreSQLデータベース共有セットアップスクリプト

set -e  # エラー時に停止

echo "🚀 異なるプロジェクト間でのPostgreSQLデータベース共有セットアップを開始します..."

# 色付きの出力関数
print_success() {
    echo -e "\033[32m✅ $1\033[0m"
}

print_info() {
    echo -e "\033[34mℹ️  $1\033[0m"
}

print_warning() {
    echo -e "\033[33m⚠️  $1\033[0m"
}

print_error() {
    echo -e "\033[31m❌ $1\033[0m"
}

# Railway CLIの確認
check_railway_cli() {
    print_info "Railway CLIの確認中..."
    if ! command -v railway &> /dev/null; then
        print_error "Railway CLIがインストールされていません。"
        echo "以下のコマンドでインストールしてください："
        echo "npm install -g @railway/cli"
        exit 1
    fi
    print_success "Railway CLIが確認されました"
}

# ログイン確認
check_login() {
    print_info "Railwayログイン状態を確認中..."
    if ! railway whoami &> /dev/null; then
        print_warning "Railwayにログインしていません。"
        echo "以下のコマンドでログインしてください："
        echo "railway login"
        exit 1
    fi
    print_success "Railwayにログイン済みです"
}

# 共有データベースプロジェクトの作成
create_shared_database_project() {
    print_info "共有データベースプロジェクトを作成中..."
    
    # 共有データベースプロジェクトディレクトリを作成
    mkdir -p shared-database-project
    cd shared-database-project
    
    # Railwayプロジェクトを初期化
    railway init --name shared-database
    
    # PostgreSQLデータベースを追加
    railway add postgresql
    
    print_success "共有データベースプロジェクトが作成されました"
    
    # 接続情報を取得
    print_info "データベース接続情報を取得中..."
    railway variables > connection_info.txt
    
    print_success "接続情報が connection_info.txt に保存されました"
    
    # 接続情報を表示
    echo ""
    print_info "データベース接続情報："
    cat connection_info.txt
    
    cd ..
}

# データベーススキーマの初期化
initialize_database_schema() {
    print_info "データベーススキーマを初期化中..."
    
    cd shared-database-project
    
    # スキーマ初期化SQLファイルを作成
    cat > init_schema.sql << 'EOF'
-- 必要なテーブルを作成
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    stripe_customer_id VARCHAR(255) UNIQUE NOT NULL,
    stripe_subscription_id VARCHAR(255) UNIQUE NOT NULL,
    line_user_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS usage_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    usage_quantity INTEGER DEFAULT 1,
    stripe_usage_record_id VARCHAR(255),
    is_free BOOLEAN DEFAULT FALSE,
    content_type VARCHAR(255),
    pending_charge BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS cancellation_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    content_type VARCHAR(255) NOT NULL,
    cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS user_states (
    id SERIAL PRIMARY KEY,
    line_user_id VARCHAR(255) UNIQUE NOT NULL,
    state VARCHAR(255),
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックスの作成
CREATE INDEX IF NOT EXISTS idx_users_line_user_id ON users(line_user_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_user_id ON usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_cancellation_history_user_id ON cancellation_history(user_id);
CREATE INDEX IF NOT EXISTS idx_cancellation_history_content_type ON cancellation_history(content_type);
CREATE INDEX IF NOT EXISTS idx_user_states_line_user_id ON user_states(line_user_id);
EOF
    
    # データベースに接続してスキーマを初期化
    railway connect < init_schema.sql
    
    print_success "データベーススキーマが初期化されました"
    
    cd ..
}

# 各サービスプロジェクトの設定
setup_service_projects() {
    print_info "各サービスプロジェクトの設定を開始..."
    
    # 接続情報を読み込み
    DATABASE_URL=$(grep "DATABASE_URL" shared-database-project/connection_info.txt | cut -d'=' -f2)
    
    if [ -z "$DATABASE_URL" ]; then
        print_error "DATABASE_URLが見つかりません"
        exit 1
    fi
    
    # 各サービスプロジェクトの設定
    services=(
        "ai-collections-main"
        "ai-schedule-secretary"
        "ai-accounting-secretary"
        "ai-task-concierge"
    )
    
    for service in "${services[@]}"; do
        print_info "$service プロジェクトを設定中..."
        
        # プロジェクトディレクトリを作成
        mkdir -p "$service-project"
        cd "$service-project"
        
        # Railwayプロジェクトを初期化
        railway init --name "$service"
        
        # 共有データベースの接続情報を設定
        railway variables set DATABASE_URL="$DATABASE_URL"
        
        print_success "$service プロジェクトが設定されました"
        
        cd ..
    done
}

# 接続テスト
test_connections() {
    print_info "各プロジェクトの接続をテスト中..."
    
    # 共有データベースプロジェクトのテスト
    cd shared-database-project
    print_info "共有データベースプロジェクトの接続テスト..."
    
    if railway connect -c "SELECT version();" &> /dev/null; then
        print_success "共有データベースプロジェクトの接続テスト成功"
    else
        print_error "共有データベースプロジェクトの接続テスト失敗"
    fi
    
    cd ..
    
    # 各サービスプロジェクトのテスト
    services=(
        "ai-collections-main"
        "ai-schedule-secretary"
        "ai-accounting-secretary"
        "ai-task-concierge"
    )
    
    for service in "${services[@]}"; do
        cd "$service-project"
        print_info "$service プロジェクトの接続テスト..."
        
        if railway connect -c "SELECT 1;" &> /dev/null; then
            print_success "$service プロジェクトの接続テスト成功"
        else
            print_warning "$service プロジェクトの接続テスト失敗"
        fi
        
        cd ..
    done
}

# 設定完了メッセージ
show_completion_message() {
    echo ""
    print_success "🎉 セットアップが完了しました！"
    echo ""
    echo "📋 次のステップ："
    echo "1. 各プロジェクトディレクトリにアプリケーションコードを配置"
    echo "2. 各プロジェクトで 'railway up' を実行してデプロイ"
    echo "3. 接続情報は 'shared-database-project/connection_info.txt' に保存されています"
    echo ""
    echo "📁 作成されたディレクトリ："
    echo "- shared-database-project/     # 共有データベース"
    echo "- ai-collections-main-project/ # AIコレクションズメイン"
    echo "- ai-schedule-secretary-project/ # AI予定秘書"
    echo "- ai-accounting-secretary-project/ # AI経理秘書"
    echo "- ai-task-concierge-project/   # AIタスクコンシェルジュ"
    echo ""
    print_warning "⚠️  重要：接続情報を安全に保管してください"
}

# メイン処理
main() {
    echo "=========================================="
    echo "PostgreSQLデータベース共有セットアップ"
    echo "=========================================="
    echo ""
    
    check_railway_cli
    check_login
    create_shared_database_project
    initialize_database_schema
    setup_service_projects
    test_connections
    show_completion_message
}

# スクリプト実行
main "$@" 