#!/usr/bin/env python3
"""
CLI tool for managing the AI Learning Engine.
"""
import logging
from icecream import ic
import typer
import sys
import platform
import json
import time
import shlex
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from dotenv import load_dotenv
import os
import google.genai as genai
import subprocess
from pydantic import ValidationError

from core import (
    Topic, Syllabus, Question, Subject, KnowledgeBase,
    save_syllabus_to_json, load_syllabus_from_json,
    create_acronym_mnemonic, get_example_difference,
    save_syllabus_to_markdown
)
from core.models import ExamPattern, ExamSection, AnalyzedQuestion
from core.pomodoro import PomodoroTimer
from core.gamification import GamificationManager
from core.todo_manager import TodoManager
from core.flashcards import FlashcardManager
from core.gemini_processor import GeminiProcessor, create_subject_folder
from core.rag import RAGEngine
from core.exam_analysis import QuestionPaperAnalyzer
from visual import create_simple_mindmap, create_tcp_handshake_animation, create_stack_animation
from visual.mindmap_v2 import MindMapGenerator2
from core.utils import get_subject_dir

app = typer.Typer(help="AI Learning Engine CLI")
console = Console()

# Persistence Manager
from core.persistence import get_persistence_manager

# Global state for current subject
CURRENT_SUBJECT_FILE = "data/.current_subject"

# Global variables
model = None
web_proc = None
client = None

@app.command()
def configure_exam(name: str = typer.Argument(..., help="Name of the exam pattern (e.g. 'University2024')")):
    """
    Interactive wizard to define an exam structure/pattern.
    """
    console.print(f"[cyan]Configuring Exam Pattern: {name}[/cyan]")
    
    sections = []
    while typer.confirm("Add a section (e.g. Part A)?", default=True):
        sec_name = typer.prompt("Section Name")
        start = typer.prompt("Start Question #", type=int)
        end = typer.prompt("End Question #", type=int)
        marks = typer.prompt("Marks per question", type=int)
        choice = typer.confirm("Is there internal choice?", default=False)
        
        sections.append(ExamSection(
            name=sec_name, 
            question_range=[start, end], 
            marks_per_question=marks,
            has_choice=choice
        ))
        
    # Module Mapping
    module_map = {}
    console.print("\n[yellow]Map Questions to Modules[/yellow]")
    while True:
        mod_name = typer.prompt("Module Name (or 'done' to finish)")
        if mod_name.lower() == 'done': break
        
        q_nums_str = typer.prompt(f"Question Numbers for {mod_name} (comma separated, e.g. 1,2,11)")
        try:
            q_nums = [int(x.strip()) for x in q_nums_str.split(",")]
            module_map[mod_name] = q_nums
        except ValueError:
            console.print("[red]Invalid format. Use comma separated numbers.[/red]")
            
    pattern = ExamPattern(name=name, sections=sections, module_mapping=module_map)
    
    # Save
    path = Path(f"data/exam_patterns/{name}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(pattern.model_dump_json(indent=2))
        
    console.print(f"[green]Pattern saved to {path}[/green]")

@app.command()
def ingest_paper(
    file_path: str = typer.Argument(..., help="Path to PDF"),
    ex_pattern: str = typer.Argument(...,help="Name of the exam pattern to use"),
    year: str = typer.Argument("Unknown", help="Year of the paper")
):
    """
    Ingest and analyze a question paper PDF using a defined pattern.
    """
    current_subject = _get_current_subject()
    if not current_subject:
        console.print("[red]No subject selected.[/red]")
        return
        
    # Load Pattern
    pat_path = Path(f"data/exam_patterns/{ex_pattern}.json")
    if not pat_path.exists():
        console.print(f"[red]Pattern '{ex_pattern}' not found. Create it with 'configure-exam'[/red]")
        return

    try:
        with open(pat_path, "r", encoding="utf-8") as f:
            data = json.load(f)  # Validates JSON syntax early

        exam_pattern = ExamPattern.model_validate(data)
        #ic(exam_pattern)

    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error in {pat_path}: {e}")
        raise ValueError(f"Invalid JSON format in {pat_path}: {e}") from e
    except ValidationError as e:
        logging.error(f"Exam pattern validation error in {pat_path}: {e}")
        raise ValueError(f"Exam pattern validation failed: {e}") from e
        
    # Initialize Analyzer
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        console.print("[red]API Key not found.[/red]")
        return
        
    analyzer = QuestionPaperAnalyzer(api_key)
    
    with console.status(f"[cyan]Analyzing {file_path}...[/cyan]"):
        questions = analyzer.analyze_paper(file_path, exam_pattern, year)
        
    if not questions:
        console.print("[red]No questions extracted.[/red]")
        return
        
    # Save to KB
    kb = KnowledgeBase()
    kb.save_analyzed_questions(questions, current_subject)
    
    # Summary
    console.print(f"[green]Extracted {len(questions)} questions.[/green]")
    for q in questions:
        console.print(f" - Q{q.number} ({q.module}): {q.text[:50]}...")
        
    # Update Importance (Simple Stub)
    # TODO: Load syllabus, increment scores based on module frequency
    console.print("[yellow]Topic importance update pending (requires topic-level mapping, currently at Module level).[/yellow]")

@app.command()
def get_pyq_answers(
    module: Optional[str] = typer.Option(None, help="Specific module to generate answers for")
):
    """
    Generate answers for ingested Previous Year Questions (PYQs).
    """
    current_subject = _get_current_subject()
    subject_path= get_subject_dir(current_subject)
    if not current_subject:
        console.print("[red]No subject selected.[/red]")
        return
        
    kb = KnowledgeBase()
    raw_data = kb.get_analyzed_questions(current_subject)
    if not raw_data:
        console.print("[red]No analyzed questions found. Use 'ingest-paper' first.[/red]")
        return
        
    questions = [AnalyzedQuestion(**q) for q in raw_data]
    
    # Filter
    if module:
        questions = [q for q in questions if q.module and module.lower() in q.module.lower()]
        
    if not questions:
        console.print("[yellow]No questions found for criteria.[/yellow]")
        return
        
    # Initialize Analyzer for generation
    load_dotenv()
    analyzer = QuestionPaperAnalyzer(os.getenv("GOOGLE_API_KEY"))
    
    # Process
    # Load syllabus to get correct module names
    with open(f"{subject_path}/syllabus/syllabus.json", 'r') as f:
        syllabus = json.load(f)
    
    # Initialize map with syllabus modules
    module_questions_map = {mod['name']: [] for mod in syllabus['modules']}
    
    # Assign questions to modules
    for q in questions:
        # 1. Try exact match
        if q.module in module_questions_map:
            module_questions_map[q.module].append(q)
            continue
            
        # 2. Try fuzzy match (case insensitive)
        found = False
        for mod_name in module_questions_map.keys():
            if mod_name.lower() == q.module.lower():
                module_questions_map[mod_name].append(q)
                found = True
                break
        if found: continue

        # 3. Fallback: Check if q.module is a substring or vice versa
        for mod_name in module_questions_map.keys():
            if mod_name.lower() in q.module.lower() or q.module.lower() in mod_name.lower():
                module_questions_map[mod_name].append(q)
                found = True
                break
        
        if not found:
            console.print(f"[yellow]Warning: Could not map question (Mod: {q.module}) to any syllabus module.[/yellow]")

    base_dir = subject_path / "notes"

    for mod_name, qs in module_questions_map.items():
        if not qs: continue
        
        # Find module directory
        # 1. Precise lookup (matching save_syllabus_to_markdown logic)
        safe_mod_name = mod_name.replace(":", " -").replace("/", "-").strip()
        found_dir = base_dir / safe_mod_name
        
        # 2. Fallback: Fuzzy search
        if not found_dir.exists():
            found_dir = None
            for p in base_dir.iterdir():
                if p.is_dir() and mod_name.lower() in p.name.lower():
                    found_dir = p
                    break
        
        if not found_dir or not found_dir.exists():
            console.print(f"[yellow]Could not find folder for module '{mod_name}'[/yellow]")
            continue
            
        output_file = found_dir / "PYQ_Solutions.md"
        
        console.print(f"[cyan]Generating answers for {mod_name} ({len(qs)} questions)...[/cyan]")
        
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"\n# Previous Year Questions & Solutions\n")
            f.write(f"Generated on {os.getenv('DATE', 'Today')}\n\n")
            
            for i, q in enumerate(qs, 1):
                console.print(f"  [dim]Generating Q{q.number}...[/dim]")
                ans = analyzer.generate_answer(q) 
                f.write(f"### Q{q.number} ({q.year}): {q.text}\n")
                f.write(f"**Marks:** {q.marks}\n\n")
                f.write(f"{ans}\n\n")
                f.write("---\n")
                
                # Rate limit throttle: sleep 15s to respect 5 RPM
                time.sleep(15)
                
        console.print(f"[green]Saved solutions to {output_file}[/green]")

