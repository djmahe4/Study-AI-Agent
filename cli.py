#!/usr/bin/env python3
"""
CLI tool for managing the AI Learning Engine.
"""
import typer
import json
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich import print as rprint

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
    question_bank: Optional[str] = typer.Option(None, help="Path to question bank PDF (use @ prefix)"),
):
    """
    Create a new subject with syllabus processing via Gemini.
    
    Example:
        python cli.py create-subject "Machine Learning" --syllabus-file syllabus.txt --question-bank @questions.pdf
    """
    console.print(f"[cyan]Creating subject: {subject_name}[/cyan]")
    
    # Read syllabus text
    if syllabus_file and Path(syllabus_file).exists():
        with open(syllabus_file, 'r') as f:
            syllabus_text = f.read()
    else:
        console.print("[yellow]No syllabus file provided. Enter syllabus text (Ctrl+D to finish):[/yellow]")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        syllabus_text = '\n'.join(lines)
    
    if not syllabus_text.strip():
        console.print("[red]Error: No syllabus text provided[/red]")
        raise typer.Exit(1)
    
    # Process question bank path
    qbank_path = None
    if question_bank:
        if question_bank.startswith('@'):
            qbank_path = question_bank[1:]  # Remove @ prefix
            if not Path(qbank_path).exists():
                console.print(f"[yellow]Warning: Question bank file not found: {qbank_path}[/yellow]")
                qbank_path = None
            else:
                console.print(f"[green]Question bank found: {qbank_path}[/green]")
                # TODO: Initialize RAG tool for question bank
                console.print("[yellow]RAG tool will process this question bank (TODO: implement)[/yellow]")
    
    # Create subject folder
    subject_folder = create_subject_folder(subject_name)
    console.print(f"[green]Subject folder created: {subject_folder}[/green]")
    
    # Process syllabus with Gemini
    console.print("[cyan]Processing syllabus with Gemini (placeholder)...[/cyan]")
    processor = GeminiProcessor()
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
    
    subjects.append({
        "name": subject_name,
        "folder_path": subject_folder,
        "syllabus_path": syllabus_path,
        "question_bank_path": qbank_path,
        "created_at": str(subject.created_at)
    })
    
    with open(subjects_file, 'w') as f:
        json.dump(subjects, f, indent=2)
    
    console.print(f"\n[green]✅ Subject '{subject_name}' created successfully![/green]")
    console.print(f"[cyan]Extracted {len(syllabus.topics)} topics from syllabus[/cyan]")
    
    # Set as current subject
    _set_current_subject(subject_name)
    console.print(f"[yellow]Set '{subject_name}' as current subject[/yellow]")


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


if __name__ == "__main__":
    app()
