from pathlib import Path
import typer
from rich.console import Console
from rich.prompt import Confirm
from rich.markdown import Markdown

from file_ops.reader import create_context_for_chat, read_file_content
from file_ops.writer import write_file_content, show_diff
from llm.providers import LLMManager
from config.settings import ConfigManager

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


def model_output(query: str, context: str = "") -> str:
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
        console.print("\n📋 Current Configuration:")
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
    """Initialize mycode in current directory"""
    console.print("Initializing mycode...")
    
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
            "file_patterns": ["*.py", "*.js", "*.ts", "*.java", "*.cpp", "*.go"]
        }
        
        try:
            with open(local_config, 'w') as f:
                import json
                json.dump(project_config, f, indent=2)
            console.print(f"Created project config: {local_config}")
        except Exception as e:
            console.print(f"Could not create project config: {e}")
    
    console.print("Project initialized! You can now use 'chat', 'edit' and 'generate' commands.")

@app.command()
def chat(message: str):
    """Chat with AI about your code with project context"""
    ensure_configured()
    console.print("Analyzing...")
    
    # Get project context
    context = create_context_for_chat(message)
    
    # Get AI response
    try:
        response = model_output(message, context)
        console.print("Response: ")
        console.print(Markdown(response))
    except Exception as e:
        console.print(f"Error getting AI response: {e}")
        raise typer.Exit(1)

@app.command()
def edit(filepath: str, prompt: str):
    """Edit a file using AI assistance"""

    ensure_configured()
    
    if not Path(filepath).exists():
        console.print(f"File {filepath} does not exist")
        raise typer.Exit(1)
    
    # console.print(f"Reading {filepath}...")
    
    original_content = read_file_content(filepath)
    if original_content.startswith("Error:"):
        console.print(original_content)
        raise typer.Exit(1)
    
    edit_prompt = f"""Please modify the following file based on this request: "{prompt}"

Current file content:
```
{original_content}
```

Return only the complete modified file content, no explanations or markdown formatting."""

    console.print("Generating...")
    
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
            else:
                console.print(f"Failed to update {filepath}")
                raise typer.Exit(1)
        else:
            console.print("Changes cancelled")
    
    except Exception as e:
        console.print(f"Error during file editing: {e}")
        raise typer.Exit(1)

@app.command()
def generate(filename: str, prompt: str):
    """Generate a new file using AI"""
    ensure_configured()
    
    # Check if file already exists
    if Path(filename).exists():
        if not Confirm.ask(f"File {filename} already exists. Overwrite?"):
            console.print("File generation cancelled")
            return
    
    console.print(f"🤖 Generating {filename}...")
    
    try:
        # Get project context for better generation
        context = create_context_for_chat(prompt)
        
        generation_prompt = f"""Create a new file named "{filename}" based on this request: "{prompt}"

Project context:
{context}

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
            else:
                console.print(f"Failed to create {filename}")
                raise typer.Exit(1)
        else:
            console.print("File generation cancelled")
    
    except Exception as e:
        console.print(f"Error during file generation: {e}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()