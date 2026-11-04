"""
Archive handling utility for KosFM.
Supports listing, extracting, and creating ZIP and TAR archives.
"""

import os
import shutil
import tarfile
import zipfile
from pathlib import Path


ARCHIVE_EXTENSIONS = (".zip", ".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz")


def is_archive(path):
    """Return True if the file extension indicates a supported archive."""
    if not os.path.isfile(path):
        return False
    name_lower = path.lower()
    return any(name_lower.endswith(ext) for ext in ARCHIVE_EXTENSIONS)


def list_archive(path):
    """Return a list of member names in the archive, or None on failure."""
    if not is_archive(path):
        return None
    try:
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path, 'r') as zf:
                return zf.namelist()
        if tarfile.is_tarfile(path):
            with tarfile.open(path, 'r:*') as tf:
                return [m.name for m in tf.getmembers()]
    except (OSError, zipfile.BadZipFile, tarfile.TarError):
        pass
    return None


def extract_archive(path, dest_dir):
    """Extract an archive to the destination directory."""
    if not is_archive(path):
        raise ValueError(f"Unsupported archive: {path}")

    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path, 'r') as zf:
            zf.extractall(dest)
        return True

    if tarfile.is_tarfile(path):
        with tarfile.open(path, 'r:*') as tf:
            tf.extractall(dest)
        return True

    raise ValueError(f"Unsupported archive: {path}")


def _unique_dest_path(dest_dir, name):
    """Generate a unique destination path, adding suffix if needed."""
    dest_path = Path(dest_dir) / name
    if not dest_path.exists():
        return str(dest_path)
    base, ext = os.path.splitext(name)
    counter = 1
    while dest_path.exists():
        dest_path = Path(dest_dir) / f"{base} ({counter}){ext}"
        counter += 1
    return str(dest_path)


def create_archive(source_paths, dest_path):
    """Create an archive at dest_path containing source_paths."""
    if not source_paths:
        raise ValueError("No paths to archive")

    dest_path = str(dest_path)
    dest_lower = dest_path.lower()

    if dest_lower.endswith(".zip"):
        return _create_zip(source_paths, dest_path)

    tar_mode = None
    if dest_lower.endswith((".tar.gz", ".tgz")):
        tar_mode = "w:gz"
    elif dest_lower.endswith((".tar.bz2", ".tbz2")):
        tar_mode = "w:bz2"
    elif dest_lower.endswith((".tar.xz", ".txz")):
        tar_mode = "w:xz"
    elif dest_lower.endswith(".tar"):
        tar_mode = "w"

    if tar_mode:
        return _create_tar(source_paths, dest_path, tar_mode)

    raise ValueError(f"Unsupported archive format: {dest_path}")


def _create_zip(source_paths, dest_path):
    """Create a zip archive from the given source paths."""
    with zipfile.ZipFile(dest_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for src in source_paths:
            src = Path(src)
            if src.is_dir():
                for file_path in src.rglob("*"):
                    arcname = str(file_path.relative_to(src.parent))
                    zf.write(file_path, arcname)
            elif src.is_file():
                zf.write(src, src.name)
    return True


def _create_tar(source_paths, dest_path, mode):
    """Create a tar archive from the given source paths."""
    with tarfile.open(dest_path, mode) as tf:
        for src in source_paths:
            src = Path(src)
            tf.add(src, arcname=src.name)
    return True
