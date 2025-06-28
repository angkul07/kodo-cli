# Kodo CLI - Intelligent Coding Assistant

An advanced AI-powered coding assistant that understands your entire codebase through intelligent context management and AST analysis.

## Features

### Context System
- **Multi-language AST analysis** supporting 30+ programming languages
- **Smart context loading** that finds relevant files for your queries
- **Living project documentation** that evolves with your code
- **Auto-updating context** when significant changes are detected

### AI-Powered Commands
- **`chat`** - Have conversations about your code with full project context
- **`edit`** - AI-assisted file editing with contextual awareness
- **`generate`** - Create new files that fit your project's patterns
- **`context`** - View current project understanding and recent activity

### Advanced Context Management
- **`overview.md`** - Concise project summary that serves as AI system prompt
- **`history.md`** - Complete log of all interactions and changes
- **`rules.cline`** - Customizable AI behavior and coding preferences
- **AST snapshot** - Deep understanding of code structure and relationships

## Installation

### From Source
```bash
# Clone the repository
git clone <repository-url>
cd kodo-cli

# Install the package
pip install .
```

### From Git
```bash
pip install git+<repository-url>
```

After installation, the `kodo` command will be available in your shell.

### Configuration
```bash
# Configure your LLM provider. It will configured globally. Re-run the command for re-configuring
kodo configure

# Initialize in your project
kodo init
```

## Supported LLM Providers

- **OpenAI** (GPT-3.5, GPT-4, GPT-4o)
- **Anthropic** (Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku)
- **Google Gemini** (Gemini 1.5 Flash, Gemini 2.0 Flash)
- **Huggingface** (DeepSeek R1, Qwen, Llama, Mixtral)
- **Ollama** (Local models - Llama 3.1, CodeLlama, Mistral, Phi3)

## Quick Start

### 1. Initialize Your Project
```bash
kodo init
```
This creates:
- `.kodo/context/snapshot.json` - AST analysis of your codebase
- `.kodo/context/overview.md` - Project summary and context
- `.kodo/context/history.md` - Development timeline
- `.kodo/context/rules.cline` - AI assistant preferences
- `.kodo/cache/` - Performance optimization data

### 2. Chat About Your Code
```bash
kodo chat "How does the authentication system work?"
kodo chat "What's the main entry point of this application?"
kodo chat "Explain the database schema"
```

### 3. AI-Assisted Editing
```bash
kodo edit main.py "Add error handling to the main function"
kodo edit config.py "Add support for environment variables"
```

### 4. Generate New Files
```bash
kodo generate tests/test_auth.py "Create comprehensive tests for authentication"
kodo generate docs/api.md "Create API documentation based on the code"
```

### 5. Agentic Mode
```bash
# Let the agent plan and execute complex tasks autonomously
kodo agent "create a REST API with user authentication and database"
kodo agent "refactor the codebase to use dependency injection" --auto-approve
kodo agent "add comprehensive error handling throughout the application"
kodo agent "implement automated testing for all core functions"
```

## Commands Reference

### Core Commands
- **`configure`** - Set up LLM provider and API keys
- **`init`** - Initialize intelligent context system in current directory
- **`status`** - Show current configuration and context status

### AI Commands
- **`chat <message>`** - Ask questions about your codebase
- **`edit <file> <prompt>`** - Modify files with AI assistance
- **`generate <file> <prompt>`** - Create new files with AI
- **`agent <goal>`** - **Agentic Mode** - Autonomous planning and execution

### Context Commands
- **`context`** - View current project context and recent activity
- **`update-context`** - Refresh project analysis and AST snapshot.

## How the Context System Works

### Project Analysis
Kodo uses advanced AST (Abstract Syntax Tree) parsing to understand:
- **Code structure** - Classes, functions, variables, imports
- **Dependencies** - Import relationships and module connections
- **Architecture patterns** - Detected patterns (MVC, API, microservices, etc.)
- **File relationships** - How different parts of your code interact

### Intelligent Context Loading
When you ask a question or request changes:
1. **Query analysis** - Extracts keywords and intent from your request
2. **Relevance scoring** - Finds files most relevant to your query
3. **Context assembly** - Builds focused context within token limits
4. **History integration** - Includes relevant past interactions

### Living Documentation
- **`overview.md`** serves as a system prompt, giving AI essential project context
- **`history.md`** logs every interaction, creating institutional memory
- **`rules.cline`** defines project-specific preferences and coding standards

## Customization

### Project Rules (`.kodo/context/rules.cline`)
```bash
# Context Configuration
max_context_files=8
max_file_size=20000
context_priority=main_files,recent_changes,query_relevant

# Code Style & Standards
- Write clean, readable code with meaningful names
- Add comments for complex logic
- Follow existing patterns in the codebase
- Maintain consistent formatting

# Response Guidelines
- Provide concise, actionable answers
- Include code examples when helpful
- Explain reasoning for significant changes
```

### Supported Languages
**Primary Support** (Full AST analysis):
- Python, JavaScript, TypeScript, Go, Rust, Java, C/C++

**Extended Support** (Basic analysis):
- PHP, Ruby, Swift, Kotlin, Scala, Dart, Lua, HTML, CSS, JSON, YAML

## Performance Features

### Smart Caching
- Only re-analyzes changed files
- Metadata tracking for performance optimization
- Auto-update triggers based on activity patterns

### Efficient Context Loading
- Relevance-based file selection
- Configurable context limits
- Preview generation for large files

### Auto-Update System
- Detects when context becomes stale
- Updates AST snapshot incrementally
- Maintains performance metrics

## Security & Privacy

- **Local-first** - All analysis happens on your machine
- **Configurable sharing** - Choose what context to include
- **API key security** - Secure storage and masked display
- **File size limits** - Prevents accidental inclusion of large files

## Advanced Usage

### Team Collaboration
```bash
# Share context with team (optional)
git add .kodo/context/overview.md .kodo/context/rules.cline
git commit -m "Add project context for AI assistance"

# Keep history private
echo ".kodo/context/history.md" >> .gitignore
```

### Custom Workflows
```bash
# Update context after major refactoring
kodo update-context

# Review recent development activity
kodo context

# Batch operations with context awareness
for file in src/*.py; do
    kodo edit "$file" "Add type hints and docstrings"
done
```

## Troubleshooting

### Common Issues

**"Could not update AST cache" error:**
- Ensure file paths are relative to project root
- Check file permissions and existence
- Run `kodo update-context` to refresh

**Context not loading:**
- Verify `.kodo/` directory exists
- Run `kodo init` to reinitialize
- Check LLM provider configuration with `kodo status`

**Large file warnings:**
- Adjust `max_file_size` in `.kodo/context/rules.cline`
- Add specific files to exclude patterns
- Use `.gitignore` patterns to skip generated files

### Performance Optimization
```bash
# Clear cache and rebuild
rm -rf .kodo/cache/
kodo update-context

# Adjust context limits
echo "max_context_files=5" >> .kodo/context/rules.cline
echo "max_file_size=15000" >> .kodo/context/rules.cline
```

## Contributing

Kodo CLI is designed to be extensible. Key areas for contribution:
- Additional language support via Tree-sitter
- New LLM provider integrations
- Enhanced context analysis algorithms
- Performance optimizations

**Built by me and Cursor** 