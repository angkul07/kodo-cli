import os
from pathlib import Path
from dotenv import load_dotenv
import typer
from rich.console import Console
from rich.prompt import Confirm
from rich.markdown import Markdown 
from litellm import completion

from file_ops.reader import create_context_for_chat, read_file_content
from file_ops.writer import write_file_content, show_diff

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
app = typer.Typer()
console = Console()

@app.command()
def init():
    console.print("Initializing...")
    console.print("Project initialized! You can use 'chat' and 'edit' commands.")

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
    
    response = completion(
        model="gemini/gemini-2.5-flash",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
    )

    return response['choices'][0]['message']['content']

@app.command()
def chat(message: str):
    """Chat with AI about your code with project context"""
    console.print("Analyzing...")
    
    # Get project context
    context = create_context_for_chat(message)
    
    # Get AI response
    response = model_output(message, context)
    
    console.print("Response:")
    console.print(Markdown(response))

@app.command()
def edit(filepath: str, prompt: str):
    """Edit a file using AI assistance"""
    
    if not Path(filepath).exists():
        console.print(f"File {filepath} does not exist")
        return
    
    # console.print(f"Reading {filepath}...")
    
    original_content = read_file_content(filepath)
    if original_content.startswith("Error:"):
        console.print(original_content)
        return
    
    edit_prompt = f"""Please modify the following file based on this request: "{prompt}"

Current file content:
```
{original_content}
```

Return only the complete modified file content, no explanations or markdown formatting."""

    console.print("Generating...")
    
    new_content = model_output(edit_prompt)
    
    if new_content.startswith("```"):
        lines = new_content.split('\n')
        # Remove first and last lines if they contain ```
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        new_content = '\n'.join(lines)
    
    show_diff(original_content, new_content, filepath)
    
    # confirmation
    if Confirm.ask("Apply these changes?"):
        if write_file_content(filepath, new_content):
            console.print(f"Successfully updated {filepath}")
        else:
            console.print(f"Failed to update {filepath}")
    else:
        console.print("Changes cancelled")

@app.command()
def generate(filename: str, prompt: str):
    """Generate a new file using AI"""
    
    if Path(filename).exists():
        if not Confirm.ask(f"File {filename} already exists. Overwrite?"):
            console.print("File generation cancelled")
            return
    
    console.print(f"Generating {filename}...")
    
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
    # Preview content, markdown rendering not applied here as it's meant to be file content.
    console.print(content[:500] + "..." if len(content) > 500 else content)
    console.print("=" * 50)
    
    # Ask for confirmation
    if Confirm.ask("Create this file?"):
        if write_file_content(filename, content, create_backup=False):
            console.print(f"Successfully created {filename}")
        else:
            console.print(f"Failed to create {filename}")
    else:
        console.print("File generation cancelled")

if __name__ == "__main__":
    app()