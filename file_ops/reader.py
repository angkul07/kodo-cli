import os
from pathlib import Path
from typing import List

def get_project_structure() -> str:
    """Get a overview of the current project structure"""
    current_dir = Path.cwd()
    structure = []
    
    # Common code file extensions
    code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.rb', '.php'}
    
    for root, dirs, files in os.walk(current_dir):
        # Skip common ignore directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env', 'bin']]
        
        level = root.replace(str(current_dir), '').count(os.sep)
        
        # Limit recursion depth
        if level > 3:
            dirs.clear()
            continue
            
        indent = ' ' * 2 * level
        structure.append(f"{indent}{os.path.basename(root)}/")
        
        # Limit files shown
        subindent = ' ' * 2 * (level + 1)
        for file in files[:10]:  # Show max 10 files per directory
            if Path(file).suffix in code_extensions:
                structure.append(f"{subindent}{file}")
    
    return "\n".join(structure)

def read_file_content(filepath: str) -> str:
    """Safely read file content"""
    try:
        path = Path(filepath)
        if not path.exists():
            return f"Error: File {filepath} does not exist"
        
        # Check file size (limit to 50KB for safety)
        if path.stat().st_size > 51200:
            return f"Error: File {filepath} is too large (>50KB)"
        
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file {filepath}: {str(e)}"
    

def get_relevant_files(query: str, max_files: int = 5) -> List[str]:
    """Get list of relevant files based on query keywords"""
    current_dir = Path.cwd()
    code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.rb', '.php'}
    relevant_files = []
    
    query_lower = query.lower()
    keywords = query_lower.split()
    
    for file_path in current_dir.rglob("*"):
        if (file_path.is_file() and 
            file_path.suffix in code_extensions and 
            not any(part.startswith('.') for part in file_path.parts)):
            
            # Check if filename or path contains query keywords
            file_str = str(file_path).lower()
            if any(keyword in file_str for keyword in keywords):
                relevant_files.append(str(file_path.relative_to(current_dir)))
        
        if len(relevant_files) >= max_files:
            break
    
    return relevant_files

def create_context_for_chat(query: str) -> str:
    """Create context string for chat queries"""
    context = []
    
    # Add project structure
    context.append("## Project Structure:")
    context.append(get_project_structure())
    context.append("")
    
    # Add relevant files content
    relevant_files = get_relevant_files(query)
    if relevant_files:
        context.append("## Relevant Files:")
        for filepath in relevant_files:
            context.append(f"### {filepath}")
            content = read_file_content(filepath)
            if not content.startswith("Error:"):
                context.append(f"```\n{content}\n```")
            else:
                context.append(content)
            context.append("")
    
    return "\n".join(context)