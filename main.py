from pathlib import Path
import typer
import json
from rich.console import Console
from rich.prompt import Confirm
from rich.markdown import Markdown

from file_ops.reader import read_file_content
from file_ops.writer import write_file_content, show_diff
from llm.providers import LLMManager
from config.settings import ConfigManager
from context_manager import ContextManager
from agent.core import CodeAgent

app = typer.Typer()
console = Console()

# Global instances
config_manager = ConfigManager()
llm_manager = LLMManager()

def ensure_configured():
    """Ensure LLM provider is configured"""
    if not config_manager.is_configured():
        console.print("LLM provider not configured!")
        console.print("Please run: python main.py configure")
        raise typer.Exit(1)
    
    # Load and set the provider
    try:
        provider_key = config_manager.get('llm.provider')
        llm_config = config_manager.get_llm_config()
        provider = llm_manager.create_provider(provider_key, llm_config)
        llm_manager.set_provider(provider)
    except Exception as e:
        console.print(f"Error loading LLM provider: {e}")
        console.print("Please run: python main.py configure")
        raise typer.Exit(1)


def model_output(query: str = "", context: str = "", system_message: str = "") -> str:
    """The model will complete the queries with optional context"""
    
    system_message = """You are a helpful coding assistant. You help with code analysis, debugging, and modifications.
    
When editing files:
- Make targeted changes based on the user's request
- Preserve existing code structure and style
- Add comments where helpful
- Return only the complete modified file content

Keep responses concise and practical."""

    user_message = query
    if context:
        user_message = f"Context:\n{context}\n\nUser Query: {query}"
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]
    
    return llm_manager.get_completion(messages)

@app.command()
def configure():
    """Configure LLM provider and settings"""
    console.print("🔧 Configuration Setup")
    
    if config_manager.is_configured():
        console.print("\n Current Configuration:")
        config_manager.show_current_config()
        
        if not Confirm.ask("\nReconfigure?"):
            return
    
    config_manager.setup_interactive()

@app.command()
def status():
    """Show current configuration status"""
    console.print("MyCode CLI Status\n")
    
    if config_manager.is_configured():
        console.print("LLM Provider: Configured")
        config_manager.show_current_config()
    else:
        console.print("LLM Provider: Not configured")
        console.print("Run 'python main.py configure' to set up")

@app.command()
def init():
    """Initialize mycode with advanced context management"""
    console.print("Initializing mycode with enhanced context system...")
    
    if not config_manager.is_configured():
        console.print("LLM provider not configured. Let's set it up first!")
        if Confirm.ask("Configure now?"):
            config_manager.setup_interactive()
        else:
            console.print("You can configure later with: python main.py configure")
            return
    
    # Create local project config if needed
    local_config = Path.cwd() / ".mycode.json"
    if not local_config.exists():
        project_config = {
            "project_name": Path.cwd().name,
            "created_at": str(Path.cwd()),
            "file_patterns": ["*.py", "*.js", "*.ts", "*.java", "*.cpp", "*.c", "*.go", "*.rs", "*.rb", "*.php"]
        }
        
        try:
            with open(local_config, 'w') as f:
                json.dump(project_config, f, indent=2)
            console.print(f"Created project config: {local_config}")
        except Exception as e:
            console.print(f"Could not create project config: {e}")

    # Initialize the enhanced context system
    context_manager = ContextManager(Path.cwd())
    if context_manager.initialize_context():
        console.print("\nProject initialized with intelligent context system!")
        console.print("\nAvailable commands:")
        console.print("• `mycode chat \"your question\"` - Chat with AI about your code")
        console.print("• `mycode edit <file> \"changes to make\"` - AI-assisted file editing")
        console.print("• `mycode generate <file> \"what to create\"` - Generate new files")
        console.print("• `mycode context` - View current project context")
        console.print("• `mycode update-context` - Refresh project context")
    else:
        console.print("Failed to initialize context system")
        raise typer.Exit(1)

