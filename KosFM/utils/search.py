"""
Search utilities for KosFM.
Provides name filtering and recursive directory search.
"""

import os
import fnmatch
import threading


def matches_query(name, query, use_glob=False):
    """Check if name matches query (case-insensitive).

    Args:
        name: File/directory name to test.
        query: Search string (substring or glob if use_glob).
        use_glob: If True, treat query as glob pattern.
    """
    if not query:
        return True
    if use_glob:
        return fnmatch.fnmatch(name.lower(), query.lower())
    return query.lower() in name.lower()





def filter_entries(entries, query, use_glob=False):
    """Filter a list of DirEntry-like objects by name."""
    if not query:
        return list(entries)
    return [e for e in entries if matches_query(e.name, query, use_glob)]




def walk_search(root_path, query, show_hidden=False, use_glob=False,
                max_results=10000, cancel_event=None, on_batch=None, batch_size=200):
    """Recursively search under root_path for entries matching query.

    Yields batches via on_batch callback to avoid blocking UI.
    Returns total count found.

    Args:
        root_path: Directory to start from.
        query: Search string.
        show_hidden: Include hidden files/dirs.
        use_glob: Treat query as glob.
        max_results: Stop after this many matches.
        cancel_event: threading.Event to signal cancellation.
        on_batch: Callable(list[dict]) called per batch of matches.
        batch_size: Number of matches per batch callback.
    """
    if not query:
        return 0

    count = 0
    batch = []

    def flush():
        nonlocal batch
        if batch and on_batch:
            on_batch(list(batch))
        batch = []

    stack = [root_path]
    visited = set()

    while stack:
        if cancel_event and cancel_event.is_set():
            flush()
            break

        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)

        try:
            with os.scandir(current) as it:
                subdirs = []
                for entry in it:
                    if cancel_event and cancel_event.is_set():
                        break
                    if not show_hidden and entry.name.startswith('.'):
                        continue
                    try:
                        is_dir = entry.is_dir(follow_symlinks=False)
                    except OSError:
                        continue

                    if matches_query(entry.name, query, use_glob):
                        try:
                            stat = entry.stat(follow_symlinks=False)
                        except OSError:
                            continue
                        batch.append({
                            'name': entry.name,
                            'path': entry.path,
                            'is_dir': is_dir,
                            'size': stat.st_size,
                            'mtime': stat.st_mtime,
                        })
                        count += 1
                        if len(batch) >= batch_size:
                            flush()
                        if count >= max_results:
                            flush()
                            return count

                    if is_dir:
                        subdirs.append(entry.path)

                # DFS: push subdirs in reverse for alphabetical-ish order
                for d in reversed(subdirs):
                    try:
                        if os.path.islink(d):
                            continue
                    except OSError:
                        continue
                    stack.append(d)
                    if count >= max_results:
                        break

        except (PermissionError, OSError):
            continue

    flush()
    return count
