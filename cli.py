#!/usr/bin/env python3
"""
CLI tool for managing the AI Learning Engine.
"""
import typer
import sys
import json
import shlex
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from dotenv import load_dotenv
import os
import google.generativeai as genai
import subprocess

from core import (
    Topic, Syllabus, Question, Subject, KnowledgeBase,
    save_syllabus_to_json, load_syllabus_from_json,
    create_acronym_mnemonic, get_example_difference
)
from core.gemini_processor import GeminiProcessor, create_subject_folder
from core.rag import RAGEngine
from visual import create_simple_mindmap, create_tcp_handshake_animation, create_stack_animation

app = typer.Typer(help="AI Learning Engine CLI")
console = Console()

# Global state for current subject
CURRENT_SUBJECT_FILE = "data/.current_subject"

# Global variables
model = None
web_proc = None

@app.command()
def help():
    """Show help information."""
    rprint("[bold cyan]AI Learning Engine CLI[/bold cyan]")
    rprint("Use the following commands to manage your learning resources:")
    rprint("- [green]python web_app.py[/green]: Run the web interface")
    rprint("- [green]init[/green]: Initialize the knowledge base")
    rprint("- [green]create-subject[/green]: Create a new subject with syllabus processing")
    rprint("- [green]list-subjects[/green]: List all created subjects")
    rprint("- [green]select-subject[/green]: Select a subject to work with")
    rprint("- [green]add-topic[/green]: Add a new topic to the knowledge base")
    rprint("- [green]list-topics[/green]: List all topics in the knowledge base")
    rprint("- [green]add-question[/green]: Add a question to the knowledge base")
    rprint("- [green]list-questions[/green]: List questions, optionally filtered by topic")
    rprint("- [green]generate-mindmap[/green]: Generate a mind map from all topics")
    rprint("- [green]create-mnemonic[/green]: Create an acronym mnemonic from key points")
    rprint("- [green]show-difference[/green]: Show an example difference table")
    rprint("- [green]create-animation[/green]: Create an educational animation")
    rprint("- [green]load-syllabus[/green]: Load a syllabus from a JSON file")
    rprint("- [green]export-syllabus[/green]: Export all topics as a syllabus")
    rprint("- [green]set-api-key[/green]: Set the Google API key for Gemini AI")
    rprint("- [green]delete-subject <subject_name>[/green]: Delete a subject")
    rprint("- [green]exit[/green]: Exit the CLI")

@app.command()
def set_api_key(api_key: str):
    """Set the Google API key for Gemini AI."""
    Path(".env").touch(exist_ok=True)
    with open(".env", "a") as f:
        f.write(f"GOOGLE_API_KEY={api_key}\n")
    console.print("[green]API key set successfully![/green]")

@app.command()
def gemini_init():
    #global model
    """Initialize Gemini AI integration."""
    load_dotenv()
    try:
        api_key = os.environ["GOOGLE_API_KEY"]
    except KeyError:
        console.print("[red]Error: GOOGLE_API_KEY not set in environment variables.[/red]")
        console.print("[yellow]Please set the API key using /set-api-key command or in a .env file.[/yellow]")
        raise typer.Exit(1)
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    console.print("[green]Gemini AI integration initialized (placeholder)[/green]")
    return model


@app.command()
def init(db_path: str = "data/memory.db"):
    """Initialize the knowledge base."""
    kb = KnowledgeBase(db_path)
    Path("data/subjects").mkdir(parents=True, exist_ok=True)
    console.print(f"[green]Knowledge base initialized at {db_path}[/green]")
    console.print(f"[green]Subjects folder created at data/subjects[/green]")