@app.command()
def chat(message: str):
    """Chat with AI about your code with intelligent context"""
    ensure_configured()
    console.print("Analyzing project context...")
    
    # Get intelligent context using the new system
    context_manager = ContextManager(Path.cwd())
    context = context_manager.get_context_for_query(message)
    
    # Get AI response
    try:
        response = model_output(message, context)
        console.print("\nResponse:")
        console.print(Markdown(response))
        
        # Log this interaction to history
        response_summary = response[:200] + "..." if len(response) > 200 else response
        context_manager.log_interaction(
            query=message,
            response_summary=response_summary,
            files_involved=_extract_files_from_query(message)
        )
        
    except Exception as e:
        console.print(f"Error getting AI response: {e}")
        raise typer.Exit(1)

@app.command()
def edit(filepath: str, prompt: str):
    """Edit a file using AI assistance with context awareness"""
    ensure_configured()
    
    if not Path(filepath).exists():
        console.print(f"File {filepath} does not exist")
        raise typer.Exit(1)
    
    console.print(f"Reading {filepath}...")
    
    original_content = read_file_content(filepath)
    if original_content.startswith("Error:"):
        console.print(original_content)
        raise typer.Exit(1)
    
    # Get intelligent context
    context_manager = ContextManager(Path.cwd())
    project_context = context_manager.get_context_for_query(f"edit {filepath} {prompt}")
    
    edit_prompt = f"""Please modify the following file based on this request: "{prompt}"

Project Context:
{project_context}

Current file content:
```
{original_content}
```

Return only the complete modified file content, no explanations or markdown formatting."""

    console.print("Generating changes...")
    
    try:
        # Get AI response
        new_content = model_output(edit_prompt)
        
        # Clean up the response (remove potential markdown formatting)
        if new_content.startswith("```"):
            lines = new_content.split('\n')
            # Remove first and last lines if they contain ```
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            new_content = '\n'.join(lines)
        
        # Show diff
        show_diff(original_content, new_content, filepath)
        
        # Ask for confirmation
        if Confirm.ask("Apply these changes?"):
            backup_enabled = config_manager.get('behavior.auto_backup', True)
            if write_file_content(filepath, new_content, create_backup=backup_enabled):
                console.print(f"Successfully updated {filepath}")
                
                # Update project history with detailed info
                context_manager.update_history("File Edit", {
                    "files": [filepath],
                    "summary": prompt,
                    "description": f"AI-assisted edit of {filepath}: {prompt}",
                    "impact": "File content modified with AI assistance"
                })
                
                # Also log the interaction
                context_manager.log_interaction(
                    query=f"Edit {filepath}: {prompt}",
                    response_summary="File successfully edited and changes applied",
                    files_involved=[filepath]
                )
            else:
                console.print(f"Failed to update {filepath}")
                raise typer.Exit(1)
        else:
            console.print("Changes cancelled")
            # Still log the interaction even if cancelled
            context_manager.log_interaction(
                query=f"Edit {filepath}: {prompt}",
                response_summary="Changes generated but cancelled by user",
                files_involved=[filepath]
            )
    
    except Exception as e:
        console.print(f"Error during file editing: {e}")
        raise typer.Exit(1)

@app.command()
def generate(filename: str, prompt: str):
    """Generate a new file using AI with project context"""
    ensure_configured()
    
    # Check if file already exists
    if Path(filename).exists():
        if not Confirm.ask(f"File {filename} already exists. Overwrite?"):
            console.print("File generation cancelled")
            return
    
    console.print(f"Generating {filename}...")
    
    try:
        # Get intelligent context for generation
        context_manager = ContextManager(Path.cwd())
        project_context = context_manager.get_context_for_query(f"generate {filename} {prompt}")
        
        generation_prompt = f"""Create a new file named "{filename}" based on this request: "{prompt}"

Project Context:
{project_context}

Return only the file content, no explanations or markdown formatting."""

        # Generate content
        content = model_output(generation_prompt)
        
        # Clean up the response
        if content.startswith("```"):
            lines = content.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = '\n'.join(lines)
        
        # Show preview
        console.print(f"Generated content for {filename}:")
        console.print("=" * 50)
        console.print(content[:500] + "..." if len(content) > 500 else content)
        console.print("=" * 50)
        
        # Ask for confirmation
        if Confirm.ask("Create this file?"):
            if write_file_content(filename, content, create_backup=False):
                console.print(f"Successfully created {filename}")
                
                # Update project history
                context_manager.update_history("File Generation", {
                    "files": [filename],
                    "summary": prompt,
                    "description": f"AI-generated new file: {filename} - {prompt}",
                    "impact": "New file added to project"
                })
                
                # Log the interaction
                context_manager.log_interaction(
                    query=f"Generate {filename}: {prompt}",
                    response_summary="New file successfully generated and created",
                    files_involved=[filename]
                )
            else:
                console.print(f"Failed to create {filename}")
                raise typer.Exit(1)
        else:
            console.print("File generation cancelled")
            # Still log the interaction
            context_manager.log_interaction(
                query=f"Generate {filename}: {prompt}",
                response_summary="File generated but creation cancelled by user",
                files_involved=[]
            )
    
    except Exception as e:
        console.print(f"Error during file generation: {e}")
        raise typer.Exit(1)

