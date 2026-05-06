"""
Cheatsheet generator with intelligent chunking for token limit management.
Uses Gemini to extract key points from notes.
"""
from pathlib import Path
from typing import List, Optional, Dict
import json
import os
from dotenv import load_dotenv
import google.genai as genai
from core.models import Cheatsheet, CheatsheetSection
from core.utils import get_subject_dir


class CheatsheetGenerator:
    """
    Generates quick revision cheatsheets from markdown notes with chunking.
    Processes each note file separately to avoid token limits.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        load_dotenv()
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key not found")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.0-flash-exp"
    
    def generate_from_module(self, subject: str, module: str, 
                            save_path: Optional[str] = None) -> Cheatsheet:
        """
        Generate cheatsheet for an entire module by processing each topic's notes separately.
        
        Args:
            subject: Subject name
            module: Module name
            save_path: Optional path to save the cheatsheet
        """
        subject_dir = get_subject_dir(subject)
        notes_dir = subject_dir / "notes" / module
        
        if not notes_dir.exists():
            raise ValueError(f"Module notes directory not found: {notes_dir}")
        
        # Find all markdown notes (excluding special files)
        note_files = [
            f for f in notes_dir.glob("*.md")
            if not f.name.endswith("_mermaid.md") 
            and f.name != "PYQ_Solutions.md"
        ]
        
        if not note_files:
            raise ValueError(f"No note files found in {notes_dir}")
        
        print(f"📚 Processing {len(note_files)} note files...")
        
        # Process each file separately to avoid token limits
        all_formulas = []
        all_definitions = []
        all_algorithms = []
        all_diagrams = []
        all_tips = []
        all_mistakes = []
        sections = []
        
        for idx, note_file in enumerate(note_files, 1):
            print(f"  [{idx}/{len(note_files)}] Processing {note_file.name}...")
            
            try:
                content = note_file.read_text(encoding='utf-8')
                
                # Extract key points from this file
                result = self._extract_key_points(content, note_file.stem)
                
                # Aggregate results
                all_formulas.extend(result.get('formulas', []))
                all_definitions.extend(result.get('definitions', []))
                all_algorithms.extend(result.get('algorithms', []))
                all_diagrams.extend(result.get('diagrams', []))
                all_tips.extend(result.get('tips', []))
                all_mistakes.extend(result.get('mistakes', []))
                
                # Create section for this topic
                if result.get('key_points'):
                    sections.append(CheatsheetSection(
                        title=note_file.stem,
                        content_type='key_points',
                        items=result['key_points']
                    ))
                
            except Exception as e:
                print(f"  ⚠️ Error processing {note_file.name}: {e}")
                continue
        
        # Create cheatsheet
        cheatsheet = Cheatsheet(
            title=f"{module} - Quick Reference",
            subject=subject,
            module=module,
            sections=sections,
            key_formulas=all_formulas[:20],  # Limit to top 20
            key_definitions=all_definitions[:20],
            key_algorithms=all_algorithms[:10],
            important_diagrams=all_diagrams[:10],
            quick_tips=all_tips[:15],
            common_mistakes=all_mistakes[:10],
            source_notes=[str(f) for f in note_files]
        )
        
        # Save if path provided
        if save_path:
            self._save_cheatsheet(cheatsheet, save_path)
        
        return cheatsheet
    
    def generate_from_topic(self, subject: str, module: str, topic: str,
                           save_path: Optional[str] = None) -> Cheatsheet:
        """
        Generate cheatsheet for a single topic.
        """
        subject_dir = get_subject_dir(subject)
        notes_dir = subject_dir / "notes" / module
        
        # Find topic file (may have numbering like "1. Topic Name.md")
        topic_files = [f for f in notes_dir.glob("*.md") 
                      if topic.lower() in f.stem.lower() 
                      and not f.name.endswith("_mermaid.md")]
        
        if not topic_files:
            raise ValueError(f"Topic note file not found for: {topic}")
        
        note_file = topic_files[0]
        content = note_file.read_text(encoding='utf-8')
        
        # Extract key points
        result = self._extract_key_points(content, topic)
        
        # Create cheatsheet
        cheatsheet = Cheatsheet(
            title=f"{topic} - Quick Reference",
            subject=subject,
            module=module,
            topic=topic,
            key_formulas=result.get('formulas', []),
            key_definitions=result.get('definitions', []),
            key_algorithms=result.get('algorithms', []),
            important_diagrams=result.get('diagrams', []),
            quick_tips=result.get('tips', []),
            common_mistakes=result.get('mistakes', []),
            source_notes=[str(note_file)]
        )
        
        if result.get('key_points'):
            cheatsheet.sections.append(CheatsheetSection(
                title="Key Concepts",
                content_type='key_points',
                items=result['key_points']
            ))
        
        if save_path:
            self._save_cheatsheet(cheatsheet, save_path)
        
        return cheatsheet
    
    def _extract_key_points(self, content: str, topic_name: str) -> Dict:
        """
        Extract key points from markdown content using Gemini.
        This is a single LLM call per note file (natural chunking).
        """
        prompt = f"""Analyze this educational content about "{topic_name}" and extract key information for a quick revision cheatsheet.

