# context_manager.py

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.markdown import Markdown

from ast_generator import ASTGenerator, save_ast_snapshot, load_ast_snapshot, is_ast_current

console = Console()

class ContextManager:
    """Advanced context management using the cline method for intelligent codebase indexing"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.context_dir = self.project_root / ".mycode" / "context"
        self.cache_dir = self.project_root / ".mycode" / "cache"
        
        # Context file paths
        self.snapshot_path = self.context_dir / "snapshot.json"
        self.overview_path = self.context_dir / "overview.md"
        self.history_path = self.context_dir / "history.md"
        self.rules_path = self.context_dir / "rules.cline"
        
    def initialize_context(self) -> bool:
        """Initialize the complete context system for a project"""
        try:
            console.print("🧠 Initializing intelligent context system...")
            
            # Create directories
            self.context_dir.mkdir(parents=True, exist_ok=True)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate AST snapshot
            console.print("📊 Generating AST snapshot...")
            ast_generator = ASTGenerator(str(self.project_root))
            snapshot = ast_generator.generate_snapshot()
            save_ast_snapshot(snapshot, self.snapshot_path)
            
            # Create cache file for performance tracking
            self._create_cache_metadata(snapshot)
            
            # Create overview.md (concise system prompt)
            console.print("📝 Creating project overview...")
            self._create_overview(snapshot)
            
            # Initialize history.md
            console.print("📚 Initializing project history...")
            self._initialize_history()
            
            # Create default rules.cline
            console.print("📋 Setting up project rules...")
            self._create_default_rules()
            
            console.print("✅ Context system initialized successfully!")
            self._show_context_summary(snapshot)
            
            return True
            
        except Exception as e:
            console.print(f"❌ Error initializing context: {e}")
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
                console.print("🔄 Auto-updating context...")
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
        
        # Format context for AI
        formatted_context = []
        
        # Add project overview (this serves as system prompt)
        if context.get("overview"):
            formatted_context.append(context["overview"])
            formatted_context.append("")
        
        # Add relevant rules
        rules = context.get("rules", {})
        if rules:
            formatted_context.append("## Assistant Guidelines")
            for key, value in rules.items():
                if not key.startswith('#'):
                    formatted_context.append(f"- {key}: {value}")
            formatted_context.append("")
        
        # Add query-focused files
        if context.get("query_focused", {}).get("relevant_files"):
            formatted_context.append("## Relevant Files")
            for file_info in context["query_focused"]["relevant_files"][:3]:  # Top 3
                formatted_context.append(f"### {file_info['path']}")
                if file_info.get('content_preview'):
                    formatted_context.append("```")
                    formatted_context.append(file_info['content_preview'])
                    formatted_context.append("```")
                formatted_context.append("")
        
        # Add recent relevant history
        if context.get("recent_history"):
            formatted_context.append("## Recent Development Context")
            # Get last 2 interactions
            history_lines = context["recent_history"].split('\n')
            recent_entries = []
            entry_count = 0
            
            for line in reversed(history_lines):
                if line.startswith("###") and "AI Interaction" in line:
                    entry_count += 1
                    if entry_count > 2:  # Only last 2 interactions
                        break
                if entry_count > 0:
                    recent_entries.insert(0, line)
            
            if recent_entries:
                formatted_context.extend(recent_entries[:15])  # Limit length
        
        return "\n".join(formatted_context)
    
    def _get_query_focused_context(self, query: str, ast_data: Dict, max_files: int = None) -> Dict:
        """Get context focused on the specific query using AST data"""
        max_files = max_files or self._get_max_context_files()
        query_lower = query.lower()
        keywords = set(query_lower.split())
        
        file_scores = []
        
        for file_path, file_data in ast_data.get('files', {}).items():
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
        
        # Sort by score and take top files
        file_scores.sort(key=lambda x: x[1], reverse=True)
        relevant_files = file_scores[:max_files]
        
        return {
            "relevant_files": [
                {
                    "path": path,
                    "score": score,
                    "content_preview": self._get_file_preview(path),
                    "functions": data.get('functions', [])[:5],  # Top 5 functions
                    "classes": data.get('classes', [])[:3],      # Top 3 classes
                }
                for path, score, data in relevant_files
            ],
            "query_keywords": list(keywords),
            "total_relevant": len(file_scores)
        }
    
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
        console.print("\n📊 Context Summary:")
        console.print(f"• Files analyzed: {snapshot['summary']['total_files']}")
        console.print(f"• Total lines: {snapshot['summary']['total_lines']:,}")
        console.print(f"• Languages: {', '.join(snapshot['summary']['languages'].keys())}")
        console.print(f"• Classes indexed: {len(snapshot['indexes']['class_locations'])}")
        console.print(f"• Functions indexed: {len(snapshot['indexes']['function_locations'])}")
        console.print(f"• Import relationships: {len(snapshot['indexes']['import_graph'])}")
        
        console.print(f"\n📁 Context files created:")
        console.print(f"• {self.snapshot_path.relative_to(self.project_root)}")
        console.print(f"• {self.overview_path.relative_to(self.project_root)}")
        console.print(f"• {self.history_path.relative_to(self.project_root)}")
        console.print(f"• {self.rules_path.relative_to(self.project_root)}")
        console.print(f"• Cache: {self.cache_dir.relative_to(self.project_root)}") 