
"""
XDG MIME integration for KosFM.
Handles MIME type detection and application associations on Linux.
"""

import os
import re
import subprocess
from pathlib import Path
from configparser import ConfigParser


def get_mime_type(file_path):
    """
    Get MIME type of file using xdg-mime.
    """
    if not os.path.exists(file_path):
        return None
        
    try:
        result = subprocess.run(
            ['xdg-mime', 'query', 'filetype', file_path],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream'


def get_default_application(mime_type):
    """
    Get default application for MIME type.
    """
    if not mime_type:
        return None
        
    try:
        result = subprocess.run(
            ['xdg-mime', 'query', 'default', mime_type],
            capture_output=True,
            text=True,
            check=True
        )
        desktop_file = result.stdout.strip()
        return desktop_file if desktop_file else None
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


def set_default_application(mime_type, desktop_file):
    """
    Set default application for MIME type.
    """
    try:
        subprocess.run(
            ['xdg-mime', 'default', desktop_file, mime_type],
            check=True
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def find_applications_for_mime_type(mime_type):
    """
    Find all applications that can handle a MIME type.
    """
    if not mime_type:
        return []
        
    apps = []
    desktop_dirs = [
        Path('/usr/share/applications'),
        Path('/usr/local/share/applications'),
        Path.home() / '.local' / 'share' / 'applications',
    ]
    
    print(f"DEBUG: Looking for apps for MIME type: {mime_type}")
    
    for desktop_dir in desktop_dirs:
        if not desktop_dir.exists():
            print(f"DEBUG: Directory does not exist: {desktop_dir}")
            continue
            
        print(f"DEBUG: Scanning {desktop_dir}")
        desktop_files = list(desktop_dir.glob('*.desktop'))
        print(f"DEBUG: Found {len(desktop_files)} .desktop files")
        
        for desktop_file in desktop_files:
            app_info = parse_desktop_file(desktop_file)
            if app_info:
                print(f"DEBUG: Checking {desktop_file.name}: mime_types={app_info.get('mime_types', [])}")
                if mime_type_matches(mime_type, app_info.get('mime_types', [])):
                    app_info['desktop_file'] = desktop_file.name
                    apps.append(app_info)
                    print(f"DEBUG: -> MATCH: {app_info['name']}")
                
    # Remove duplicates
    seen = set()
    unique_apps = []
    for app in apps:
        if app['desktop_file'] not in seen:
            seen.add(app['desktop_file'])
            unique_apps.append(app)
            
    print(f"DEBUG: Total matching apps: {len(unique_apps)}")
    return unique_apps


def mime_type_matches(target_mime, app_mime_types):
    """Check if target MIME type matches any of app's MIME types."""
    for app_mime in app_mime_types:
        if app_mime == target_mime:
            return True
        if app_mime.endswith('/*'):
            prefix = app_mime[:-1]
            if target_mime.startswith(prefix):
                return True
    return False


def parse_desktop_file(desktop_path):
    """Parse a .desktop file and extract relevant fields."""
    if not os.path.exists(desktop_path):
        return None
        
    try:
        config = ConfigParser(interpolation=None)
        config.read(desktop_path)
        
        if 'Desktop Entry' not in config:
            print(f"DEBUG: No [Desktop Entry] in {desktop_path.name}")
            return None
            
        entry = config['Desktop Entry']
        
        # Skip NoDisplay and hidden apps
        try:
            if entry.getboolean('NoDisplay', False):
                return None
            if entry.getboolean('Hidden', False):
                return None
        except:
            pass
            
        # Get Type - must be Application
        app_type = entry.get('Type', '')
        if app_type != 'Application':
            return None
            
        name = entry.get('Name', 'Unknown')
        icon = entry.get('Icon', 'application-x-executable')
        exec_cmd = entry.get('Exec', '')
        mime_types_str = entry.get('MimeType', '')
        
        # Parse MimeType field
        mime_types = [m.strip() for m in mime_types_str.split(';') if m.strip()]
        
        print(f"DEBUG: Parsed {desktop_path.name}: name={name}, type={app_type}, mime_types={mime_types}")
        
        return {
            'name': name,
            'icon': icon,
            'exec': exec_cmd,
            'mime_types': mime_types,
        }
        
    except Exception as e:
        print(f"DEBUG: Error parsing {desktop_path}: {e}")
        return None


def launch_application(file_path, app_info):
    """Launch a file with a specific application."""
    if not app_info or 'exec' not in app_info:
        return False
        
    exec_cmd = app_info['exec']
    cmd = exec_cmd
    
    # Replace field codes
    if '%F' in cmd:
        cmd = cmd.replace('%F', file_path)
    elif '%f' in cmd:
        cmd = cmd.replace('%f', file_path)
    elif '%U' in cmd:
        cmd = cmd.replace('%U', file_path)
    elif '%u' in cmd:
        cmd = cmd.replace('%u', file_path)
    else:
        cmd = f"{cmd} {file_path}"
        
    # Remove other field codes
    cmd = re.sub(r'%\w', '', cmd)
    cmd = ' '.join(cmd.split())
    
    try:
        subprocess.Popen(cmd, shell=True, 
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def open_file_with_default(file_path):
    """Open file with default application using xdg-open."""
    try:
        subprocess.Popen(['xdg-open', file_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False
