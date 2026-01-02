#!/usr/bin/env python3
"""
Script để cleanup các log files cũ.

Xóa các log files cũ hơn 7 ngày trong thư mục gốc.
Giữ lại các log files gần đây để debug.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Thêm project root vào path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def cleanup_old_logs(days_to_keep=7, dry_run=False):
    """
    Xóa các log files cũ hơn days_to_keep ngày.
    
    Args:
        days_to_keep: Số ngày giữ lại log files (mặc định 7 ngày)
        dry_run: Nếu True, chỉ hiển thị files sẽ bị xóa, không xóa thực sự
    """
    project_root = Path(__file__).parent.parent
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    # Tìm tất cả log files (tránh duplicate)
    log_files = set(project_root.glob("*.log"))
    log_files.update(project_root.glob("vocab_generate*.log"))
    log_files = list(log_files)
    
    deleted_count = 0
    deleted_size = 0
    kept_count = 0
    
    print(f"Dang tim log files cu hon {days_to_keep} ngay...")
    print(f"Cutoff date: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project root: {project_root}")
    print()
    
    for log_file in log_files:
        if not log_file.exists():
            continue
        
        # Lấy thời gian modified
        mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
        file_size = log_file.stat().st_size
        
        if mtime < cutoff_date:
            # File cũ, sẽ xóa
            size_mb = file_size / (1024 * 1024)
            prefix = "[DRY RUN] " if dry_run else ""
            print(f"{prefix}Xoa: {log_file.name}")
            print(f"   Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Size: {size_mb:.2f} MB")
            print()
            
            if not dry_run:
                try:
                    log_file.unlink()
                    deleted_count += 1
                    deleted_size += file_size
                except Exception as e:
                    print(f"   Loi khi xoa: {e}")
            else:
                deleted_count += 1
                deleted_size += file_size
        else:
            # Giữ lại
            size_mb = file_size / (1024 * 1024)
            print(f"Giu lai: {log_file.name} ({size_mb:.2f} MB, {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
            kept_count += 1
    
    print()
    print("=" * 60)
    if dry_run:
        print(f"DRY RUN - Se xoa {deleted_count} files ({deleted_size / (1024*1024):.2f} MB)")
    else:
        print(f"Da xoa {deleted_count} files ({deleted_size / (1024*1024):.2f} MB)")
    print(f"Giu lai {kept_count} files")
    print("=" * 60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Cleanup old log files")
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Số ngày giữ lại log files (mặc định: 7)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chỉ hiển thị files sẽ bị xóa, không xóa thực sự"
    )
    
    args = parser.parse_args()
    
    cleanup_old_logs(days_to_keep=args.days, dry_run=args.dry_run)
