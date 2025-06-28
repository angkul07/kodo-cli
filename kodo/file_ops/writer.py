from pathlib import Path
from typing import Optional
from datetime import datetime

def write_file_content(filepath: str, content: str, create_backup: bool = True) -> bool:
    """Write content to file with optional backup"""
    try:
        path = Path(filepath)
        
        # Create backup if file exists
        if create_backup and path.exists():
            backup_path = create_backup_file(filepath)
            if backup_path:
                print(f"Backup created: {backup_path}")
        
        # Create directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"Error writing file {filepath}: {str(e)}")
        return False

def create_backup_file(filepath: str) -> Optional[str]:
    """Create a backup of the file"""
    try:
        path = Path(filepath)
        if not path.exists():
            return None
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{path.stem}.backup_{timestamp}{path.suffix}"
        backup_path = path.parent / backup_name
        
        # Copy file content
        with open(path, 'r', encoding='utf-8') as original:
            content = original.read()
        
        with open(backup_path, 'w', encoding='utf-8') as backup:
            backup.write(content)
        
        return str(backup_path)
    except Exception as e:
        print(f"Error creating backup: {str(e)}")
        return None

def show_diff(original_content: str, new_content: str, filepath: str):
    """Show a simple diff between original and new content"""
    from rich.console import Console
    
    console = Console()
    
    # Simple line-by-line comparison
    original_lines = original_content.splitlines()
    new_lines = new_content.splitlines()
    
    console.print(f"\nProposed changes for: {filepath}")
    console.print("=" * 50)
    
    max_lines = max(len(original_lines), len(new_lines))
    
    for i in range(max_lines):
        orig_line = original_lines[i] if i < len(original_lines) else ""
        new_line = new_lines[i] if i < len(new_lines) else ""
        
        if orig_line != new_line:
            if orig_line:
                console.print(f"- {orig_line}", style="red")
            if new_line:
                console.print(f"+ {new_line}", style="green")
    
    console.print("=" * 50)