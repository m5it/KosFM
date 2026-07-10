#!/usr/bin/env python3
"""
KosFM Installer Script

Installs KosFM by creating a symlink in ~/.local/bin and a .desktop file
in ~/.local/share/applications.

Usage:
    ./install.py --install     Install KosFM
    ./install.py --uninstall   Remove KosFM
    ./install.py --status      Check installation status
"""

import os
import sys
import stat
import argparse
from pathlib import Path


# Installation paths
LOCAL_BIN = Path.home() / ".local" / "bin"
LOCAL_SHARE = Path.home() / ".local" / "share"
APPLICATIONS_DIR = LOCAL_SHARE / "applications"
DESKTOP_FILE = APPLICATIONS_DIR / "KosFM.desktop"
SYMLINK_PATH = LOCAL_BIN / "kosfm"


def ensure_executable():
    """Ensure this script is executable."""
    script_path = Path(__file__).resolve()
    current_mode = script_path.stat().st_mode
    if not (current_mode & stat.S_IXUSR):
        print("Making install.py executable...")
        script_path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def get_script_dir():
    """Get the directory where this script is located."""
    return Path(__file__).parent.resolve()


def get_kosfm_dir():
    """Get the KosFM installation directory."""
    script_dir = get_script_dir()
    # Check if we're in the KosFM root (where main.py exists)
    if (script_dir / "main.py").exists():
        return script_dir
    return None


def check_installation():
    """Check if KosFM is currently installed."""
    symlink_exists = SYMLINK_PATH.exists() or SYMLINK_PATH.is_symlink()
    desktop_exists = DESKTOP_FILE.exists()
    return symlink_exists or desktop_exists


