"""
SSHFS remote mount manager for KosFM.
Requires the system `sshfs` binary and `fusermount3`/`fusermount` to unmount.
"""

import os
import shutil
import subprocess
import tempfile
import threading
import time


class SSHFSManager:
    """Manage SSHFS remote mounts."""

    def __init__(self, base_mount_dir=None):
        if base_mount_dir is None:
            base_mount_dir = os.path.join(tempfile.gettempdir(), "kosfm_sshfs")
        self.base_mount_dir = base_mount_dir
        os.makedirs(self.base_mount_dir, exist_ok=True)
        self._mounts = {}  # alias -> mountpoint
        self._lock = threading.Lock()

    def sshfs_available(self):
        """Return True if sshfs is installed on the system."""
        return shutil.which("sshfs") is not None

    def _try_unmount_path(self, mountpoint):
        """Best-effort unmount a path directly (no alias)."""
        bin_path = self._unmount_bin()
        for cmd in ([bin_path, "-u", mountpoint] if bin_path else None,
                    [bin_path, "-u", "-z", mountpoint] if bin_path else None,
                    ["fusermount", "-u", mountpoint],
                    ["fusermount3", "-u", mountpoint],
                    ["umount", mountpoint]):
            if not cmd or not cmd[0]:
                continue
            try:
                subprocess.run(cmd, capture_output=True, timeout=5)
            except Exception:
                pass

    def _unmount_bin(self):
        """Return fusermount3/fusermount binary or None."""
        for name in ("fusermount3", "fusermount"):
            path = shutil.which(name)
            if path:
                return path
        return None

    def mount(self, user_host_path, alias=None, password=None, identity_file=None,
              port=None, options=None):
        """
        Mount a remote path via sshfs.

        Args:
            user_host_path: e.g. "user@host:/path" or "host:/path"
            alias: friendly name; defaults to user_host_path
            password: optional password (uses sshpass if provided)
            identity_file: optional SSH private key path
            port: optional SSH port
            options: dict of extra sshfs/ssh options

        Returns:
            mountpoint path on success, raises RuntimeError on failure.
        """
        if not self.sshfs_available():
            raise RuntimeError("sshfs is not installed on this system")

        alias = alias or user_host_path
        # Sanitize alias for filesystem path - keep it simple (no @:.)
        safe_alias = "".join(c if c.isalnum() or c in "-_" else "_" for c in alias)
        if not safe_alias:
            safe_alias = "mount"
        mountpoint = os.path.join(self.base_mount_dir, safe_alias)
        # Clean stale failed mount (I/O error) if present
        if os.path.exists(mountpoint):
            try:
                os.listdir(mountpoint)
            except OSError:
                # stale mount - try to unmount
                self._try_unmount_path(mountpoint)
                try:
                    os.rmdir(mountpoint)
                except Exception:
                    import shutil as _sh
                    try:
                        _sh.rmtree(mountpoint, ignore_errors=True)
                    except Exception:
                        pass
        os.makedirs(mountpoint, exist_ok=True)

        with self._lock:
            if alias in self._mounts:
                # Already mounted
                return self._mounts[alias]

        cmd = ["sshfs", user_host_path, mountpoint]

        opts = []
        if options:
            for k, v in options.items():
                if v is True:
                    opts.append(k)
                elif v is not None:
                    opts.append(f"{k}={v}")
        # defaults
        if "reconnect" not in (options or {}):
            opts.append("reconnect")
        if "idmap=user" not in (options or {}):
            opts.append("idmap=user")

        ssh_opts = []
        if port:
            ssh_opts.append(f"Port={port}")
        if identity_file:
            ssh_opts.append(f"IdentityFile={identity_file}")
        # Don't block on unknown host key after a fresh install
        ssh_opts.append("StrictHostKeyChecking=accept-new")
        if ssh_opts:
            opts.append("ssh_command=ssh " + " ".join(f"-o {o}" for o in ssh_opts))

        if opts:
            cmd.extend(["-o", ",".join(opts)])

        env = os.environ.copy()
        if password:
            sshpass = shutil.which("sshpass")
            if not sshpass:
                raise RuntimeError("sshpass is required for password-based SSHFS mounts")
            cmd = [sshpass, "-p", password] + cmd
            # Don't leak password in env longer than needed

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"sshfs mount failed: {e.stderr or e.stdout or 'unknown error'}")

        # Verify mount by listing
        time.sleep(0.5)
        try:
            os.listdir(mountpoint)
        except OSError as e:
            # mount probably failed
            try:
                self.unmount(alias, force=True)
            except Exception:
                self._try_unmount_path(mountpoint)
            raise RuntimeError(f"Mount did not become readable: {e}\nCheck remote path and that you are in 'fuse' group (groups | grep fuse). Try: fusermount -u {mountpoint}")

        with self._lock:
            self._mounts[alias] = mountpoint
        return mountpoint

    def unmount(self, alias, force=False):
        """Unmount a remote mount by alias."""
        with self._lock:
            mountpoint = self._mounts.pop(alias, None)
        if not mountpoint:
            return False

        umount_bin = self._unmount_bin()
        if umount_bin:
            cmd = [umount_bin, "-u", mountpoint]
            if force:
                cmd.append("-z")
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Unmount failed: {e.stderr or e.stdout}")
        else:
            try:
                subprocess.run(["umount", mountpoint], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Unmount failed: {e.stderr or e.stdout}")

        try:
            os.rmdir(mountpoint)
        except OSError:
            pass
        return True

    def unmount_all(self):
        """Unmount all managed mounts."""
        aliases = list(self._mounts.keys())
        failed = []
        for alias in aliases:
            try:
                self.unmount(alias)
            except Exception as e:
                failed.append(f"{alias}: {e}")
        return failed

    def list_mounts(self):
        """Return dict of alias -> mountpoint for active managed mounts."""
        with self._lock:
            return dict(self._mounts)
