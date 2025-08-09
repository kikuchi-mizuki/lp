#!/usr/bin/env python3
"""
アプリのデータベースを安全に初期化するユーティリティ。

実行内容:
1) 全テーブルの内容をJSONバックアップ (backups/db_backup_YYYYmmdd_HHMMSS.json)
2) 全テーブルのデータを削除
   - PostgreSQL: TRUNCATE ... RESTART IDENTITY CASCADE
   - SQLite: DELETE FROM ...; シーケンスも初期化

使用例:
  python lp/scripts/clear_database.py --yes

注意:
 - 破壊的操作です。--yes を付けないと実行しません。
 - 接続情報は環境変数 RAILWAY_DATABASE_URL または DATABASE_URL を使用します。
"""

import json
import os
import sys
import datetime
from typing import List, Dict, Any

# パッケージパスを追加（scripts/ の親である lp/ を sys.path に入れる）
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from utils.db import get_db_connection, get_db_type


def fetch_all_table_names_postgres(cursor) -> List[str]:
    cursor.execute(
        """
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename NOT LIKE 'pg_%'
          AND tablename NOT LIKE 'sql_%'
        ORDER BY tablename;
        """
    )
    return [row[0] for row in cursor.fetchall()]


def fetch_all_table_names_sqlite(cursor) -> List[str]:
    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name;
        """
    )
    return [row[0] for row in cursor.fetchall()]


def dump_table_to_memory(cursor, table_name: str) -> List[Dict[str, Any]]:
    try:
        cursor.execute(f'SELECT * FROM {table_name}')
        colnames = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        records = []
        for row in rows:
            # psycopg2: tuple / sqlite3: tuple → dict に変換
            record = {}
            for idx, col in enumerate(colnames):
                value = row[idx]
                try:
                    json.dumps(value)
                    record[col] = value
                except TypeError:
                    # シリアライズできない型は文字列化
                    record[col] = str(value)
            records.append(record)
        return records
    except Exception as e:
        # 権限や一時テーブルで失敗しても続行
        return [{"_error": f"dump failed: {e}"}]


def backup_database() -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    db_type = get_db_type()

    if db_type == 'postgresql':
        tables = fetch_all_table_names_postgres(cursor)
    else:
        tables = fetch_all_table_names_sqlite(cursor)

    snapshot = {
        'meta': {
            'timestamp': datetime.datetime.now().isoformat(),
            'db_type': db_type,
            'table_count': len(tables),
        },
        'tables': {}
    }

    for table in tables:
        snapshot['tables'][table] = dump_table_to_memory(cursor, table)

    conn.close()

    os.makedirs('backups', exist_ok=True)
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    path = os.path.join('backups', f'db_backup_{ts}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    return path


def clear_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    db_type = get_db_type()

    if db_type == 'postgresql':
        tables = fetch_all_table_names_postgres(cursor)
        if tables:
            joined = ', '.join([f'"{t}"' for t in tables])
            cursor.execute(f'TRUNCATE TABLE {joined} RESTART IDENTITY CASCADE')
            conn.commit()
    else:
        tables = fetch_all_table_names_sqlite(cursor)
        # 外部キー制約を一時無効化
        try:
            cursor.execute('PRAGMA foreign_keys = OFF')
        except Exception:
            pass
        for t in tables:
            cursor.execute(f'DELETE FROM {t}')
        # オートインクリメント初期化
        try:
            cursor.execute("DELETE FROM sqlite_sequence")
        except Exception:
            pass
        conn.commit()

    conn.close()


def main():
    if '--yes' not in sys.argv:
        print('この操作は破壊的です。実行するには --yes を付けてください。')
        sys.exit(1)

    print('バックアップを作成しています...')
    backup_path = backup_database()
    print(f'バックアップ作成完了: {backup_path}')

    print('全テーブルのデータを削除しています...')
    clear_database()
    print('削除完了。')


if __name__ == '__main__':
    main()


