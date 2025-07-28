#!/usr/bin/env python3
from datetime import datetime, timedelta

def debug_period_calculation():
    print("=== 期間計算デバッグ ===")
    
    # トライアル終了日
    trial_end_timestamp = 1733299506  # 2025-08-04 08:05:06
    # 正しいタイムスタンプを計算
    trial_end_date = datetime(2025, 8, 4, 8, 5, 6)
    trial_end_timestamp = int(trial_end_date.timestamp())
    trial_end_date = datetime.fromtimestamp(trial_end_timestamp)
    
    print(f"トライアル終了日: {trial_end_date}")
    
    # 現在の計算方法
    start_date = trial_end_date
    print(f"開始日: {start_date}")
    
    # 次の月の同じ日付を計算
    if start_date.month == 12:
        end_date = start_date.replace(year=start_date.year + 1, month=1)
    else:
        end_date = start_date.replace(month=start_date.month + 1)
    
    print(f"次の月の同じ日付: {end_date}")
    
    # 1日前に調整（翌月の同じ日付の前日）
    end_date_adjusted = end_date - timedelta(days=1)
    print(f"1日前に調整後: {end_date_adjusted}")
    
    # 期間の日数を計算
    period_days = (end_date_adjusted - start_date).days + 1
    print(f"期間の日数: {period_days}日")
    
    # 期待される結果
    print(f"\n期待される期間:")
    print(f"開始: 2025-08-04")
    print(f"終了: 2025-09-03")
    print(f"日数: 31日")

if __name__ == "__main__":
    debug_period_calculation() 