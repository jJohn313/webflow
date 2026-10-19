#!/usr/bin/env python3
"""
lib/cache_manager.py - LRU Disk Cache Quota & Storage Manager for Webflow
Enforces per-workbench and ephemeral disk cache quotas (e.g. 200MB per workbench).
Ensures pages leverage persistent disk cache while strictly bounding storage growth.
"""
import os
import time
from pathlib import Path


def get_cache_dir_size_bytes(cache_dir: Path) -> int:
    """Returns total size in bytes of all files in cache_dir."""
    if not cache_dir.exists():
        return 0
    total = 0
    try:
        for root, _, files in os.walk(cache_dir):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total += os.path.getsize(fp)
                except (OSError, FileNotFoundError):
                    pass
    except Exception:
        pass
    return total


def get_cache_dir_size_mb(cache_dir: Path) -> float:
    """Returns total size in megabytes of all files in cache_dir."""
    return get_cache_dir_size_bytes(cache_dir) / (1024 * 1024)


def enforce_lru_cache_quota(cache_dir: Path, max_mb: int = 200):
    """
    Enforces a strict LRU (Least Recently Used) disk quota on cache_dir.
    If total size exceeds max_mb, deletes the oldest accessed cache files
    until the size drops to 85% of the quota limit (leaving headroom).
    """
    if not cache_dir.exists():
        return

    try:
        max_bytes = max_mb * 1024 * 1024
        target_bytes = int(max_bytes * 0.85)

        files = []
        total_size = 0

        for root, _, fnames in os.walk(cache_dir):
            for fn in fnames:
                fp = os.path.join(root, fn)
                try:
                    st = os.stat(fp)
                    total_size += st.st_size
                    # Use access time (atime), falling back to mtime
                    atime = st.st_atime if st.st_atime > 0 else st.st_mtime
                    files.append((atime, st.st_size, fp))
                except (OSError, FileNotFoundError):
                    pass

        if total_size > max_bytes:
            # Sort files by oldest access time first (LRU)
            files.sort(key=lambda x: x[0])
            for _, size, path in files:
                try:
                    os.unlink(path)
                    total_size -= size
                    if total_size <= target_bytes:
                        break
                except (OSError, FileNotFoundError):
                    pass
    except Exception:
        pass