@app.command()
def create_subject(
    subject_name: str = typer.Argument(..., help="Name of the subject"),
    syllabus_file: Optional[str] = typer.Option(None, help="Path to syllabus text file"),
    question_bank: Optional[str] = typer.Option(None, help="Path to question bank PDF"), #(use @ prefix)
):
    """
    Create a new subject with syllabus processing via Gemini.
    
    Example:
        python cli.py create-subject "Machine Learning" --syllabus-file syllabus.txt --question-bank @questions.pdf
    """
    global model
    if not model:
        model = gemini_init()
    console.print(f"[cyan]Creating subject: {subject_name}[/cyan]")
    
    # Read syllabus text
    if syllabus_file and Path(syllabus_file).exists():
        with open(syllabus_file, 'r') as f:
            syllabus_text = f.read()
    else:
        # console.print("[yellow]No syllabus file provided. Enter syllabus text (Ctrl+D to finish):[/yellow]")
        # lines = []
        # try:
        #     while True:
        #         line = input()
        #         lines.append(line)
        # except EOFError:
        #     pass
        # syllabus_text = '\n'.join(lines)
        try:
            # Reads everything until Ctrl+D (Linux/macOS) or Ctrl+Z+Enter (Windows)
            syllabus_text = sys.stdin.read()
        except KeyboardInterrupt:
            console.print("[red]Input cancelled by user.[/red]")
            syllabus_text = ""

        if syllabus_text.strip():
            console.print("[green]Collected syllabus:[/green]")
            console.print(syllabus_text)
        else:
            console.print("[red]No input provided.[/red]")
    
    if not syllabus_text.strip():
        console.print("[red]Error: No syllabus text provided[/red]")
        raise typer.Exit(1)
    
    # Process question bank path
    qbank_path = question_bank
    if qbank_path and not Path(qbank_path).exists():
        console.print(f"[yellow]Warning: Question bank file not found: {qbank_path}[/yellow]")
        qbank_path = None
    elif qbank_path:
        console.print(f"[green]Question bank found: {qbank_path}[/green]")
        # TODO: Initialize RAG tool for question bank
        console.print("[yellow]RAG tool will process this question bank (TODO: implement)[/yellow]")

    # Create subject folder
    subject_folder = create_subject_folder(subject_name)
    console.print(f"[green]Subject folder created: {subject_folder}[/green]")
    
    # Process syllabus with Gemini
    console.print("[cyan]Processing syllabus with Gemini (placeholder)...[/cyan]")
    processor = GeminiProcessor(model)
    syllabus = processor.process_syllabus_text(syllabus_text, subject_name)
    
    if qbank_path:
        syllabus.question_bank_path = qbank_path
    
    # Save syllabus
    syllabus_path = f"{subject_folder}/syllabus/{subject_name.lower().replace(' ', '_')}.json"
    save_syllabus_to_json(syllabus, syllabus_path)
    console.print(f"[green]Syllabus saved: {syllabus_path}[/green]")
    
    # Create subject metadata
    subject = Subject(
        name=subject_name,
        syllabus=syllabus,
        folder_path=subject_folder,
        question_bank_path=qbank_path
    )
    
    # Save subject list
    subjects_file = "data/subjects/subjects.json"
    subjects = []
    if Path(subjects_file).exists():
        with open(subjects_file, 'r') as f:
            subjects = json.load(f)
    
    # Check if subject already exists
    existing_subject = next((s for s in subjects if s["name"] == subject_name), None)
    
    if existing_subject:
        # Update existing subject
        console.print(f"[yellow]Subject '{subject_name}' already exists. Updating it.[/yellow]")
        existing_subject.update({
            "folder_path": subject_folder,
            "syllabus_path": syllabus_path,
            "question_bank_path": qbank_path,
            "created_at": str(subject.created_at)
        })
    else:
        # Add new subject
        subjects.append({
            "name": subject_name,
            "folder_path": subject_folder,
            "syllabus_path": syllabus_path,
            "question_bank_path": qbank_path,
            "created_at": str(subject.created_at)
        })
    
    with open(subjects_file, 'w') as f:
        json.dump(subjects, f, indent=2)
    
    console.print(f"\n[green]✅ Subject '{subject_name}' created/updated successfully![/green]")
    console.print(f"[cyan]Extracted {len(syllabus.topics)} topics from syllabus[/cyan]")
    
    # Set as current subject
    _set_current_subject(subject_name)
    console.print(f"[yellow]Set '{subject_name}' as current subject[/yellow]")