@app.command()
def help():
    """Show aesthetic help and workflow information."""
    from rich.panel import Panel
    from rich.text import Text
    from rich.align import Align
    
    # Header
    title = Text.assemble(
        ("🧠 ", "magenta"),
        ("AI Learning Engine ", "bold cyan"),
        ("v2.0", "dim white")
    )
    console.print("\n", Align.center(title))
    
    # Workflow Panel
    workflow_steps = [
        "[bold yellow]1. Setup:[/bold yellow]      [green]init[/green] -> [green]set-api-key[/green]",
        "[bold yellow]2. Create:[/bold yellow]     [green]create-subject[/green] (AI extracts modules, topics & creates markdown notes)",
        "[bold yellow]3. Prioritize:[/bold yellow] [green]ingest-paper[/green] (Analyze importance from previous year papers)",
        "[bold yellow]4. Study:[/bold yellow]      [green]save-notes[/green] (Generate MD) -> Review in [dim]data/subjects/<subj>/notes[/dim]",
        "[bold yellow]5. Deepen:[/bold yellow]     [green]ask-youtube[/green], [green]quiz-youtube[/green], [green]create-mnemonic[/green]",
        "[bold yellow]6. Visualize:[/bold yellow]  [green]generate-mindmap-v2[/green] (Mermaid), [green]run-web[/green] (Explorer)"
    ]
    
    workflow_panel = Panel(
        "\n".join(workflow_steps),
        title="[bold white]🚀 Recommended Study Workflow[/bold white]",
        border_style="bright_blue",
        padding=(1, 2)
    )
    console.print(workflow_panel)

    # Command Groups Table
    table = Table(show_header=True, header_style="bold magenta", box=None, expand=True)
    table.add_column("Category", style="cyan", width=15)
    table.add_column("Commands", style="white")

    table.add_row("📁 Subjects", "create-subject, list-subjects, select-subject, delete-subject")
    table.add_row("📝 Content", "configure-exam, save-notes, add-topic, list-topics, load-syllabus, export-syllabus")
    table.add_row("📺 YouTube", "ask-youtube, quiz-youtube")
    table.add_row("🧠 Study", "add-question, list-questions, create-mnemonic, show-difference, ingest-paper, get-pyq-answers")
    table.add_row("🎨 Visuals", "generate-mindmap, generate-mindmap-v2, create-animation")
    table.add_row("🎮 Gamification", "pomodoro, progress")
    table.add_row("✅ Tasks", "todo-add, todo-list, todo-complete")
    table.add_row("🎴 Flashcards", "flashcard-create-deck, flashcard-add, flashcard-study")
    table.add_row("⚙️ System", "backup-list, backup-restore, init, run-web, stop-web, set-api-key, exit")

    console.print(table)
    
    # Current Context
    current = _get_current_subject()
    status = f"[bold green]Active Subject:[/bold green] {current}" if current else "[bold red]No subject selected (use select-subject)[/bold red]"
    console.print(Panel(status, border_style="dim"))
    console.print(" [dim]Type 'exit' to quit.[/dim]\n")