@app.command()
def context():
    """Show current project context information"""
    context_manager = ContextManager(Path.cwd())
    
    # Check if context exists
    if not context_manager.context_dir.exists():
        console.print("No context found. Run 'mycode init' first.")
        return
    
    console.print("Project Context Status\n")
    
    # Show overview
    if context_manager.overview_path.exists():
        overview = context_manager._load_overview()
        console.print(Markdown(overview))
    
    # Show recent activity
    if context_manager.history_path.exists():
        console.print("\nRecent Activity:")
        history = context_manager._load_recent_history(days=3)
        
        # Extract last few entries
        lines = history.split('\n')
        recent_entries = []
        entry_count = 0
        
        for line in reversed(lines):
            if line.startswith("###") and ("AI Interaction" in line or "File Edit" in line or "File Generation" in line):
                entry_count += 1
                if entry_count > 3:  # Show last 3 entries
                    break
            if entry_count > 0:
                recent_entries.insert(0, line)
        
        if recent_entries:
            console.print(Markdown('\n'.join(recent_entries)))
        else:
            console.print("No recent activity found")

@app.command() 
def update_context():
    """Update project context and AST snapshot"""
    console.print("Updating project context...")
    
    context_manager = ContextManager(Path.cwd())
    
    if context_manager.initialize_context():
        console.print("Context updated successfully!")
        
        # Log the update
        context_manager.update_history("Context Update", {
            "files": ["context system"],
            "summary": "Manual context refresh",
            "description": "Project context and AST snapshot updated manually",
            "impact": "Refreshed codebase understanding and indexes"
        })
    else:
        console.print("Failed to update context")
        raise typer.Exit(1)

@app.command()
def agent(goal: str, auto_approve: bool = False):
    """Run the intelligent code agent to accomplish a coding goal"""
    ensure_configured()
    
    console.print("[bold cyan]Initializing Code Agent...[/bold cyan]")
    console.print(f"[dim]Goal: {goal}[/dim]")
    
    try:
        # Create the agent
        agent = CodeAgent(llm_manager, Path.cwd())
        
        # Execute the goal
        success = agent.execute_goal(goal, auto_approve)
        
        if success:
            console.print("\n[bold green]Agent mission accomplished![/bold green]")
            
            # Show session summary
            summary = agent.get_session_summary()
            console.print(f"\nSession Summary:")
            console.print(f"  • Steps completed: {summary['steps_completed']}/{summary['total_steps']}")
            console.print(f"  • Memory items: {summary['memory_items']}")
            console.print(f"  • Session ID: {summary['session_id']}")
            
        else:
            console.print("\n[yellow]Agent could not complete all tasks[/yellow]")
            summary = agent.get_session_summary()
            console.print(f"  • Steps completed: {summary['steps_completed']}/{summary['total_steps']}")
            
    except Exception as e:
        console.print(f"[red]Agent initialization error: {e}[/red]")
        raise typer.Exit(1)

def _extract_files_from_query(query: str) -> list:
    """Extract potential file names from a query string"""
    words = query.split()
    files = []
    
    for word in words:
        # Look for file extensions
        if '.' in word and any(word.endswith(ext) for ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.rb', '.php', '.md', '.txt', '.json', '.yaml', '.yml']):
            files.append(word)
        # Look for file paths
        elif '/' in word:
            files.append(word)
    
    return files

if __name__ == "__main__":
    app()