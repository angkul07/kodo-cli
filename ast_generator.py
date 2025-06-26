# ast_generator.py

import ast
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set
import fnmatch
import tree_sitter_language_pack
from tree_sitter_language_pack import get_language, get_parser
TREE_SITTER_AVAILABLE = True

# --- Enhanced tree-sitter support ---
# try:
#     from tree_sitter_language_pack import get_language, get_parser
#     TREE_SITTER_AVAILABLE = True
# except ImportError:
#     print("Warning: tree-sitter-language-pack not found. Multi-language support will be limited.")
#     get_language = None
#     get_parser = None
#     TREE_SITTER_AVAILABLE = False

class PythonAnalyzer(ast.NodeVisitor):
    """Extracts key information from a Python AST."""
    def __init__(self):
        self.imports = []
        self.classes = []
        self.functions = []
        self.variables = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append({
                "name": alias.name,
                "alias": alias.asname,
                "line": node.lineno
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            for alias in node.names:
                self.imports.append({
                    "name": f"{node.module}.{alias.name}",
                    "from": node.module,
                    "import": alias.name,
                    "alias": alias.asname,
                    "line": node.lineno
                })
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.classes.append({
            "name": node.name,
            "start_line": node.lineno,
            "end_line": node.end_lineno,
            "bases": [self._get_name(base) for base in node.bases],
            "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
        })
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.functions.append({
            "name": node.name,
            "start_line": node.lineno,
            "end_line": node.end_lineno,
            "args": [arg.arg for arg in node.args.args],
            "decorators": [self._get_name(dec) for dec in node.decorator_list]
        })
        self.generic_visit(node)

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.variables.append({
                    "name": target.id,
                    "line": node.lineno
                })
        self.generic_visit(node)

    def _get_name(self, node):
        """Extract name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        return "unknown"


class TreeSitterAnalyzer:
    """Enhanced Tree-sitter analyzer for multiple languages"""
    
    def __init__(self, language: str):
        self.language = language
        self.parser = get_parser(language) if TREE_SITTER_AVAILABLE else None
        
    def analyze(self, filepath: Path) -> Dict:
        """Analyze file using tree-sitter"""
        if not self.parser:
            return {"imports": [], "classes": [], "functions": [], "variables": []}
            
        try:
            source_bytes = filepath.read_bytes()
            tree = self.parser.parse(source_bytes)
            
            return {
                "imports": self._extract_imports(tree.root_node, source_bytes),
                "classes": self._extract_classes(tree.root_node, source_bytes),
                "functions": self._extract_functions(tree.root_node, source_bytes),
                "variables": self._extract_variables(tree.root_node, source_bytes)
            }
        except Exception as e:
            return {"error": str(e), "imports": [], "classes": [], "functions": [], "variables": []}

    def _extract_imports(self, node, source_bytes: bytes) -> List[Dict]:
        """Extract import statements"""
        imports = []
        
        # Language-specific import patterns
        import_queries = {
            'javascript': ['import_statement', 'import_clause'],
            'typescript': ['import_statement', 'import_clause'],
            'go': ['import_declaration', 'import_spec'],
            'java': ['import_declaration'],
            'rust': ['use_declaration'],
            'c': ['preproc_include'],
            'cpp': ['preproc_include']
        }
        
        query_types = import_queries.get(self.language, ['import_statement'])
        for query_type in query_types:
            for child in self._find_nodes_by_type(node, query_type):
                imports.append({
                    "name": self._get_node_text(child, source_bytes),
                    "line": child.start_point[0] + 1
                })
        
        return imports

    def _extract_classes(self, node, source_bytes: bytes) -> List[Dict]:
        """Extract class definitions"""
        classes = []
        
        class_queries = {
            'javascript': ['class_declaration'],
            'typescript': ['class_declaration'],
            'go': ['type_declaration'],
            'java': ['class_declaration'],
            'rust': ['struct_item', 'enum_item'],
            'c': ['struct_specifier'],
            'cpp': ['class_specifier', 'struct_specifier']
        }
        
        query_types = class_queries.get(self.language, ['class_declaration'])
        for query_type in query_types:
            for child in self._find_nodes_by_type(node, query_type):
                name_node = self._find_first_child_by_type(child, 'identifier')
                if name_node:
                    classes.append({
                        "name": self._get_node_text(name_node, source_bytes),
                        "start_line": child.start_point[0] + 1,
                        "end_line": child.end_point[0] + 1,
                        "type": query_type
                    })
        
        return classes

    def _extract_functions(self, node, source_bytes: bytes) -> List[Dict]:
        """Extract function definitions"""
        functions = []
        
        function_queries = {
            'javascript': ['function_declaration', 'method_definition', 'arrow_function'],
            'typescript': ['function_declaration', 'method_definition', 'arrow_function'],
            'go': ['function_declaration', 'method_declaration'],
            'java': ['method_declaration'],
            'rust': ['function_item'],
            'c': ['function_definition'],
            'cpp': ['function_definition']
        }
        
        query_types = function_queries.get(self.language, ['function_declaration'])
        for query_type in query_types:
            for child in self._find_nodes_by_type(node, query_type):
                name_node = self._find_first_child_by_type(child, 'identifier')
                if name_node:
                    functions.append({
                        "name": self._get_node_text(name_node, source_bytes),
                        "start_line": child.start_point[0] + 1,
                        "end_line": child.end_point[0] + 1,
                        "type": query_type
                    })
        
        return functions

    def _extract_variables(self, node, source_bytes: bytes) -> List[Dict]:
        """Extract variable declarations"""
        variables = []
        
        var_queries = {
            'javascript': ['variable_declaration', 'lexical_declaration'],
            'typescript': ['variable_declaration', 'lexical_declaration'],
            'go': ['var_declaration'],
            'java': ['variable_declarator'],
            'rust': ['let_declaration'],
            'c': ['declaration'],
            'cpp': ['declaration']
        }
        
        query_types = var_queries.get(self.language, ['variable_declaration'])
        for query_type in query_types:
            for child in self._find_nodes_by_type(node, query_type):
                name_node = self._find_first_child_by_type(child, 'identifier')
                if name_node:
                    variables.append({
                        "name": self._get_node_text(name_node, source_bytes),
                        "line": child.start_point[0] + 1
                    })
        
        return variables

    def _find_nodes_by_type(self, node, node_type: str):
        """Find all nodes of a specific type"""
        if node.type == node_type:
            yield node
        for child in node.children:
            yield from self._find_nodes_by_type(child, node_type)

    def _find_first_child_by_type(self, node, node_type: str):
        """Find first child node of a specific type"""
        for child in node.children:
            if child.type == node_type:
                return child
        return None

    def _get_node_text(self, node, source_bytes: bytes) -> str:
        """Get text content of a node"""
        return source_bytes[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')


class ASTGenerator:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path).absolute()
        
        # Enhanced ignore patterns including virtual environments
        self.ignore_patterns = [
            # Version control
            '**/.git/**', '**/.svn/**', '**/.hg/**',
            
            # Python virtual environments
            '**/*venv*/**', '**/.venv/**', '**/venv/**', '**/env/**',
            '**/virtualenv*/**', '**/VIRTUAL_ENV/**', '**/.virtualenv/**',
            
            # UV virtual environments (new Python package manager)
            '**/.uv/**', '**/uv.lock', '**/uv-cache/**',
            
            # Node.js
            '**/node_modules/**', '**/npm-debug.log*', '**/yarn-debug.log*',
            '**/yarn-error.log*', '**/.npm/**', '**/.yarn/**',
            
            # Compiled/build outputs
            '**/__pycache__/**', '**/*.pyc', '**/*.pyo', '**/*.pyd',
            '**/dist/**', '**/build/**', '**/target/**', '**/out/**',
            '**/*.egg-info/**', '**/.tox/**',
            
            # IDEs and editors
            '**/.vscode/**', '**/.idea/**', '**/*.swp', '**/*.swo',
            '**/.DS_Store', '**/Thumbs.db',
            
            # Dependencies and packages
            '**/vendor/**', '**/deps/**', '**/lib/**',
            '**/packages/**', '**/bower_components/**',
            
            # Logs and temporary files
            '**/logs/**', '**/*.log', '**/tmp/**', '**/temp/**',
            '**/cache/**', '**/.cache/**',
            
            # Our own context files
            '**/.mycode/**'
        ]
        
        # Enhanced language support
        self.language_map = {
            # Python
            '.py': 'python', '.pyi': 'python', '.pyx': 'python',
            
            # JavaScript/TypeScript
            '.js': 'javascript', '.jsx': 'javascript', '.mjs': 'javascript',
            '.ts': 'typescript', '.tsx': 'typescript',
            
            # Systems programming
            '.go': 'go', '.rs': 'rust', '.c': 'c', '.cpp': 'cpp',
            '.cc': 'cpp', '.cxx': 'cpp', '.h': 'c', '.hpp': 'cpp',
            
            # JVM languages
            '.java': 'java', '.kt': 'kotlin', '.scala': 'scala',
            
            # Web
            '.html': 'html', '.css': 'css', '.scss': 'scss',
            '.vue': 'vue', '.svelte': 'svelte',
            
            # Shell/Config
            '.sh': 'bash', '.bash': 'bash', '.zsh': 'bash',
            '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml',
            '.toml': 'toml', '.ini': 'ini',
            
            # Other
            '.php': 'php', '.rb': 'ruby', '.swift': 'swift',
            '.dart': 'dart', '.lua': 'lua'
        }

    def _should_ignore(self, path: Path) -> bool:
        """Check if path matches any ignore pattern"""
        try:
            rel_path_str = str(path.relative_to(self.root_path).as_posix())
            
            # Check patterns
            for pattern in self.ignore_patterns:
                if fnmatch.fnmatch(rel_path_str, pattern):
                    return True
                    
            # Additional checks for hidden files/dirs at any level
            if any(part.startswith('.') and part not in {'.', '..'} 
                   for part in path.parts if not part.startswith('.mycode')):
                return True
                
            return False
        except ValueError:
            return True

    def generate_snapshot(self) -> Dict:
        """Generate a complete snapshot of the project's codebase."""
        snapshot = {
            'meta': {
                'version': '2.0',
                'created_at': datetime.now().isoformat(),
                'project_root': str(self.root_path),
                'tree_sitter_available': TREE_SITTER_AVAILABLE,
                'languages_supported': list(self.language_map.keys())
            },
            'files': {},
            'summary': {
                'total_files': 0,
                'total_lines': 0,
                'languages': {},
                'largest_files': []
            }
        }

        file_sizes = []
        total_lines = 0
        language_counts = {}

        for filepath in self._walk_code_files():
            rel_path = str(filepath.relative_to(self.root_path))
            file_data = self._process_file(filepath)
            snapshot['files'][rel_path] = file_data
            
            # Collect summary statistics
            file_size = file_data.get('size', 0)
            file_sizes.append((rel_path, file_size))
            
            if 'line_count' in file_data:
                total_lines += file_data['line_count']
                
            lang = file_data.get('language', 'unknown')
            language_counts[lang] = language_counts.get(lang, 0) + 1

        # Build summary
        snapshot['summary']['total_files'] = len(snapshot['files'])
        snapshot['summary']['total_lines'] = total_lines
        snapshot['summary']['languages'] = language_counts
        snapshot['summary']['largest_files'] = sorted(file_sizes, key=lambda x: x[1], reverse=True)[:10]
        
        # Build indexes
        snapshot['indexes'] = self._build_indexes(snapshot)
        return snapshot

    def _walk_code_files(self):
        """Yield all non-ignored code files that have a parser."""
        for root, dirs, files in os.walk(self.root_path):
            root_path = Path(root)
            
            # Prune ignored directories
            dirs[:] = [d for d in dirs if not self._should_ignore(root_path / d)]
            
            if self._should_ignore(root_path):
                continue
                
            for file in files:
                filepath = root_path / file
                if (filepath.suffix in self.language_map and 
                    not self._should_ignore(filepath) and
                    filepath.is_file()):
                    yield filepath

    def _process_file(self, filepath: Path) -> Dict:
        """Process a single file with the appropriate parser."""
        file_data = {
            'mtime': filepath.stat().st_mtime,
            'size': filepath.stat().st_size,
            'language': self.language_map.get(filepath.suffix, 'unknown'),
            'error': None,
            'line_count': 0
        }
        
        try:
            # Count lines
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                file_data['line_count'] = sum(1 for _ in f)
                
            # Parse based on language
            if filepath.suffix == '.py':
                file_data.update(self._parse_python(filepath))
            elif TREE_SITTER_AVAILABLE and filepath.suffix in self.language_map:
                lang = self.language_map[filepath.suffix]
                analyzer = TreeSitterAnalyzer(lang)
                file_data.update(analyzer.analyze(filepath))
            else:
                # Basic fallback for unsupported languages
                file_data.update({
                    'imports': [],
                    'classes': [],
                    'functions': [],
                    'variables': []
                })
                
        except Exception as e:
            file_data['error'] = str(e)
            file_data.update({
                'imports': [],
                'classes': [],
                'functions': [],
                'variables': []
            })
            
        return file_data

    def _parse_python(self, filepath: Path) -> Dict:
        """Python parser using native AST."""
        try:
            source = filepath.read_text(encoding='utf-8')
            tree = ast.parse(source)
            analyzer = PythonAnalyzer()
            analyzer.visit(tree)
            return {
                'imports': analyzer.imports,
                'classes': analyzer.classes,
                'functions': analyzer.functions,
                'variables': analyzer.variables
            }
        except Exception as e:
            return {
                'error': f"Python AST parsing failed: {str(e)}",
                'imports': [],
                'classes': [],
                'functions': [],
                'variables': []
            }

    def _build_indexes(self, snapshot: Dict) -> Dict:
        """Build comprehensive cross-reference indexes from the file data."""
        import_graph = {}
        class_locations = {}
        function_locations = {}
        variable_locations = {}
        dependency_map = {}
        
        for path, data in snapshot['files'].items():
            if data.get('error'):
                continue
                
            # Build import graph
            if data.get('imports'):
                import_graph[path] = [imp.get('name', imp) if isinstance(imp, dict) else imp 
                                    for imp in data['imports']]

            # Build location maps
            for class_info in data.get('classes', []):
                class_name = class_info.get('name') if isinstance(class_info, dict) else class_info
                if class_name:
                    class_locations[class_name] = path

            for func_info in data.get('functions', []):
                func_name = func_info.get('name') if isinstance(func_info, dict) else func_info
                if func_name:
                    function_locations[func_name] = path

            for var_info in data.get('variables', []):
                var_name = var_info.get('name') if isinstance(var_info, dict) else var_info
                if var_name:
                    variable_locations[var_name] = path

        # Build dependency map (reverse of import graph)
        for file, imports in import_graph.items():
            for imp in imports:
                if imp not in dependency_map:
                    dependency_map[imp] = []
                dependency_map[imp].append(file)

        return {
            "import_graph": import_graph,
            "dependency_map": dependency_map,
            "class_locations": class_locations,
            "function_locations": function_locations,
            "variable_locations": variable_locations,
            "file_relationships": self._analyze_file_relationships(import_graph)
        }

    def _analyze_file_relationships(self, import_graph: Dict) -> Dict:
        """Analyze relationships between files."""
        relationships = {}
        
        for file, imports in import_graph.items():
            relationships[file] = {
                "imports_count": len(imports),
                "imported_by": [],
                "related_files": []
            }
            
        # Find files that import each other
        for file, imports in import_graph.items():
            for other_file, other_imports in import_graph.items():
                if file != other_file:
                    # Check if other_file imports from file
                    if any(imp.startswith(file.replace('/', '.').replace('.py', '')) for imp in other_imports):
                        relationships[file]["imported_by"].append(other_file)
                        
        return relationships


def save_ast_snapshot(snapshot: Dict, path: Path):
    """Saves the AST snapshot to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(snapshot, f, indent=2)


def load_ast_snapshot(path: Path) -> Optional[Dict]:
    """Load AST snapshot from file."""
    try:
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading AST snapshot: {e}")
    return None


def is_ast_current(filepath: Path, ast_cache: Dict) -> bool:
    """Check if AST cache is current for a file."""
    if not ast_cache or 'files' not in ast_cache:
        return False
        
    rel_path = str(filepath.relative_to(Path.cwd()))
    file_data = ast_cache['files'].get(rel_path, {})
    
    try:
        return file_data.get('mtime') == filepath.stat().st_mtime
    except (OSError, KeyError):
        return False