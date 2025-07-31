#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
重複LINEチャネルIDの調査と解決スクリプト
"""

from utils.db import get_db_connection

def check_duplicate_line_channels():
    """重複しているLINEチャネルIDを調査"""
    try:
        print("=== 重複LINEチャネルID調査 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 重複しているLINEチャネルIDを検索
        c.execute('''
            SELECT line_channel_id, COUNT(*) as count, 
                   array_agg(company_id) as company_ids,
                   array_agg(c.company_name) as company_names
            FROM company_line_accounts cla
            JOIN companies c ON cla.company_id = c.id
            WHERE line_channel_id IS NOT NULL
            GROUP BY line_channel_id
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        ''')
        
        duplicates = c.fetchall()
        
        if duplicates:
            print(f"⚠️ 重複しているLINEチャネルID: {len(duplicates)}件")
            
            for line_channel_id, count, company_ids, company_names in duplicates:
                print(f"\n🔍 LINEチャネルID: {line_channel_id}")
                print(f"   重複数: {count}件")
                print(f"   企業ID: {company_ids}")
                print(f"   企業名: {company_names}")
                
                # 各企業の詳細情報を表示
                for i, company_id in enumerate(company_ids):
                    c.execute('''
                        SELECT cla.id, cla.company_id, c.company_name, cla.created_at, cla.updated_at
                        FROM company_line_accounts cla
                        JOIN companies c ON cla.company_id = c.id
                        WHERE cla.line_channel_id = %s AND cla.company_id = %s
                    ''', (line_channel_id, company_id))
                    
                    detail = c.fetchone()
                    if detail:
                        print(f"     {i+1}. 企業ID {detail[1]}: {detail[2]} (作成: {detail[3]})")
        else:
            print("✅ 重複しているLINEチャネルIDはありません")
        
        # 特定のLINEチャネルIDの詳細を確認
        target_channel_id = "2007858939"
        print(f"\n🔍 特定のLINEチャネルID {target_channel_id} の詳細:")
        
        c.execute('''
            SELECT cla.id, cla.company_id, c.company_name, cla.line_channel_id,
                   cla.created_at, cla.updated_at
            FROM company_line_accounts cla
            JOIN companies c ON cla.company_id = c.id
            WHERE cla.line_channel_id = %s
            ORDER BY cla.created_at
        ''', (target_channel_id,))
        
        target_records = c.fetchall()
        
        if target_records:
            print(f"📋 該当レコード数: {len(target_records)}件")
            for record in target_records:
                print(f"  - ID: {record[0]}, 企業ID: {record[1]}, 企業名: {record[2]}")
                print(f"    作成日時: {record[4]}, 更新日時: {record[5]}")
        else:
            print(f"⚠️ LINEチャネルID {target_channel_id} のレコードが見つかりません")
        
        conn.close()
        return duplicates
        
    except Exception as e:
        print(f"❌ 調査エラー: {e}")
        import traceback
        traceback.print_exc()
        return None

def fix_duplicate_line_channels():
    """重複しているLINEチャネルIDを修正"""
    try:
        print("\n=== 重複LINEチャネルID修正 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 重複しているLINEチャネルIDを検索
        c.execute('''
            SELECT line_channel_id, COUNT(*) as count, 
                   array_agg(company_id) as company_ids
            FROM company_line_accounts cla
            WHERE line_channel_id IS NOT NULL
            GROUP BY line_channel_id
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        ''')
        
        duplicates = c.fetchall()
        
        if not duplicates:
            print("✅ 修正対象の重複はありません")
            return True
        
        fixed_count = 0
        for line_channel_id, count, company_ids in duplicates:
            print(f"\n🔧 LINEチャネルID {line_channel_id} の修正:")
            print(f"   重複数: {count}件, 企業ID: {company_ids}")
            
            # 最初の企業以外のLINEチャネルIDを更新
            for i, company_id in enumerate(company_ids[1:], 1):
                new_channel_id = f"{line_channel_id}_{i}"
                
                c.execute('''
                    UPDATE company_line_accounts 
                    SET line_channel_id = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE company_id = %s AND line_channel_id = %s
                ''', (new_channel_id, company_id, line_channel_id))
                
                print(f"   ✅ 企業ID {company_id}: {line_channel_id} → {new_channel_id}")
                fixed_count += 1
        
        # 変更をコミット
        conn.commit()
        conn.close()
        
        print(f"\n🎉 重複修正完了！修正件数: {fixed_count}件")
        return True
        
    except Exception as e:
        print(f"❌ 修正エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_fix():
    """修正結果を確認"""
    try:
        print("\n=== 修正結果確認 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 重複チェック
        c.execute('''
            SELECT line_channel_id, COUNT(*) as count
            FROM company_line_accounts cla
            WHERE line_channel_id IS NOT NULL
            GROUP BY line_channel_id
            HAVING COUNT(*) > 1
        ''')
        
        remaining_duplicates = c.fetchall()
        
        if remaining_duplicates:
            print(f"⚠️ まだ重複が残っています: {len(remaining_duplicates)}件")
            for line_channel_id, count in remaining_duplicates:
                print(f"  - {line_channel_id}: {count}件")
        else:
            print("✅ 重複は解消されました")
        
        # 全企業のLINEチャネルID一覧
        c.execute('''
            SELECT c.id, c.company_name, cla.line_channel_id, cla.created_at
            FROM companies c
            LEFT JOIN company_line_accounts cla ON c.id = cla.company_id
            ORDER BY c.id
        ''')
        
        companies = c.fetchall()
        conn.close()
        
        print(f"\n📊 全企業のLINEチャネルID一覧 ({len(companies)}件):")
        for company_id, company_name, line_channel_id, created_at in companies:
            print(f"  - 企業ID {company_id}: {company_name}")
            print(f"    LINEチャネルID: {line_channel_id or '未設定'}")
            print(f"    作成日時: {created_at}")
        
        return len(remaining_duplicates) == 0
        
    except Exception as e:
        print(f"❌ 確認エラー: {e}")
        return False

def main():
    """メイン関数"""
    print("🚀 重複LINEチャネルID調査・修正を開始します")
    
    # 1. 重複調査
    duplicates = check_duplicate_line_channels()
    
    if duplicates:
        print(f"\n📝 {len(duplicates)}件の重複が見つかりました")
        
        # 2. 重複修正
        if fix_duplicate_line_channels():
            print("\n✅ 重複修正が完了しました")
            
            # 3. 修正結果確認
            if verify_fix():
                print("\n🎉 すべての重複が解消されました！")
                print("\n📋 次のステップ:")
                print("1. 企業登録フォームを再試行")
                print("2. LINEチャネルIDが重複しないことを確認")
                print("3. 正常に登録できることを確認")
            else:
                print("\n⚠️ 一部の重複が残っています")
        else:
            print("\n❌ 重複修正に失敗しました")
    else:
        print("\n✅ 重複は見つかりませんでした")
        print("企業登録フォームを再試行してください")

if __name__ == "__main__":
    main() 