Content:
{content}

Extract and return a JSON object with:
1. "formulas": List of important formulas/equations (as LaTeX or plain text)
2. "definitions": List of key definitions (format: "Term: Definition")
3. "algorithms": List of algorithm names or pseudocode steps
4. "key_points": List of 5-10 most important concepts (brief bullet points)
5. "tips": List of study tips or shortcuts
6. "mistakes": List of common mistakes to avoid
7. "diagrams": List of Mermaid diagram scripts if visualizations would help

Keep each item concise (1-2 lines max). Focus on what's essential for quick revision.
Return ONLY valid JSON, no markdown formatting."""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            # Parse JSON response
            result_text = response.text.strip()
            if result_text.startswith("```json"):
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif result_text.startswith("```"):
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(result_text)
            return result
            
        except Exception as e:
            print(f"  Error extracting key points: {e}")
            return {
                'formulas': [],
                'definitions': [],
                'algorithms': [],
                'key_points': [],
                'tips': [],
                'mistakes': [],
                'diagrams': []
            }
    
    def _save_cheatsheet(self, cheatsheet: Cheatsheet, output_path: str):
        """Save cheatsheet as markdown and JSON."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as markdown
        md_content = self._format_as_markdown(cheatsheet)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        # Save JSON metadata
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(cheatsheet.model_dump(), f, indent=2, default=str)
    
    def _format_as_markdown(self, cheatsheet: Cheatsheet) -> str:
        """Format cheatsheet as readable markdown."""
        md = f"# {cheatsheet.title}\n\n"
        md += f"**Subject:** {cheatsheet.subject}\n\n"
        if cheatsheet.module:
            md += f"**Module:** {cheatsheet.module}\n\n"
        md += f"⏱️ **Estimated Review Time:** {cheatsheet.estimated_review_time} minutes\n\n"
        md += "---\n\n"
        
        # Key sections
        if cheatsheet.sections:
            md += "## 📝 Key Concepts\n\n"
            for section in cheatsheet.sections:
                md += f"### {section.title}\n\n"
                for item in section.items:
                    md += f"- {item}\n"
                md += "\n"
        
        if cheatsheet.key_formulas:
            md += "## 📐 Formulas\n\n"
            for formula in cheatsheet.key_formulas:
                md += f"- {formula}\n"
            md += "\n"
        
        if cheatsheet.key_definitions:
            md += "## 📖 Definitions\n\n"
            for definition in cheatsheet.key_definitions:
                md += f"- **{definition}**\n"
            md += "\n"
        
        if cheatsheet.key_algorithms:
            md += "## ⚙️ Algorithms\n\n"
            for algo in cheatsheet.key_algorithms:
                md += f"- {algo}\n"
            md += "\n"
        
        if cheatsheet.important_diagrams:
            md += "## 📊 Visual Aids\n\n"
            for idx, diagram in enumerate(cheatsheet.important_diagrams, 1):
                md += f"### Diagram {idx}\n\n"
                md += f"```mermaid\n{diagram}\n```\n\n"
        
        if cheatsheet.quick_tips:
            md += "## 💡 Quick Tips\n\n"
            for tip in cheatsheet.quick_tips:
                md += f"- ✅ {tip}\n"
            md += "\n"
        
        if cheatsheet.common_mistakes:
            md += "## ⚠️ Common Mistakes\n\n"
            for mistake in cheatsheet.common_mistakes:
                md += f"- ❌ {mistake}\n"
            md += "\n"
        
        md += "---\n\n"
        md += f"*Generated on {cheatsheet.created_at.strftime('%Y-%m-%d %H:%M')}*\n"
        
        return md