@app.command()
def delete_subject(subject_name: str = typer.Argument(..., help="Name of the subject to delete")):
    """Delete a subject."""
    subjects_file = "data/subjects/subjects.json"
    
    if not Path(subjects_file).exists():
        console.print("[red]No subjects found.[/red]")
        raise typer.Exit(1)
    
    with open(subjects_file, 'r') as f:
        subjects = json.load(f)
    
    subject_to_delete = next((s for s in subjects if s["name"] == subject_name), None)
    
    if not subject_to_delete:
        console.print(f"[red]Subject '{subject_name}' not found.[/red]")
        raise typer.Exit(1)
    
    if typer.confirm(f"Are you sure you want to delete the subject '{subject_name}'?"):
        subjects = [s for s in subjects if s["name"] != subject_name]
        
        with open(subjects_file, 'w') as f:
            json.dump(subjects, f, indent=2)
        
        console.print(f"[green]Subject '{subject_name}' deleted successfully.[/green]")
        
        if typer.confirm("Do you also want to delete the subject's folder and all its contents?"):
            import shutil
            shutil.rmtree(subject_to_delete["folder_path"])
            console.print(f"[green]Subject folder '{subject_to_delete['folder_path']}' deleted.[/green]")
    else:
        console.print("Deletion cancelled.")


@app.command()
def list_subjects():
    """List all created subjects."""
    subjects_file = "data/subjects/subjects.json"
    
    if not Path(subjects_file).exists():
        console.print("[yellow]No subjects found. Create one with 'create-subject'[/yellow]")
        return
    
    with open(subjects_file, 'r') as f:
        subjects = json.load(f)
    
    if not subjects:
        console.print("[yellow]No subjects found.[/yellow]")
        return
    
    current_subject = _get_current_subject()
    
    table = Table(title="Available Subjects")
    table.add_column("Subject", style="cyan")
    table.add_column("Folder", style="green")
    table.add_column("Question Bank", style="yellow")
    table.add_column("Current", style="magenta")
    
    for subj in subjects:
        is_current = "✓" if subj["name"] == current_subject else ""
        qbank = "Yes" if subj.get("question_bank_path") else "No"
        table.add_row(
            subj["name"],
            subj["folder_path"],
            qbank,
            is_current
        )
    
    console.print(table)


@app.command()
def select_subject(subject_name: str = typer.Argument(..., help="Name of the subject to select")):
    """Select a subject to work with."""
    subjects_file = "data/subjects/subjects.json"
    
    if not Path(subjects_file).exists():
        console.print("[red]No subjects found. Create one first.[/red]")
        raise typer.Exit(1)
    
    with open(subjects_file, 'r') as f:
        subjects = json.load(f)
    
    subject_names = [s["name"] for s in subjects]
    
    if subject_name not in subject_names:
        console.print(f"[red]Subject '{subject_name}' not found.[/red]")
        console.print(f"[yellow]Available subjects: {', '.join(subject_names)}[/yellow]")
        raise typer.Exit(1)
    
    _set_current_subject(subject_name)
    console.print(f"[green]Selected subject: {subject_name}[/green]")


