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
    Topic, Syllabus, Question, KnowledgeBase,
    save_syllabus_to_json, load_syllabus_from_json,
    create_acronym_mnemonic, get_example_difference
)
from visual import create_simple_mindmap, create_tcp_handshake_animation, create_stack_animation

app = typer.Typer(help="AI Learning Engine CLI")
console = Console()


@app.command()
def init(db_path: str = "data/memory.db"):
    """Initialize the knowledge base."""
    kb = KnowledgeBase(db_path)
    console.print(f"[green]Knowledge base initialized at {db_path}[/green]")


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
    except Exception as e:
        console.print(f"[red]Error loading syllabus: {e}[/red]")


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
