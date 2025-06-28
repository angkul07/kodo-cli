import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.markdown import Markdown
import hashlib
from rich.progress import Progress, TaskID

from ast_generator import ASTGenerator, save_ast_snapshot, load_ast_snapshot, is_ast_current

console = Console()

class ContextManager:
    """Advanced context management using the cline method for intelligent codebase indexing"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.context_dir = self.project_root / "kodo_context" / "context"
        self.cache_dir = self.project_root / "kodo_context" / "cache"
        
        # Context file paths
        self.snapshot_path = self.context_dir / "snapshot.json"
        self.overview_path = self.context_dir / "overview.md"
        self.history_path = self.context_dir / "history.md"
        self.rules_path = self.context_dir / "rules.cline"
        
    def initialize_context(self) -> bool:
        """Initialize the complete context system for a project"""
        try:
            console.print("Initializing context system...")
            
            # Create directories
            self.context_dir.mkdir(parents=True, exist_ok=True)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate AST snapshot
            console.print("Generating AST snapshot...")
            ast_generator = ASTGenerator(str(self.project_root))
            snapshot = ast_generator.generate_snapshot()
            save_ast_snapshot(snapshot, self.snapshot_path)
            
            # Create cache file for performance tracking
            self._create_cache_metadata(snapshot)
            
            # Create overview.md (concise system prompt)
            console.print("Creating project overview...")
            self._create_overview(snapshot)
            
            # Initialize history.md
            console.print("Initializing project history...")
            self._initialize_history()
            
            # Create default rules.cline
            console.print("Setting up project rules...")
            self._create_default_rules()
            
            console.print("Context system initialized successfully!")
            self._show_context_summary(snapshot)
            
            return True
            
        except Exception as e:
            console.print(f"Error initializing context: {e}")
            return False
    
    def _create_overview(self, snapshot: Dict):
        """Create concise project overview as system prompt"""
        project_name = self.project_root.name
        total_files = snapshot['summary']['total_files']
        languages = snapshot['summary']['languages']
        main_lang = max(languages.items(), key=lambda x: x[1])[0] if languages else "unknown"
        
        # Get key files and entry points
        key_files = self._identify_key_files(snapshot)
        
        overview_content = f"""# {project_name}

## Project Overview
{main_lang} project with {total_files} files. Main technologies: {', '.join(list(languages.keys())[:3])}.

## Key Files & Structure
{key_files}

## Architecture Pattern
{self._detect_architecture_pattern(snapshot)}

## Development Context
- Entry points: {self._find_entry_points(snapshot)}
- Main modules: {self._get_main_modules(snapshot)}
- Dependencies: {self._get_key_dependencies(snapshot)}

## Current State
- Total lines: {snapshot['summary']['total_lines']:,}
- Last updated: {datetime.now().strftime('%Y-%m-%d')}

---
*This is the essential context for understanding and working with this project.*
"""
        
        with open(self.overview_path, 'w', encoding='utf-8') as f:
            f.write(overview_content)
    
    def _initialize_history(self):
        """Initialize the project history as living documentation"""
        history_content = f"""# {self.project_root.name} - Development History

## Project Timeline

### {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Project Context Initialized
- Context system established
- AST snapshot created
- Project structure analyzed
- Ready for AI-assisted development

---

*This document tracks all interactions, decisions, and changes made to the project.*
*Each AI query and response will be logged here for future reference.*
"""
        
        with open(self.history_path, 'w', encoding='utf-8') as f:
            f.write(history_content)
    
    def _create_default_rules(self):
        """Create default .clinerules file with intelligent defaults"""
        rules_content = f"""# {self.project_root.name} - AI Assistant Rules

## Context Configuration
max_context_files=8
max_file_size=20000
context_priority=main_files,recent_changes,query_relevant

## Code Style & Standards
- Write clean, readable code with meaningful names
- Add comments for complex logic
- Follow existing patterns in the codebase
- Maintain consistent formatting

## Response Guidelines
- Provide concise, actionable answers
- Include code examples when helpful
- Explain reasoning for significant changes
- Ask for clarification when requirements are unclear

## Project-Specific Notes
- Check overview.md for current project context
- Reference history.md for past decisions and changes
- Prioritize existing architecture patterns
- Consider performance and maintainability