def _set_current_subject(subject_name: str):
    """Save current subject to file."""
    Path(CURRENT_SUBJECT_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(CURRENT_SUBJECT_FILE, 'w') as f:
        f.write(subject_name)


def _get_current_subject() -> Optional[str]:
    """Get current subject from file."""
    if Path(CURRENT_SUBJECT_FILE).exists():
        with open(CURRENT_SUBJECT_FILE, 'r') as f:
            return f.read().strip()
    return None


@app.command()
def add_topic(
    name: str = typer.Argument(..., help="Topic name"),
    summary: str = typer.Option("", help="Topic summary"),
    key_points: str = typer.Option("", help="Comma-separated key points"),
):
    """Add a new topic to the knowledge base."""
    kb = KnowledgeBase()
    
    topic = Topic(
        name=name,
        summary=summary,
        key_points=[kp.strip() for kp in key_points.split(",")] if key_points else []
    )
    
    kb.save_topic(topic)
    console.print(f"[green]Topic '{name}' added successfully![/green]")


@app.command()
def list_topics():
    """List all topics in the knowledge base."""
    kb = KnowledgeBase()
    topics = kb.get_topics()
    
    if not topics:
        console.print("[yellow]No topics found. Add some topics first![/yellow]")
        return
    
    table = Table(title="Topics in Knowledge Base")
    table.add_column("Name", style="cyan")
    table.add_column("Summary", style="green")
    table.add_column("Key Points", style="yellow")
    
    for topic in topics:
        table.add_row(
            topic.name,
            topic.summary[:50] + "..." if len(topic.summary) > 50 else topic.summary,
            str(len(topic.key_points))
        )
    
    console.print(table)


@app.command()
def add_question(
    topic: str = typer.Argument(..., help="Topic name"),
    question: str = typer.Argument(..., help="Question text"),
    answer: str = typer.Argument(..., help="Answer text"),
    difficulty: str = typer.Option("medium", help="Difficulty level (easy/medium/hard)"),
):
    """Add a question to the knowledge base."""
    kb = KnowledgeBase()
    
    q = Question(
        topic=topic,
        question=question,
        answer=answer,
        difficulty=difficulty
    )
    
    kb.save_question(q)
    console.print(f"[green]Question added for topic '{topic}'![/green]")


@app.command()
def list_questions(topic: Optional[str] = None):
    """List questions, optionally filtered by topic."""
    kb = KnowledgeBase()
    questions = kb.get_questions(topic)
    
    if not questions:
        console.print("[yellow]No questions found.[/yellow]")
        return
    
    table = Table(title=f"Questions{' for ' + topic if topic else ''}")
    table.add_column("Topic", style="cyan")
    table.add_column("Question", style="green")
    table.add_column("Difficulty", style="yellow")
    
    for q in questions:
        table.add_row(
            q.topic,
            q.question[:60] + "..." if len(q.question) > 60 else q.question,
            q.difficulty
        )
    
    console.print(table)


@app.command()
def generate_mindmap(output_format: str = "json"):
    """Generate a mind map from all topics."""
    kb = KnowledgeBase()
    topics = kb.get_topics()
    
    if not topics:
        console.print("[yellow]No topics found. Add some topics first![/yellow]")
        return
    
    output_path = create_simple_mindmap(topics, output_format)
    console.print(f"[green]Mind map generated at {output_path}[/green]")


@app.command()
def create_mnemonic(topic: str, key_points: str):
    """Create an acronym mnemonic from key points."""
    points = [p.strip() for p in key_points.split(",")]
    mnemonic = create_acronym_mnemonic(topic, points)
    
    console.print(f"[cyan]Topic:[/cyan] {mnemonic.topic}")
    console.print(f"[cyan]Technique:[/cyan] {mnemonic.technique}")
    console.print(f"[green]Mnemonic:[/green] {mnemonic.content}")
    console.print(f"[yellow]Explanation:[/yellow] {mnemonic.explanation}")
@app.command()
def run_web():
    global web_proc
    """Run the web interface."""
    console.print("[cyan]Starting web interface...[/cyan]")
    try:
        web_proc=subprocess.Popen([sys.executable, "streamlit/app.py"])
    except Exception as e:
        console.print(f"[red]Failed to start web interface: {e}[/red]")
@app.command()
def stop_web():
    global web_proc
    """Stop the web interface."""
    console.print("[cyan]Stopping web interface...[/cyan]")
    if web_proc:
        web_proc.terminate()

@app.command()
def show_difference(example: str = "tcp_vs_udp"):
    """Show an example difference table."""
    diff = get_example_difference(example)
    
    if not diff:
        console.print(f"[red]Example '{example}' not found.[/red]")
        console.print("[yellow]Available examples: tcp_vs_udp, stack_vs_queue[/yellow]")
        return
    
    table = Table(title=f"{diff.concept_a} vs {diff.concept_b}")
    table.add_column("Aspect", style="cyan")
    table.add_column(diff.concept_a, style="green")
    table.add_column(diff.concept_b, style="yellow")
    
    for item in diff.differences:
        table.add_row(
            item["aspect"],
            item["concept_a_value"],
            item["concept_b_value"]
        )
    
    console.print(table)


@app.command()
def create_animation(animation_type: str = "tcp"):
    """Create an educational animation."""
    if animation_type == "tcp":
        output_path = create_tcp_handshake_animation()
        console.print(f"[green]TCP handshake animation created at {output_path}[/green]")
    elif animation_type == "stack":
        output_path = create_stack_animation()
        console.print(f"[green]Stack animation created at {output_path}[/green]")
    else:
        console.print(f"[red]Unknown animation type: {animation_type}[/red]")
        console.print("[yellow]Available types: tcp, stack[/yellow]")


@app.command()
def load_syllabus(file_path: str):
    """Load a syllabus from a JSON file."""
    kb = KnowledgeBase()
    
    try:
        syllabus = load_syllabus_from_json(file_path)
        
        for topic in syllabus.topics:
            kb.save_topic(topic)
        
        console.print(f"[green]Loaded {len(syllabus.topics)} topics from {file_path}[/green]")
    except FileNotFoundError:
        console.print(f"[red]Error: File not found at {file_path}[/red]")
    except json.JSONDecodeError:
        console.print(f"[red]Error: Could not decode JSON from {file_path}[/red]")
    except Exception as e:
        console.print(f"[red]An unexpected error occurred: {e}[/red]")


@app.command()
def export_syllabus(output_path: str = "data/syllabus/export.json"):
    """Export all topics as a syllabus."""
    kb = KnowledgeBase()
    topics = kb.get_topics()
    
    syllabus = Syllabus(
        title="Exported Syllabus",
        description="All topics from knowledge base",
        topics=topics
    )
    
    save_syllabus_to_json(syllabus, output_path)
    console.print(f"[green]Syllabus exported to {output_path}[/green]")
@app.command()
def exit():
    """Exit the CLI."""
    console.print("[cyan]Exiting AI Learning Engine CLI. Goodbye![/cyan]")
    raise typer.Exit()
@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Main callback for interactive mode."""
    if ctx.invoked_subcommand is None:
        # Interactive mode
        while True:
            try:
                help()
                user_input = typer.prompt("\nEnter command (or 'exit' to quit)")
                if user_input.lower() == "exit":
                    console.print("[cyan]Exiting AI Learning Engine CLI. Goodbye![/cyan]")
                    break
                
                # Parse command and execute
                try:
                    # Split command into parts while respecting quoted strings
                    args = shlex.split(user_input.strip())
                    if args:
                        # Invoke the app with the parsed arguments
                        app.main(args, standalone_mode=False)
                except SystemExit:
                    # Typer commands may raise SystemExit, catch and continue
                    pass
                except Exception as e:
                    console.print(f"[red]Error executing command: {e}[/red]")
                    console.print("[yellow]Type 'help' to see available commands[/yellow]")
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'exit' command to quit[/yellow]")
                continue
            except EOFError:
                console.print("\n[cyan]Exiting...[/cyan]")
                break

if __name__ == "__main__":
    try:
        app()
    except Exception as e:
        import traceback
        traceback.print_exc()
        console.print(f"[red]An error occurred: {e}[/red]")
