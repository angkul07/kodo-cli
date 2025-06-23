import os
from dotenv import load_dotenv
import typer
from rich.console import Console
from litellm import completion

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
app = typer.Typer()
console = Console()

@app.command()
def init():
    console.print("Initializing...")

def model_output(query: str):
    """The model will complete the queries"""
    response = completion(
        model="gemini/gemini-2.5-flash",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that complete the query of user in less than 100 words and give output in markdown."},
            {"role": "user", "content": query}
        ]
    )

    return response['choices'][0]['message']['content']

@app.command()
def chat(message: str):
    """Chat with AI"""
    console.print(f"{model_output(message)}")

@app.command()
def edit(prompt: str):
    pass

@app.command()
def generate():
    pass


if __name__ == "__main__":
    app()