@app.command()
def generate_mindmap_v2(
    scope: str = typer.Option("subject", help="Scope: 'subject' (all topics in current subject) or 'global'"),
    output_file: str = "mindmap.mmd"
):
    """
    Generate Mermaid mindmaps.
    If scope is 'subject', generates <topic>_mermaid.md for each topic in the current subject.
    If scope is 'global', generates a single mindmap for all topics.
    """
    kb = KnowledgeBase()
    
    if scope == "global":
        topics = kb.get_topics()
        if not topics:
            console.print("[yellow]No topics found.[/yellow]")
            return
        try:
            generator = MindMapGenerator2(topics)
            output_path = generator.save(output_file)
            console.print(f"[bold green]Global Mermaid mind map generated at: {output_path}[/bold green]")
        except Exception as e:
            console.print(f"[red]Failed to generate mind map: {e}[/red]")
        return

    # Subject Scope
    current_subject = _get_current_subject()
    if not current_subject:
        console.print("[red]No subject selected. Use 'select-subject' first.[/red]")
        return

    subjects_file = "data/subjects/subjects.json"
    with open(subjects_file, 'r') as f:
        subjects = json.load(f)
    subject_data = next((s for s in subjects if s["name"] == current_subject), None)
    
    if not subject_data: return

    syllabus_path = subject_data.get("syllabus_path")
    syllabus = load_syllabus_from_json(syllabus_path)
    
    count = 0
    with console.status(f"[cyan]Generating mindmaps for {current_subject}...[/cyan]"):
        base_dir = Path(subject_data['folder_path']) / "notes"
        
        for i, module in enumerate(syllabus.modules, 1):
            safe_mod_name = module.name.replace(":", " -").replace("/", "-").strip()
            
            for j, topic in enumerate(module.topics, 1):
                safe_topic_name = topic.name.replace("/", "-").strip()
                safe_topic_name = "".join([c for c in safe_topic_name if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).strip()
                
                # Construct path
                file_path = base_dir / safe_mod_name / f"{j}. {safe_topic_name}_mermaid.md"
                
                # Generate
                # Create a single-topic generator for focused map
                # or pass relevant connected topics? For now, just the topic itself.
                # Actually MindMapGenerator2 takes a list.
                generator = MindMapGenerator2([topic])
                generator.save_as_markdown(str(file_path), title=f"Mindmap: {topic.name}")
                count += 1
                
    console.print(f"[bold green]Generated {count} mindmaps in {base_dir}[/bold green]")

@app.command()
def save_notes(output_file: Optional[str] = None):
    """
    Save the current subject's syllabus as Markdown notes.
    """
    current_subject = _get_current_subject()
    if not current_subject:
        console.print("[red]No subject selected. Use 'select-subject' first.[/red]")
        return

    # Find subject details to get syllabus
    subjects_file = "data/subjects/subjects.json"
    if not Path(subjects_file).exists():
        console.print("[red]Subjects metadata not found.[/red]")
        return
        
    with open(subjects_file, 'r') as f:
        subjects = json.load(f)
        
    subject_data = next((s for s in subjects if s["name"] == current_subject), None)
    if not subject_data:
        console.print(f"[red]Subject '{current_subject}' data not found.[/red]")
        return

    syllabus_path = subject_data.get("syllabus_path")
    if not syllabus_path or not Path(syllabus_path).exists():
        console.print(f"[red]Syllabus file not found at {syllabus_path}[/red]")
        return

    try:
        syllabus = load_syllabus_from_json(syllabus_path)
        
        if not output_file:
            output_file = f"{subject_data['folder_path']}/notes.md"
            
        save_syllabus_to_markdown(syllabus, output_file)
        console.print(f"[bold green]Notes saved to: {output_file}[/bold green]")
    except Exception as e:
        console.print(f"[red]Error saving notes: {e}[/red]")

@app.command()
def set_api_key(api_key: str):
    """Set the Google API key for Gemini AI."""
    Path(".env").touch(exist_ok=True)
    with open(".env", "a") as f:
        f.write(f"GOOGLE_API_KEY={api_key}\n")
    console.print("[green]API key set successfully![/green]")

@app.command()
def gemini_init():
    """Initialize Gemini AI integration."""
    global client
    load_dotenv()
    try:
        api_key = os.environ["GOOGLE_API_KEY"]
    except KeyError:
        console.print("[red]Error: GOOGLE_API_KEY not set in environment variables.[/red]")
        console.print("[yellow]Please set the API key using set-api-key command or in a .env file.[/yellow]")
        raise typer.Exit(1)
    client = genai.Client()

    # genai.configure(api_key=api_key)
    # model = genai.GenerativeModel('gemini-2.5-flash')

    console.print("[green]Gemini AI integration initialized[/green]")
    #return model
    return client

@app.command()
def ask_youtube(
    url: str = typer.Argument(..., help="YouTube video URL"),
    topic: Optional[str] = typer.Argument(None, help="Topic name to link this video to"),
    query: Optional[str] = typer.Argument(None, help="Question to ask (optional, triggers Q&A mode)"),
):
    """
    Analyze a YouTube video.
    If 'topic' is provided, generates Notes & Mindmap for that topic.
    If 'query' is provided, answers the question using RAG.
    """
    _init_gemini_model() # Ensure env vars are loaded
    rag = RAGEngine()
    
    if query:
        # Q&A Mode
        console.print(f"[cyan]Processing video: {url}[/cyan]")
        console.print("[yellow]This may take a moment (launching browser to fetch subs)...[/yellow]")
        answer = rag.ask_youtube(url, query)
        console.print("\n[bold green]Answer:[/bold green]")
        console.print(answer)
        return

    # Learning Workflow Mode
    current_subject = _get_current_subject()
    if not current_subject:
        console.print("[red]No subject selected. Please select a subject first.[/red]")
        return

    # Resolve Topic
    if not topic:
        # List topics and ask user to choose?
        # For CLI conciseness, we'll ask for the argument.
        console.print("[yellow]Please provide a topic name using --topic to generate notes/mindmaps.[/yellow]")
        # TODO: Interactive selection could be added here
        return

    console.print(f"[cyan]Analyzing video for topic '{topic}' in subject '{current_subject}'...[/cyan]")
    
    # Analyze Video
    result = rag.analyze_video_structure(url, topic)
    
    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return

    # Find where to save
    module_name, topic_path_prefix = _find_topic_path(current_subject, topic)
    if not topic_path_prefix:
        console.print(f"[red]Topic '{topic}' not found in current subject's syllabus.[/red]")
        # Fallback to a general 'Inbox' or similar? For now, abort.
        return

    # Save Notes
    notes_file = f"{topic_path_prefix}.md"
    
    # Append to existing or create new? 
    # Current flow implies overwriting or creating. Let's append if exists or create.
    # Actually, let's create a dedicated video note or append to the main topic note.
    # User said "generate notes...".
    
    # Let's append a "Video Notes" section to the main topic file
    try:
        with open(notes_file, "a", encoding="utf-8") as f:
            f.write(f"\n\n# Video Notes: {result.get('summary', 'YouTube Video')}\n")
            f.write(f"**Source:** {url}\n\n")
            f.write(result.get('detailed_notes', ''))
            
            if result.get('differences'):
                f.write("\n## Differences & Comparisons\n")
                for diff in result['differences']:
                    f.write(f"### {diff.get('concept_a')} vs {diff.get('concept_b')}\n")
                    f.write(f"{diff.get('explanation')}\n")
        
        console.print(f"[green]Notes updated in: {notes_file}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to save notes: {e}[/red]")

    # Save Mindmap
    if result.get('mindmap_mermaid'):
        mermaid_file = f"{topic_path_prefix}_mermaid.md"
        try:
            with open(mermaid_file, "w", encoding="utf-8") as f:
                f.write(f"# Mindmap: {topic}\n\n")
                f.write(f"```mermaid\n{result['mindmap_mermaid']}\n```\n")
            console.print(f"[green]Mindmap saved to: {mermaid_file}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to save mindmap: {e}[/red]")

def _find_topic_path(subject_name: str, topic_name: str) -> tuple[Optional[str], Optional[str]]:
    """
    Finds the module name and full path prefix (without extension) for a topic.
    Returns (module_name, path_prefix)
    """
    subjects_file = "data/subjects/subjects.json"
    if not Path(subjects_file).exists():
        return None, None
        
    with open(subjects_file, 'r') as f:
        subjects = json.load(f)
        
    subject_data = next((s for s in subjects if s["name"] == subject_name), None)
    if not subject_data:
        return None, None

    syllabus_path = subject_data.get("syllabus_path")
    if not syllabus_path or not Path(syllabus_path).exists():
        return None, None
        
    syllabus = load_syllabus_from_json(syllabus_path)
    
    # Locate topic
    base_dir = Path(subject_data['folder_path']) / "notes"
    
    for i, module in enumerate(syllabus.modules, 1):
        for j, t in enumerate(module.topics, 1):
            if t.name.lower() == topic_name.lower():
                # Reconstruct path logic from save_syllabus_to_markdown
                safe_mod_name = module.name.replace(":", " -").replace("/", "-").strip()
                safe_topic_name = t.name.replace("/", "-").strip()
                safe_topic_name = "".join([c for c in safe_topic_name if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).strip()
                
                full_path_prefix = base_dir / safe_mod_name / f"{j}. {safe_topic_name}"
                return module.name, str(full_path_prefix)
                
    return None, None

@app.command()
def quiz_youtube(
    url: str = typer.Argument(..., help="YouTube video URL"),
    num: int = typer.Option(5, help="Number of questions to generate"),
    save: bool = typer.Option(True, "--save", help="Save questions to knowledge base"),
):
    """
    Generate a quiz from a YouTube video.
    """
    _init_gemini_model()
    rag = RAGEngine()
    console.print(f"[cyan]Generating {num} questions from: {url}[/cyan]")
    console.print("[yellow]Fetching content and generating quiz...[/yellow]")
    
    questions = rag.generate_quiz_from_video(url, num)
    
    if not questions:
        console.print("[red]Failed to generate questions.[/red]")
        return
        
    kb = KnowledgeBase()
    
    for i, q in enumerate(questions, 1):
        console.print(f"\n[bold]Q{i}: {q.question}[/bold]")
        for opt in q.options:
            console.print(f" - {opt}")
        console.print(f"[green]Answer: {q.answer}[/green]")
        
        if save:
            q.topic = f"YouTube: {url}" # Or a better identifier
            kb.save_question(q)
            
    if save:
        console.print(f"\n[green]Saved {len(questions)} questions to knowledge base.[/green]")


def _init_gemini_model():
    """Internal function to initialize Gemini model without CLI context."""
    load_dotenv()
    try:
        api_key = os.environ["GOOGLE_API_KEY"]
    except KeyError:
        console.print("[red]Error: GOOGLE_API_KEY not set in environment variables.[/red]")
        console.print("[yellow]Please set the API key using set-api-key command or in a .env file.[/yellow]")
        raise typer.Exit(1)
    # genai.configure(api_key=api_key)
    # return genai.GenerativeModel('gemini-2.5-flash')
    return genai.Client()


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
    global client
    if not client:
        client = _init_gemini_model()
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
            os_type = platform.system()
            if os_type == "Windows":
                end_hint = "Ctrl+Z then Enter"
            else:
                end_hint = "Ctrl+D"
            sys.stdout.write(f"[yellow]Enter syllabus text ({end_hint} to finish):[/yellow]\n")
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
    console.print("[cyan]Processing syllabus with Gemini (extracting Modules & Topics)...[/cyan]")
    processor = GeminiProcessor(model)
    syllabus = processor.process_syllabus_text(syllabus_text, subject_name)
    
    if qbank_path:
        syllabus.question_bank_path = qbank_path
    
    # Create Subject Folder Structure
    # Folder already created above, but let's ensure subfolders
    
    # Save syllabus JSON
    syllabus_path = f"{subject_folder}/syllabus/syllabus.json"
    save_syllabus_to_json(syllabus, syllabus_path)
    console.print(f"[green]Syllabus JSON saved: {syllabus_path}[/green]")
    
    # Save markdown notes structure
    notes_dir = f"{subject_folder}/notes"
    save_syllabus_to_markdown(syllabus, notes_dir)
    console.print(f"[green]Markdown notes structure created at: {notes_dir}[/green]")
    
    # Save topics to Knowledge Base
    kb = KnowledgeBase()
    topic_count = 0
    for module in syllabus.modules:
        for topic in module.topics:
            topic.module_id = module.id
            # topic.module_name = module.name # If we add this field for convenience
            kb.save_topic(topic)
            topic_count += 1
            
    console.print(f"[cyan]Extracted {len(syllabus.modules)} modules and {topic_count} topics[/cyan]")

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
            try:
                subjects = json.load(f)
            except json.JSONDecodeError:
                subjects = []

    existing_subject = next((s for s in subjects if s['name'] == subject_name), None)
    if existing_subject:
        # Update existing
        existing_subject.update({
             "folder_path": subject_folder,
             "syllabus_path": syllabus_path,
             "question_bank_path": qbank_path,
        })
    else:
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
    
    # Set as current subject
    _set_current_subject(subject_name)
    console.print(f"[yellow]Set '{subject_name}' as current subject[/yellow]")



@app.command()
def create_module(
    name: str = typer.Argument(..., help="Module name"),
    description: str = typer.Option("", help="Module description")
):
    """
    Add a manual module to the current subject.
    """
    current_subject = _get_current_subject()
    # Implementation logic to load syllabus.json, add module, save back, recreate notes structure
    console.print(f"[yellow]Adding module '{name}' to {current_subject}... (TODO: Implement persistence update)[/yellow]")



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
    current_subject = _get_current_subject()
    
    # Try to resolve module from the syllabus if subject is selected
    module_name = None
    if current_subject:
        resolved_module, _ = _find_topic_path(current_subject, topic)
        module_name = resolved_module

    q = Question(
        topic=topic,
        subject=current_subject,
        module=module_name,
        question=question,
        answer=answer,
        difficulty=difficulty
    )
    
    kb.save_question(q)
    
    msg = f"[green]Question added for topic '{topic}'"
    if current_subject:
        msg += f" in subject '{current_subject}'"
    if module_name:
        msg += f" ({module_name})"
    msg += "![/green]"
    
    console.print(msg)


@app.command()
def list_questions(
    topic: Optional[str] = typer.Option(None, "--topic", "-t", help="Filter by topic"),
    module: Optional[str] = typer.Option(None, "--module", "-m", help="Filter by module"),
    all_subjects: bool = typer.Option(False, "--all", help="Show questions from all subjects")
):
    """List questions from both knowledge base and subject-specific question bank."""
    kb = KnowledgeBase()
    current_subject = _get_current_subject()
    
    # Target subject for filtering
    target_subject = None if all_subjects else current_subject

    # Source 1: Manual questions from SQLite
    manual_questions = kb.get_questions(topic=topic, subject=target_subject, module=module)
    
    # Source 2: Analyzed questions from JSON bank
    analyzed_questions = []
    
    def normalize_mod(m):
        if not m: return ""
        m = str(m).lower().strip()
        if m.startswith("module "):
            m = m[7:].strip()
        return m

    norm_module = normalize_mod(module) if module else None

    if target_subject:
        # Fetch for current subject
        raw_analyzed = kb.get_analyzed_questions(target_subject)
        for q_dict in raw_analyzed:
            q_module = q_dict.get("module")
            q_topic = q_dict.get("topic")
            
            # Normalize q_module for matching
            norm_q_mod = normalize_mod(q_module)
            
            # Apply filters
            if topic and q_topic and topic.lower() not in q_topic.lower():
                continue
            if norm_module and norm_q_mod and norm_module != norm_q_mod:
                continue
            
            analyzed_questions.append({
                "source": "Bank",
                "subject": target_subject,
                "module": q_module or "N/A",
                "topic": q_topic or "N/A",
                "question": q_dict.get("text", "N/A"),
                "difficulty": f"Marks: {q_dict.get('marks', '?')}" if q_dict.get('marks') else "N/A"
            })
    elif all_subjects:
        # Fetch for all subjects
        subjects_file = "data/subjects/subjects.json"
        if Path(subjects_file).exists():
            with open(subjects_file, 'r') as f:
                subjects = json.load(f)
                for s in subjects:
                    s_name = s["name"]
                    raw_analyzed = kb.get_analyzed_questions(s_name)
                    for q_dict in raw_analyzed:
                        q_module = q_dict.get("module")
                        q_topic = q_dict.get("topic")
                        
                        norm_q_mod = normalize_mod(q_module)
                        
                        if topic and q_topic and topic.lower() not in q_topic.lower():
                            continue
                        if norm_module and norm_q_mod and norm_module != norm_q_mod:
                            continue
                            
                        analyzed_questions.append({
                            "source": "Bank",
                            "subject": s_name,
                            "module": q_module or "N/A",
                            "topic": q_topic or "N/A",
                            "question": q_dict.get("text", "N/A"),
                            "difficulty": f"Marks: {q_dict.get('marks', '?')}" if q_dict.get('marks') else "N/A"
                        })

    # Combine and convert manual questions to the same display format
    for q in manual_questions:
        q_module = q.module
        q_topic = q.topic
        
        norm_q_mod = normalize_mod(q_module)
        
        # Apply module filter if not already filtered by kb.get_questions (which might be too strict)
        if norm_module and norm_q_mod and norm_module != norm_q_mod:
            continue

        analyzed_questions.append({
            "source": "Manual",
            "subject": q.subject or "N/A",
            "module": q_module or "N/A",
            "topic": q_topic or "N/A",
            "question": q.question,
            "difficulty": q.difficulty
        })

    display_list = analyzed_questions
    
    if not display_list:
        console.print("[yellow]No questions found.[/yellow]")
        return
    
    title = "Questions"
    if topic: title += f" for '{topic}'"
    if module: title += f" in module '{module}'"
    if target_subject: title += f" of subject '{target_subject}'"
    
    table = Table(title=title)
    table.add_column("Src", style="dim")
    table.add_column("Subject", style="blue")
    table.add_column("Module", style="magenta")
    table.add_column("Topic", style="cyan")
    table.add_column("Question", style="green")
    table.add_column("Meta", style="yellow")
    
    for q in display_list:
        table.add_row(
            q["source"],
            q["subject"],
            q["module"],
            q["topic"],
            q["question"][:60] + "..." if len(q["question"]) > 60 else q["question"],
            q["difficulty"]
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
        # Use 'start' (Windows) or 'open' (Mac) to launch in new window
        if platform.system() == "Windows":
             web_proc = subprocess.Popen("start streamlit run streamlit/app.py", shell=True)
        else:
             web_proc = subprocess.Popen(["streamlit", "run", "streamlit/app.py"], start_new_session=True)
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
def pomodoro(
    duration: int = typer.Option(25, "--duration", "-d", help="Duration in minutes"),
    subject: str = typer.Option(None, "--subject", "-s", help="Subject to focus on")
):
    """Start a Pomodoro focus session."""
    timer = PomodoroTimer()
    
    # Check if a session is already running
    if timer.current_session and timer.current_session.end_time > datetime.now():
        remaining = int((timer.current_session.end_time - datetime.now()).total_seconds() / 60)
        console.print(f"[yellow]Session already running! {remaining}m remaining.[/yellow]")
        if not typer.confirm("Stop current session and start new one?"):
            return
        timer.current_session = None

    if not subject:
        # Try to get from global context
        try:
             with open("data/.current_subject", "r") as f:
                 subject = f.read().strip()
        except:
             subject = "General"

    console.print(f"[bold green]🍅 Starting {duration}m focus session for '{subject}'...[/bold green]")
    timer.start_session(duration, subject)
    
    # Simple countdown
    try:
        total_seconds = duration * 60
        with typer.progressbar(range(total_seconds), label="Focusing...") as progress:
            for _ in progress:
                time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Session paused/cancelled.[/yellow]")
        return

    # Finish
    console.print("\n[bold green]⏰ Session Complete![/bold green]")
    notes = typer.prompt("Session notes (optional)", default="")
    session = timer.complete_session(notes)
    
    # Show rewards
    console.print(f"[cyan]Logged! Earned {session.xp_earned} XP[/cyan]")
    
    # Show stats
    stats = timer.get_stats()
    console.print(f"Today: {stats['daily_count']} sessions ({stats['daily_minutes']}m)")


@app.command(name="progress")
def show_progress():
    """Show detailed progress and stats."""
    gm = GamificationManager()
    progress = gm._load_progress()
    
    table = Table(title="🏆 User Progress 🏆")
    table.add_column("Level", style="cyan")
    table.add_column("XP", style="green")
    table.add_column("Streak", style="magenta")
    
    table.add_row(str(progress.current_level), f"{progress.total_points}/{progress.points_to_next_level}", f"{progress.current_streak} days 🔥")
    console.print(table)
    
    # Achievements
    if progress.achievements:
        console.print("\n[bold]Unlocked Achievements:[/bold]")
        for a in progress.achievements:
            console.print(f"🏅 {a.name}: {a.description}")

@app.command(name="todo-add")
def todo_add(
    title: str = typer.Argument(..., help="Task title"),
    description: str = typer.Option("", "--desc", help="Task description"),
    priority: str = typer.Option("medium", "--priority", "-p", help="Priority (low/medium/high)"),
    due: str = typer.Option(None, "--due", help="Due date (YYYY-MM-DD)")
):
    """Add a new task."""
    tm = TodoManager()
    
    # Context
    subject = None
    try:
         with open("data/.current_subject", "r") as f:
             subject = f.read().strip()
    except: pass
    
    due_date = None
    if due:
        try:
             due_date = datetime.strptime(due, "%Y-%m-%d")
        except:
             console.print("[red]Invalid date format. Use YYYY-MM-DD[/red]")
             return

    item = tm.add_todo(title, description, priority, subject, due_date)
    console.print(f"[green]Task added! ID: {item.id}[/green]")

@app.command(name="todo-list")
def todo_list(
    status: str = typer.Option("pending", "--status", help="Filter by status (pending/done/all)")
):
    """List tasks."""
    tm = TodoManager()
    subject = None
    try:
         with open("data/.current_subject", "r") as f:
             subject = f.read().strip()
    except: pass
    
    todos = tm.get_todos(status=status if status != "all" else None, subject=subject)
    
    if not todos:
        console.print("[yellow]No tasks found.[/yellow]")
        return
        
    table = Table(title=f"Tasks ({status})")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Priority", style="magenta")
    table.add_column("Due", style="green")
    
    for t in todos:
        p_style = "red" if t.priority=="high" else "yellow" if t.priority=="medium" else "blue"
        due_str = t.due_date.strftime("%Y-%m-%d") if t.due_date else "-"
        table.add_row(t.id, t.title, f"[{p_style}]{t.priority}[/{p_style}]", due_str)
        
    console.print(table)

@app.command(name="todo-complete")
def todo_complete(task_id: str = typer.Argument(..., help="Task ID")):
    """Complete a task."""
    tm = TodoManager()
    
    # Find task to verify
    # (Optional verify) but tm.complete handles it
    
    item = tm.complete_todo(task_id)
    if item:
        console.print(f"[green]Task '{item.title}' completed! +XP earned[/green]")
    else:
        console.print(f"[red]Task ID {task_id} not found.[/red]")

@app.command(name="flashcard-create-deck")
def flashcard_create_deck(name: str = typer.Argument(..., help="Deck name")):
    """Create a new flashcard deck."""
    fm = FlashcardManager()
    subject = None
    try:
         with open("data/.current_subject", "r") as f:
             subject = f.read().strip()
    except: pass
    
    deck = fm.create_deck(name, subject)
    console.print(f"[green]Deck '{deck.name}' created![/green]")

@app.command(name="flashcard-add")
def flashcard_add(
    deck_name: str = typer.Argument(..., help="Deck name (fuzzy match)"),
    front: str = typer.Argument(..., help="Front text"),
    back: str = typer.Argument(..., help="Back text")
):
    """Add a card to a deck."""
    fm = FlashcardManager()
    decks = fm.list_decks()
    
    # Simple fuzzy search
    target = None
    for d in decks:
        if deck_name.lower() in d.name.lower():
            target = d
            break
            
    if not target:
        console.print(f"[red]Deck matching '{deck_name}' not found.[/red]")
        return
        
    fm.add_card(target.id, front, back)
    console.print(f"[green]Card added to '{target.name}'![/green]")

@app.command(name="flashcard-study")
def flashcard_study(deck_name: str = typer.Argument(..., help="Deck name")):
    """Interactive study session."""
    fm = FlashcardManager()
    decks = fm.list_decks()
    target = None
    for d in decks:
        if deck_name.lower() in d.name.lower():
            target = d
            break
            
    if not target:
        console.print(f"[red]Deck not found.[/red]")
        return
        
    cards = fm.get_cards_for_review(target.id)
    if not cards:
         console.print("[green]No cards due for review! Great job![/green]")
         return
         
    console.print(f"Studying {len(cards)} cards from '{target.name}'...")
    
    for card in cards:
        console.print(f"\n[bold cyan]Front:[/bold cyan] {card.front}")
        typer.prompt("Press Enter to flip...")
        console.print(f"[bold magenta]Back:[/bold magenta] {card.back}")
        
        rating = typer.prompt("Quality (0=Fail, 3=Pass, 5=Perfect)", type=int)
        # Map simple 0-5 to SM-2 0-5
        fm.review_card(target.id, card.id, rating)
    
    console.print("\n[green]Session complete![/green]")


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
@app.command(name="backup-list")
def backup_list(
    file_path: str = typer.Option(..., "--file", "-f", help="Path to the file to check backups for")
):
    """
    List available backups for a specific file.
    """
    from core.persistence import get_persistence_manager
    pm = get_persistence_manager()
    backups = pm.list_backups(file_path)
    
    if not backups:
        console.print(f"[yellow]No backups found for {file_path}[/yellow]")
        return
        
    table = Table(title=f"Backups for {Path(file_path).name}")
    table.add_column("Index", style="cyan")
    table.add_column("Timestamp", style="green")
    table.add_column("Filename", style="magenta")
    
    for i, backup in enumerate(backups):
        try:
            # Extract timestamp from filename pattern: *_YYYYMMDD_HHMMSS.ext
            ts_part = backup.stem.split('_')[-2:]
            timestamp = f"{ts_part[0]} {ts_part[1][:2]}:{ts_part[1][2:4]}:{ts_part[1][4:]}"
        except:
            timestamp = "Unknown"
            
        table.add_row(str(i), timestamp, backup.name)
        
    console.print(table)


@app.command(name="backup-restore")
def backup_restore(
    file_path: str = typer.Option(..., "--file", "-f", help="Original file path"),
    backup_index: int = typer.Option(None, "--index", "-i", help="Index of backup to restore (0 is newest)"),
    backup_name: str = typer.Option(None, "--name", "-n", help="Exact filename of backup to restore")
):
    """
    Restore a file from a backup.
    """
    if backup_index is None and backup_name is None:
        console.print("[red]Error: Must provide either --index or --name[/red]")
        return
        
    from core.persistence import get_persistence_manager
    pm = get_persistence_manager()
    backups = pm.list_backups(file_path)
    
    if not backups:
        console.print(f"[red]No backups found for {file_path}[/red]")
        return
        
    target_backup = None
    if backup_name:
        for b in backups:
            if b.name == backup_name:
                target_backup = b
                break
        if not target_backup:
            console.print(f"[red]Backup '{backup_name}' not found[/red]")
            return
    else:
        if backup_index < 0 or backup_index >= len(backups):
            console.print(f"[red]Invalid index {backup_index}. Max index is {len(backups)-1}[/red]")
            return
        target_backup = backups[backup_index]
        
    if typer.confirm(f"Restore {target_backup.name} to {file_path}? This will overwrite current content."):
        success, error = pm.restore_from_backup(file_path, target_backup)
        if success:
            console.print(f"[green]Successfully restored backup to {file_path}[/green]")
        else:
            console.print(f"[red]Restore failed: {error}[/red]")


def interactive_mode():
    """Run the CLI in interactive mode."""
    # Show help at startup
    console.print("[bold cyan]AI Learning Engine CLI[/bold cyan]")
    try:
        app(["--help"], standalone_mode=False)
    except SystemExit:
        pass
    except Exception:
        pass

    console.print("\nType 'exit' to quit.\n")
    
    while True:
        try:
            user_input = typer.prompt("\n(cli) >>>", prompt_suffix=" ")
            if user_input.lower() in ("exit", "quit"):
                console.print("[cyan]Goodbye![/cyan]")
                break
            
            # Split command into parts
            try:
                args = shlex.split(user_input.strip())
            except ValueError:
                console.print("[red]Error: mismatched quotes[/red]")
                continue
                
            if not args:
                continue

            try:
                # Invoke the app directly for speed
                # standalone_mode=False prevents SystemExit on error/help
                app(args, standalone_mode=False)
            except SystemExit:
                pass
            except Exception as e:
                console.print(f"[red]Error executing command: {e}[/red]")
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            continue
        except EOFError:
            break

if __name__ == "__main__":
    if len(sys.argv) > 1:
        app()
    else:
        interactive_mode()