def main():
    """Main entry point."""
    # Ensure script is executable
    ensure_executable()
    
    parser = argparse.ArgumentParser(
        description="Install or uninstall KosFM file manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --install      Install KosFM to ~/.local/bin
  %(prog)s --uninstall    Remove KosFM from system
  %(prog)s --status       Check installation status
        """
    )
    
    parser.add_argument(
        "--install", "-i",
        action="store_true",
        help="Install KosFM"
    )
    
    parser.add_argument(
        "--uninstall", "-u",
        action="store_true",
        help="Uninstall KosFM"
    )
    
    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="Check installation status"
    )
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if not (args.install or args.uninstall or args.status):
        parser.print_help()
        sys.exit(0)
    
    # Check status
    if args.status:
        return show_status()
    
    # Install
    if args.install:
        return install()
    
    # Uninstall
    if args.uninstall:
        return uninstall()


def show_status():
    """Show current installation status."""
    print("=" * 50)
    print("KosFM Installation Status")
    print("=" * 50)
    
    kosfm_dir = get_kosfm_dir()
    if kosfm_dir:
        print(f"✓ KosFM directory found: {kosfm_dir}")
        # Check if main.py is executable
        main_py = kosfm_dir / "main.py"
        if main_py.exists():
            is_exec = os.access(main_py, os.X_OK)
            if is_exec:
                print(f"✓ main.py is executable")
            else:
                print(f"⚠ main.py is NOT executable (run with 'python kosfm')")
    else:
        print("✗ KosFM directory not found")
    
    if SYMLINK_PATH.exists():
        if SYMLINK_PATH.is_symlink():
            target = os.readlink(SYMLINK_PATH)
            print(f"✓ Symlink exists: {SYMLINK_PATH} -> {target}")
        else:
            print(f"⚠ Warning: {SYMLINK_PATH} exists but is not a symlink")
    else:
        print(f"✗ Symlink not found: {SYMLINK_PATH}")
    
    if DESKTOP_FILE.exists():
        print(f"✓ Desktop file exists: {DESKTOP_FILE}")
    else:
        print(f"✗ Desktop file not found: {DESKTOP_FILE}")
    
    print("=" * 50)
    
    if check_installation():
        print("Status: KosFM is installed")
    else:
        print("Status: KosFM is not installed")
    
    return 0


def install():
    """Install KosFM."""
    print("=" * 50)
    print("Installing KosFM")
    print("=" * 50)
    
    # Check if already installed
    if check_installation():
        print("KosFM is already installed!")
        print("Use --uninstall first to remove the existing installation.")
        print("Or use --status to check the installation status.")
        return 1
    
    # Get KosFM directory
    kosfm_dir = get_kosfm_dir()
    if not kosfm_dir:
        print("Error: Cannot find KosFM directory!")
        print("Make sure you're running this script from the KosFM folder.")
        return 1
    
    print(f"KosFM directory: {kosfm_dir}")
    
    # Make main.py executable
    main_py = kosfm_dir / "main.py"
    if main_py.exists():
        print(f"Making main.py executable")
        current_mode = main_py.stat().st_mode
        main_py.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    
    # Create ~/.local/bin if needed
    if not LOCAL_BIN.exists():
        print(f"Creating directory: {LOCAL_BIN}")
        LOCAL_BIN.mkdir(parents=True, exist_ok=True)
    
    # Create symlink
    try:
        print(f"Creating symlink: {SYMLINK_PATH} -> {kosfm_dir}/main.py")
        SYMLINK_PATH.symlink_to(kosfm_dir / "main.py")
        print("✓ Symlink created successfully")
    except OSError as e:
        print(f"✗ Error creating symlink: {e}")
        return 1
    
    # Create ~/.local/share/applications if needed
    if not APPLICATIONS_DIR.exists():
        print(f"Creating directory: {APPLICATIONS_DIR}")
        APPLICATIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create .desktop file
    desktop_content = f"""[Desktop Entry]
Name=KosFM
Comment=Simple file manager built with Python and tkinter
Exec={SYMLINK_PATH}
Icon=system-file-manager
Type=Application
Terminal=false
Categories=System;FileTools;FileManager;
Keywords=file;manager;browser;directory;folder;
MimeType=inode/directory;
"""
    
    try:
        print(f"Creating desktop file: {DESKTOP_FILE}")
        DESKTOP_FILE.write_text(desktop_content)
        DESKTOP_FILE.chmod(0o755)
        print("✓ Desktop file created successfully")
    except OSError as e:
        print(f"✗ Error creating desktop file: {e}")
        return 1
    
    # Update desktop database
    try:
        print("Updating desktop database...")
        os.system("update-desktop-database ~/.local/share/applications 2>/dev/null")
        print("✓ Desktop database updated")
    except:
        pass  # Not critical if this fails
    
    print("=" * 50)
    print("Installation complete!")
    print("=" * 50)
    print()
    print("✓ main.py is now executable")
    print("✓ Symlink created: ~/.local/bin/kosfm")
    print("✓ Desktop entry created")
    print()
    print("You can now run KosFM by typing:")
    print("  kosfm")
    print()
    print("Or from your application menu.")
    print()
    print("Note: You may need to log out and log back in for")
    print("      the PATH changes to take effect.")
    
    return 0


def uninstall():
    """Uninstall KosFM."""
    print("=" * 50)
    print("Uninstalling KosFM")
    print("=" * 50)
    
    # Check if installed
    if not check_installation():
        print("KosFM is not installed!")
        print("Nothing to uninstall.")
        return 0
    
    # Ask for confirmation
    response = input("Are you sure you want to uninstall KosFM? [y/N]: ")
    if response.lower() not in ('y', 'yes'):
        print("Uninstall cancelled.")
        return 0
    
    # Remove symlink
    if SYMLINK_PATH.exists():
        try:
            print(f"Removing symlink: {SYMLINK_PATH}")
            SYMLINK_PATH.unlink()
            print("✓ Symlink removed")
        except OSError as e:
            print(f"✗ Error removing symlink: {e}")
            return 1
    
    # Remove desktop file
    if DESKTOP_FILE.exists():
        try:
            print(f"Removing desktop file: {DESKTOP_FILE}")
            DESKTOP_FILE.unlink()
            print("✓ Desktop file removed")
        except OSError as e:
            print(f"✗ Error removing desktop file: {e}")
            return 1
    
    # Update desktop database
    try:
        print("Updating desktop database...")
        os.system("update-desktop-database ~/.local/share/applications 2>/dev/null")
        print("✓ Desktop database updated")
    except:
        pass
    
    print("=" * 50)
    print("Uninstall complete!")
    print("=" * 50)
    print()
    print("KosFM has been removed from your system.")
    print("The KosFM directory itself was not removed.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