## Auto-Update Triggers
- File creation/deletion
- Significant code changes (>50 lines)
- New dependencies added
- Architecture changes
"""
        
        with open(self.rules_path, 'w', encoding='utf-8') as f:
            f.write(rules_content)
    
    def _create_cache_metadata(self, snapshot: Dict):
        """Create cache metadata for performance tracking"""
        cache_metadata = {
            "created_at": datetime.now().isoformat(),
            "files_count": len(snapshot['files']),
            "last_update": datetime.now().isoformat(),
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        cache_file = self.cache_dir / "metadata.json"
        with open(cache_file, 'w') as f:
            json.dump(cache_metadata, f, indent=2)
    
    def log_interaction(self, query: str, response_summary: str, files_involved: List[str] = None):
        """Log every AI interaction to history"""
        try:
            files_involved = files_involved or []
            
            entry = f"""
### {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - AI Interaction

**Query:** {query}

**Response Summary:** {response_summary}

**Files Involved:** {', '.join(files_involved) if files_involved else 'None'}

**Context Used:** Project overview, {len(files_involved)} relevant files

---
"""
            
            # Append to history file
            with open(self.history_path, 'a', encoding='utf-8') as f:
                f.write(entry)
                
            # Auto-update context if needed
            self._check_auto_update()
                
        except Exception as e:
            console.print(f"Warning: Could not log interaction: {e}")
    
    def update_history(self, change_type: str, details: Dict):
        """Add structured entry to project history"""
        try:
            entry = f"""
### {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {change_type}

**Summary:** {details.get('summary', 'No summary provided')}

**Files Changed:** {', '.join(details.get('files', ['N/A']))}

**Impact:** {details.get('impact', 'Not specified')}

{self._format_change_details(details)}

