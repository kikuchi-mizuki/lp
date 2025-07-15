#!/usr/bin/env python3
"""
画像ファイルを最適化するスクリプト
"""

from PIL import Image
import os
import glob

def optimize_image(input_path, output_path, max_size=(800, 800), quality=85):
    """画像を最適化して保存"""
    try:
        with Image.open(input_path) as img:
            # 画像の形式を確認
            if img.mode in ('RGBA', 'LA'):
                # アルファチャンネルがある場合は白背景に変換
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # アスペクト比を保ってリサイズ
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 最適化して保存
            img.save(output_path, 'JPEG', quality=quality, optimize=True)
            print(f"最適化完了: {input_path} -> {output_path}")
            
    except Exception as e:
        print(f"エラー: {input_path} - {e}")

def main():
    """メイン処理"""
    # 画像ディレクトリ
    image_dir = "static/images"
    
    # 最適化対象の画像ファイル
    target_files = [
        "accounting_icon.png",
        "task_icon.png", 
        "secretary.png",
        "line_accounting.PNG",
        "line_schedule.PNG",
        "line_task.PNG"
    ]
    
    # バックアップディレクトリを作成
    backup_dir = "static/images/backup"
    os.makedirs(backup_dir, exist_ok=True)
    
    for filename in target_files:
        input_path = os.path.join(image_dir, filename)
        if os.path.exists(input_path):
            # バックアップを作成
            backup_path = os.path.join(backup_dir, filename)
            if not os.path.exists(backup_path):
                import shutil
                shutil.copy2(input_path, backup_path)
                print(f"バックアップ作成: {backup_path}")
            
            # 出力ファイル名を決定
            name, ext = os.path.splitext(filename)
            output_filename = f"{name}_optimized.jpg"
            output_path = os.path.join(image_dir, output_filename)
            
            # 画像を最適化
            optimize_image(input_path, output_path)
        else:
            print(f"ファイルが見つかりません: {input_path}")

if __name__ == "__main__":
    main() 