---
"""
            
            # Append to history file
            with open(self.history_path, 'a', encoding='utf-8') as f:
                f.write(entry)
                
            # Update AST snapshot if files changed
            if details.get('files'):
                self._update_ast_cache(details['files'])
                
        except Exception as e:
            console.print(f"Warning: Could not update history: {e}")
    
    def _update_ast_cache(self, changed_files: List[str]):
        """Selectively update AST cache for changed files"""
        try:
            ast_data = load_ast_snapshot(self.snapshot_path)
            if not ast_data:
                return
                
            ast_generator = ASTGenerator(str(self.project_root))
            updated = False
            
            for file_path_str in changed_files:
                # Ensure we have absolute path
                if not os.path.isabs(file_path_str):
                    file_path_obj = self.project_root / file_path_str
                else:
                    file_path_obj = Path(file_path_str)
                
                # Check if file exists and needs update
                if file_path_obj.exists():
                    try:
                        # Get relative path for storage
                        rel_path = str(file_path_obj.relative_to(self.project_root))
                        
                        # Check if update needed
                        if not is_ast_current(file_path_obj, ast_data):
                            # Re-analyze this file
                            ast_data['files'][rel_path] = ast_generator._process_file(file_path_obj)
                            updated = True
                            
                    except ValueError:
                        # File is not in project directory, skip
                        continue
            
            if updated:
                # Rebuild indexes
                ast_data['indexes'] = ast_generator._build_indexes(ast_data)
                ast_data['meta']['updated_at'] = datetime.now().isoformat()
                save_ast_snapshot(ast_data, self.snapshot_path)
                
                # Update cache metadata
                self._update_cache_metadata()
                
        except Exception as e:
            console.print(f"Warning: Could not update AST cache: {e}")
    
    def _update_cache_metadata(self):
        """Update cache performance metadata"""
        cache_file = self.cache_dir / "metadata.json"
        try:
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    metadata = json.load(f)
            else:
                metadata = {"cache_hits": 0, "cache_misses": 0}
                
            metadata["last_update"] = datetime.now().isoformat()
            metadata["cache_hits"] = metadata.get("cache_hits", 0) + 1
            
            with open(cache_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception:
            pass
    
    def _check_auto_update(self):
        """Check if context should be auto-updated"""
        try:
            # Get cache metadata
            cache_file = self.cache_dir / "metadata.json"
            if not cache_file.exists():
                return
                
            with open(cache_file, 'r') as f:
                metadata = json.load(f)
            
            # Check if significant time has passed or many interactions
            last_update = datetime.fromisoformat(metadata.get("last_update", datetime.now().isoformat()))
            hours_since_update = (datetime.now() - last_update).total_seconds() / 3600
            
            # Auto-update if more than 24 hours or many cache misses
            if hours_since_update > 24 or metadata.get("cache_misses", 0) > 10:
                console.print("Auto-updating context...")
                self.initialize_context()
                
        except Exception:
            pass
    
    def load_context(self, query: str = None, max_files: int = None) -> Dict[str, Any]:
        """Load comprehensive context with query-aware prioritization"""
        try:
            # Load base context
            base_context = {
                "overview": self._load_overview(),
                "rules": self._load_rules(),
                "recent_history": self._load_recent_history(),
                "ast_snapshot": load_ast_snapshot(self.snapshot_path),
                "query_focused": {}
            }
            
            # Add query-focused context if provided
            if query and base_context["ast_snapshot"]:
                base_context["query_focused"] = self._get_query_focused_context(
                    query, base_context["ast_snapshot"], max_files
                )
            
            return base_context
            
        except Exception as e:
            console.print(f"Warning: Error loading context: {e}")
            return {"error": str(e)}
    
    def get_context_for_query(self, query: str) -> str:
        """Get formatted context string for AI consumption"""
        context = self.load_context(query)
        
        if "error" in context:
            return f"Context Error: {context['error']}"
        
        # Use the new enhanced formatting
        return self._format_context(context)
    
    def _get_query_focused_context(self, query: str, ast_data: Dict, max_files: int = None) -> Dict:
        """Get context focused on the specific query using AST data"""
        max_files = max_files or self._get_max_context_files()
        query_lower = query.lower()
        keywords = set(query_lower.split())
        
        # Extract explicitly mentioned files from the query
        explicit_files = self._extract_file_mentions(query)
        
        file_scores = []
        explicit_file_data = []
        
        # First, handle explicitly mentioned files
        for file_mention in explicit_files:
            file_found = False
            # Try to find the file in AST data (exact match or partial match)
            for file_path, file_data in ast_data.get('files', {}).items():
                if (file_mention.lower() in file_path.lower() or 
                    file_path.lower().endswith(file_mention.lower()) or
                    file_mention.lower() == file_path.lower()):
                    
                    explicit_file_data.append({
                        "path": file_path,
                        "score": 100,  # Highest priority
                        "content_preview": self._get_file_content(file_path),  # Full content for explicit requests
                        "functions": file_data.get('functions', []),
                        "classes": file_data.get('classes', []),
                        "explicit": True
                    })
                    file_found = True
                    break
            
            # If file not in AST data, try to read it directly
            if not file_found:
                direct_content = self._try_read_file_directly(file_mention)
                if direct_content:
                    explicit_file_data.append({
                        "path": file_mention,
                        "score": 100,
                        "content_preview": direct_content,
                        "functions": [],
                        "classes": [],
                        "explicit": True,
                        "note": "File read directly (not in AST analysis)"
                    })
        
        # Then, do normal relevance scoring for additional context
        for file_path, file_data in ast_data.get('files', {}).items():
            # Skip if already included as explicit file
            if any(explicit['path'] == file_path for explicit in explicit_file_data):
                continue
                
            score = 0
            
            # Score based on filename relevance
            if any(keyword in file_path.lower() for keyword in keywords):
                score += 10
            
            # Score based on functions/classes matching query
            for func in file_data.get('functions', []):
                func_name = func.get('name', func) if isinstance(func, dict) else func
                if any(keyword in func_name.lower() for keyword in keywords):
                    score += 5
                    
            for cls in file_data.get('classes', []):
                cls_name = cls.get('name', cls) if isinstance(cls, dict) else cls
                if any(keyword in cls_name.lower() for keyword in keywords):
                    score += 5
            
            # Score based on imports
            for imp in file_data.get('imports', []):
                imp_name = imp.get('name', imp) if isinstance(imp, dict) else imp
                if any(keyword in imp_name.lower() for keyword in keywords):
                    score += 3
            
            if score > 0:
                file_scores.append((file_path, score, file_data))
        
        # Sort by score and take top files (excluding space used by explicit files)
        file_scores.sort(key=lambda x: x[1], reverse=True)
        remaining_slots = max(0, max_files - len(explicit_file_data))
        relevant_files = file_scores[:remaining_slots]
        
        # Combine explicit files with relevant files
        all_files = explicit_file_data + [
            {
                "path": path,
                "score": score,
                "content_preview": self._get_file_preview(path),
                "functions": data.get('functions', [])[:5],  # Top 5 functions
                "classes": data.get('classes', [])[:3],      # Top 3 classes
                "explicit": False
            }
            for path, score, data in relevant_files
        ]
        
        return {
            "relevant_files": all_files,
            "query_keywords": list(keywords),
            "total_relevant": len(file_scores),
            "explicit_files": len(explicit_file_data),
            "explicit_file_names": [f["path"] for f in explicit_file_data]
        }
    
    def _extract_file_mentions(self, query: str) -> List[str]:
        """Extract explicit file mentions from a query"""
        import re
        
        file_mentions = []
        words = query.split()
        
        # Pattern 1: Direct file extensions
        file_extensions = [
            '.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.java', '.cpp', '.c', '.h', '.hpp',
            '.php', '.rb', '.swift', '.kt', '.scala', '.dart', '.lua', '.md', '.txt', '.json', 
            '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.xml', '.html', '.css', '.scss'
        ]
        
        for word in words:
            # Remove common punctuation
            clean_word = word.strip('.,;:!?"()[]{}')
            
            # Check if word has file extension
            if any(clean_word.lower().endswith(ext) for ext in file_extensions):
                file_mentions.append(clean_word)
            
            # Check for file paths (containing forward slashes)
            elif '/' in clean_word and any(ext in clean_word.lower() for ext in file_extensions):
                file_mentions.append(clean_word)
        
        # Pattern 2: Common file name patterns without extensions
        common_filenames = [
            'readme', 'makefile', 'dockerfile', 'requirements', 'package', 'setup',
            'config', 'settings', 'main', 'index', 'app', 'server', '__init__'
        ]
        
        for word in words:
            clean_word = word.strip('.,;:!?"()[]{}').lower()
            if clean_word in common_filenames:
                # Try to find the actual file with common extensions
                potential_files = [
                    f"{clean_word}.py", f"{clean_word}.js", f"{clean_word}.ts", 
                    f"{clean_word}.md", f"{clean_word}.txt", f"{clean_word}.json",
                    clean_word  # Some files have no extension
                ]
                file_mentions.extend(potential_files)
        
        # Pattern 3: Quoted file names
        quoted_pattern = r'["\']([^"\']*(?:\.[a-zA-Z0-9]+)?)["\']'
        quoted_matches = re.findall(quoted_pattern, query)
        for match in quoted_matches:
            if any(ext in match.lower() for ext in file_extensions) or '/' in match:
                file_mentions.append(match)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_mentions = []
        for mention in file_mentions:
            if mention.lower() not in seen:
                seen.add(mention.lower())
                unique_mentions.append(mention)
        
        return unique_mentions
    
    def _get_file_content(self, file_path: str, max_lines: int = 100) -> str:
        """Get full or partial content of a file for explicit requests"""
        try:
            full_path = self.project_root / file_path
            if not full_path.exists():
                return f"File {file_path} not found"
            
            # Check file size
            file_size = full_path.stat().st_size
            if file_size > 50000:  # 50KB limit
                return f"File {file_path} is too large ({file_size} bytes). Showing preview:\n\n" + self._get_file_preview(file_path, lines=20)
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
                if len(lines) <= max_lines:
                    return ''.join(lines)
                else:
                    # Show first part + indication of truncation
                    content = ''.join(lines[:max_lines])
                    remaining = len(lines) - max_lines
                    content += f"\n\n... (showing first {max_lines} lines, {remaining} more lines available)"
                    return content
                    
        except Exception as e:
            return f"Error reading {file_path}: {str(e)}"
    
    def _try_read_file_directly(self, file_mention: str) -> Optional[str]:
        """Try to read a file directly from the project directory"""
        try:
            # Try different variations of the file mention
            possible_paths = [
                file_mention,
                f"./{file_mention}",
                f"src/{file_mention}",
                f"lib/{file_mention}",
                f"app/{file_mention}",
            ]
            
            # If no extension, try common ones
            if '.' not in file_mention:
                base_paths = possible_paths.copy()
                possible_paths = []
                for base in base_paths:
                    possible_paths.extend([
                        f"{base}.py", f"{base}.js", f"{base}.ts", 
                        f"{base}.md", f"{base}.txt", f"{base}.json"
                    ])
            
            for path_attempt in possible_paths:
                full_path = self.project_root / path_attempt
                if full_path.exists() and full_path.is_file():
                    return self._get_file_content(path_attempt)
            
            return None
            
        except Exception:
            return None
    
    # Helper methods for overview generation
    def _identify_key_files(self, snapshot: Dict) -> str:
        """Identify and list key project files"""
        files = snapshot.get('files', {})
        key_files = []
        
        # Look for common entry points and important files
        important_patterns = [
            'main.py', 'app.py', 'index.js', 'index.ts', 'server.py',
            'manage.py', 'setup.py', 'requirements.txt', 'package.json',
            'README.md', 'Dockerfile', 'Makefile'
        ]
        
        for pattern in important_patterns:
            for file_path in files.keys():
                if pattern.lower() in file_path.lower():
                    key_files.append(f"- {file_path}")
                    break
        
        return '\n'.join(key_files) if key_files else "- Standard project structure"
    
    def _detect_architecture_pattern(self, snapshot: Dict) -> str:
        """Detect the project's architecture pattern"""
        files = snapshot.get('files', {})
        file_paths = list(files.keys())
        
        if any('controller' in path.lower() for path in file_paths):
            return "MVC/Controller-based architecture"
        elif any('service' in path.lower() for path in file_paths):
            return "Service-oriented architecture"
        elif any('api' in path.lower() for path in file_paths):
            return "API-based architecture"
        elif any('component' in path.lower() for path in file_paths):
            return "Component-based architecture"
        else:
            return "Modular architecture"
    
    def _find_entry_points(self, snapshot: Dict) -> str:
        """Find main entry points"""
        files = snapshot.get('files', {})
        entry_points = []
        
        for file_path, file_data in files.items():
            if 'main' in file_path.lower() or file_path.endswith('main.py'):
                entry_points.append(file_path)
        
        return ', '.join(entry_points) if entry_points else "Not clearly defined"
    
    def _get_main_modules(self, snapshot: Dict) -> str:
        """Get main modules/directories"""
        files = snapshot.get('files', {})
        dirs = set()
        
        for file_path in files.keys():
            parts = file_path.split('/')
            if len(parts) > 1:
                dirs.add(parts[0])
        
        return ', '.join(sorted(list(dirs))[:5])
    
    def _get_key_dependencies(self, snapshot: Dict) -> str:
        """Extract key dependencies"""
        files = snapshot.get('files', {})
        dependencies = set()
        
        for file_data in files.values():
            for imp in file_data.get('imports', []):
                imp_name = imp.get('name', imp) if isinstance(imp, dict) else imp
                if imp_name and not imp_name.startswith('.'):
                    # Extract top-level package name
                    dep = imp_name.split('.')[0]
                    if dep not in ['os', 'sys', 'json', 'datetime', 'pathlib']:  # Skip stdlib
                        dependencies.add(dep)
        
        return ', '.join(sorted(list(dependencies))[:8])
    
    # Existing helper methods with minor improvements
    def _load_overview(self) -> str:
        """Load project overview content"""
        try:
            if self.overview_path.exists():
                return self.overview_path.read_text(encoding='utf-8')
        except Exception:
            pass
        return "Project overview not available"
    
    def _load_rules(self) -> Dict[str, str]:
        """Load and parse .clinerules file"""
        rules = {}
        try:
            if self.rules_path.exists():
                content = self.rules_path.read_text(encoding='utf-8')
                for line in content.split('\n'):
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.split('=', 1)
                        rules[key.strip()] = value.strip()
        except Exception:
            pass
        return rules
    
    def _load_recent_history(self, days: int = 7) -> str:
        """Load recent project history"""
        try:
            if self.history_path.exists():
                content = self.history_path.read_text(encoding='utf-8')
                # Return last 3000 characters for recent context
                return content[-3000:] if len(content) > 3000 else content
        except Exception:
            pass
        return "Project history not available"
    
    def _get_max_context_files(self) -> int:
        """Get maximum context files from rules"""
        rules = self._load_rules()
        try:
            return int(rules.get('max_context_files', '8'))
        except (ValueError, TypeError):
            return 8
    
    def _get_file_preview(self, file_path: str, lines: int = 10) -> str:
        """Get preview of file content"""
        try:
            full_path = self.project_root / file_path
            if full_path.exists() and full_path.stat().st_size < 20000:  # Preview larger files
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    preview_lines = [f.readline().strip() for _ in range(lines)]
                    return "\n".join(line for line in preview_lines if line)
        except Exception:
            pass
        return "Preview not available"
    
    def _format_change_details(self, details: Dict) -> str:
        """Format change details for history entry"""
        formatted = []
        
        if details.get('description'):
            formatted.append(f"**Details:** {details['description']}")
        
        if details.get('diff'):
            formatted.append("**Changes:**")
            formatted.append("```diff")
            formatted.append(details['diff'])
            formatted.append("```")
        
        return "\n".join(formatted)
    
    def _show_context_summary(self, snapshot: Dict):
        """Show a summary of the created context"""
        console.print("\nContext Summary:")
        console.print(f"• Files analyzed: {snapshot['summary']['total_files']}")
        console.print(f"• Total lines: {snapshot['summary']['total_lines']:,}")
        console.print(f"• Languages: {', '.join(snapshot['summary']['languages'].keys())}")
        console.print(f"• Classes indexed: {len(snapshot['indexes']['class_locations'])}")
        console.print(f"• Functions indexed: {len(snapshot['indexes']['function_locations'])}")
        console.print(f"• Import relationships: {len(snapshot['indexes']['import_graph'])}")
        
        console.print(f"\nContext files created:")
        console.print(f"• {self.snapshot_path.relative_to(self.project_root)}")
        console.print(f"• {self.overview_path.relative_to(self.project_root)}")
        console.print(f"• {self.history_path.relative_to(self.project_root)}")
        console.print(f"• {self.rules_path.relative_to(self.project_root)}")
        console.print(f"• Cache: {self.cache_dir.relative_to(self.project_root)}")
    
    def _format_context(self, context: Dict) -> str:
        """Format context for LLM consumption"""
        formatted = []
        
        # Project overview
        overview_file = self.context_dir / "overview.md"
        if overview_file.exists():
            formatted.append("# Project Overview\n")
            with open(overview_file, 'r', encoding='utf-8') as f:
                formatted.append(f.read())
            formatted.append("\n" + "="*50 + "\n")
        
        # Relevant files with explicit file handling
        relevant_files = context.get('query_focused', {}).get('relevant_files', [])
        if relevant_files:
            # Separate explicit files from regular files
            explicit_files = [f for f in relevant_files if f.get('explicit', False)]
            regular_files = [f for f in relevant_files if not f.get('explicit', False)]
            
            # Show explicitly requested files first with full content
            if explicit_files:
                formatted.append("# Explicitly Requested Files\n")
                for file_info in explicit_files:
                    formatted.append(f"## File: {file_info['path']}\n")
                    if file_info.get('note'):
                        formatted.append(f"*{file_info['note']}*\n\n")
                    
                    # Include full content for explicit requests
                    content = file_info.get('content_preview', '')
                    if content:
                        formatted.append(f"```{self._get_file_language(file_info['path'])}\n")
                        formatted.append(content)
                        if not content.endswith('\n'):
                            formatted.append('\n')
                        formatted.append("```\n\n")
                    
                    # Add function/class info if available
                    if file_info.get('functions'):
                        formatted.append("**Functions:**\n")
                        for func in file_info.get('functions', [])[:10]:  # Show more for explicit files
                            if isinstance(func, dict):
                                formatted.append(f"- {func.get('name', 'Unknown')} (line {func.get('line', '?')})\n")
                            else:
                                formatted.append(f"- {func}\n")
                        formatted.append("\n")
                    
                    if file_info.get('classes'):
                        formatted.append("**Classes:**\n")
                        for cls in file_info.get('classes', [])[:10]:  # Show more for explicit files
                            if isinstance(cls, dict):
                                formatted.append(f"- {cls.get('name', 'Unknown')} (line {cls.get('line', '?')})\n")
                            else:
                                formatted.append(f"- {cls}\n")
                        formatted.append("\n")
                    
                    formatted.append("-" * 40 + "\n\n")
            
            # Then show additional context files with previews
            if regular_files:
                formatted.append("# Additional Context Files\n")
                for file_info in regular_files:
                    formatted.append(f"## {file_info['path']} (relevance: {file_info['score']})\n")
                    
                    preview = file_info.get('content_preview', '')
                    if preview:
                        formatted.append(f"```{self._get_file_language(file_info['path'])}\n")
                        formatted.append(preview)
                        if not preview.endswith('\n'):
                            formatted.append('\n')
                        formatted.append("```\n")
                    
                    if file_info.get('functions'):
                        formatted.append("**Key Functions:** ")
                        func_names = []
                        for func in file_info.get('functions', [])[:5]:
                            if isinstance(func, dict):
                                func_names.append(func.get('name', 'Unknown'))
                            else:
                                func_names.append(str(func))
                        formatted.append(", ".join(func_names) + "\n")
                    
                    if file_info.get('classes'):
                        formatted.append("**Key Classes:** ")
                        class_names = []
                        for cls in file_info.get('classes', [])[:3]:
                            if isinstance(cls, dict):
                                class_names.append(cls.get('name', 'Unknown'))
                            else:
                                class_names.append(str(cls))
                        formatted.append(", ".join(class_names) + "\n")
                    
                    formatted.append("\n")
            
            # Add context summary
            formatted.append("# Context Summary\n")
            query_focused = context.get('query_focused', {})
            if query_focused.get('explicit_files', 0) > 0:
                formatted.append(f"- **Explicit files included:** {query_focused.get('explicit_files', 0)} ({', '.join(query_focused.get('explicit_file_names', []))})\n")
            formatted.append(f"- **Additional context files:** {len(regular_files)}\n")
            formatted.append(f"- **Query keywords:** {', '.join(query_focused.get('query_keywords', []))}\n")
            formatted.append(f"- **Total relevant files found:** {query_focused.get('total_relevant', 0)}\n\n")
        
        # Recent history for additional context
        history_file = self.context_dir / "history.md"
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_content = f.read()
                    # Include only the most recent entries (last 1000 characters)
                    if len(history_content) > 1000:
                        recent_history = "..." + history_content[-1000:]
                    else:
                        recent_history = history_content
                    
                    if recent_history.strip():
                        formatted.append("# Recent Development History\n")
                        formatted.append(recent_history)
                        formatted.append("\n")
            except Exception:
                pass  # Skip if history cannot be read
        
        return "\n".join(formatted)
    
    def _get_file_language(self, file_path: str) -> str:
        """Get language identifier for syntax highlighting"""
        ext = file_path.lower().split('.')[-1] if '.' in file_path else ''
        
        language_map = {
            'py': 'python', 'js': 'javascript', 'ts': 'typescript', 'jsx': 'jsx', 'tsx': 'tsx',
            'go': 'go', 'rs': 'rust', 'java': 'java', 'cpp': 'cpp', 'c': 'c', 'h': 'c',
            'hpp': 'cpp', 'php': 'php', 'rb': 'ruby', 'swift': 'swift', 'kt': 'kotlin',
            'scala': 'scala', 'dart': 'dart', 'lua': 'lua', 'md': 'markdown', 'txt': 'text',
            'json': 'json', 'yaml': 'yaml', 'yml': 'yaml', 'toml': 'toml', 'ini': 'ini',
            'xml': 'xml', 'html': 'html', 'css': 'css', 'scss': 'scss', 'sql': 'sql',
            'sh': 'bash', 'bash': 'bash', 'zsh': 'zsh', 'fish': 'fish'
        }
        
        return language_map.get(ext, 'text') 