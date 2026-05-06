"""
Practice problem generator with batch processing for token limit management.
Uses Gemini to generate coding/numerical problems for non-theory subjects.
"""
from pathlib import Path
from typing import List, Optional
import json
import os
from dotenv import load_dotenv
import google.genai as genai
from core.models import PracticeProblem
from core.utils import get_subject_dir


class PracticeGenerator:
    """
    Generates practice problems in batches to manage token limits.
    Optimized for non-theory subjects (coding, math, algorithms).
    """
    
    def __init__(self, api_key: Optional[str] = None):
        load_dotenv()
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key not found")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.0-flash-exp"
        self.data_path = Path("data/practice_problems")
        self.data_path.mkdir(parents=True, exist_ok=True)
    
    def generate_problems_batch(self, subject: str, topic: str, 
                               count: int = 5, difficulty: str = "medium",
                               problem_types: List[str] = None) -> List[PracticeProblem]:
        """
        Generate a batch of practice problems for a topic.
        Processes in batches of 5 to avoid token limits.
        
        Args:
            subject: Subject name
            topic: Topic to generate problems for
            count: Total number of problems to generate
            difficulty: easy, medium, or hard
            problem_types: List of types (mcq, short_answer, coding, derivation)
        """
        if problem_types is None:
            problem_types = ["mcq", "short_answer", "coding"]
        
        all_problems = []
        batch_size = 5
        batches_needed = (count + batch_size - 1) // batch_size
        
        print(f"🎯 Generating {count} practice problems for '{topic}'...")
        print(f"   Processing in {batches_needed} batch(es)...")
        
        for batch_num in range(batches_needed):
            remaining = count - len(all_problems)
            batch_count = min(batch_size, remaining)
            
            print(f"\n📝 Batch {batch_num + 1}/{batches_needed} ({batch_count} problems)...")
            
            try:
                problems = self._generate_single_batch(
                    subject, topic, batch_count, difficulty, problem_types
                )
                all_problems.extend(problems)
                print(f"   ✅ Generated {len(problems)} problems")
                
            except Exception as e:
                print(f"   ⚠️ Error in batch {batch_num + 1}: {e}")
                continue
        
        # Save problems
        self._save_problems(all_problems, subject, topic)
        
        return all_problems
    
    def _generate_single_batch(self, subject: str, topic: str, count: int,
                              difficulty: str, problem_types: List[str]) -> List[PracticeProblem]:
        """
        Generate a single batch of problems (max 5) in one LLM call.
        """
        types_str = ", ".join(problem_types)
        
        prompt = f"""Generate {count} practice problems for the topic "{topic}" in {subject}.

Requirements:
- Difficulty: {difficulty}
- Problem types to include: {types_str}
- Each problem should test understanding and application
- For coding problems: Include clear problem statement, examples, constraints
- For MCQs: Provide 4 options with one correct answer
- For derivations: Include step-by-step solution
- Include helpful hints and key concepts tested

Return a JSON array where each problem has:
{{
  "question": "problem statement",
  "difficulty": "{difficulty}",
  "problem_type": "one of {types_str}",
  "options": ["A", "B", "C", "D"],  // Only for MCQs
  "correct_option": 0,  // Only for MCQs (0-3 index)
  "solution": "detailed step-by-step solution",
  "hints": ["hint1", "hint2"],
  "key_concepts": ["concept1", "concept2"],
  "solution_diagram": "mermaid diagram if helpful (optional)"
}}

Generate exactly {count} diverse problems. Return ONLY valid JSON array, no markdown formatting."""

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
            
            problems_data = json.loads(result_text)
            
            # Convert to PracticeProblem objects
            problems = []
            for data in problems_data:
                try:
                    problem = PracticeProblem(
                        subject=subject,
                        topic=topic,
                        question=data['question'],
                        difficulty=data['difficulty'],
                        problem_type=data['problem_type'],
                        options=data.get('options', []),
                        correct_option=data.get('correct_option'),
                        solution=data['solution'],
                        hints=data.get('hints', []),
                        key_concepts=data.get('key_concepts', []),
                        solution_diagram=data.get('solution_diagram')
                    )
                    problems.append(problem)
                except Exception as e:
                    print(f"     Error parsing problem: {e}")
                    continue
            
            return problems
            
        except Exception as e:
            print(f"     LLM error: {e}")
            return []
    
    def _save_problems(self, problems: List[PracticeProblem], subject: str, topic: str):
        """Save problems to JSON file."""
        filename = f"{subject}_{topic}_problems.json".replace(" ", "_").replace("/", "-")
        file_path = self.data_path / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([p.model_dump() for p in problems], f, indent=2, default=str)
    
    def load_problems(self, subject: str, topic: Optional[str] = None) -> List[PracticeProblem]:
        """Load saved problems for a subject/topic."""
        if topic:
            filename = f"{subject}_{topic}_problems.json".replace(" ", "_").replace("/", "-")
            file_path = self.data_path / filename
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = json.load(f)
                return [PracticeProblem(**p) for p in data]
        else:
            # Load all problems for subject
            all_problems = []
            pattern = f"{subject}_*.json".replace(" ", "_")
            for file in self.data_path.glob(pattern):
                with open(file, 'r') as f:
                    data = json.load(f)
                all_problems.extend([PracticeProblem(**p) for p in data])
            return all_problems
        
        return []
    
    def generate_mixed_difficulty_set(self, subject: str, topic: str,
                                     total: int = 15) -> List[PracticeProblem]:
        """
        Generate a balanced set with mixed difficulty levels.
        Distribution: 40% easy, 40% medium, 20% hard
        """
        easy_count = int(total * 0.4)
        medium_count = int(total * 0.4)
        hard_count = total - easy_count - medium_count
        
        all_problems = []
        
        if easy_count > 0:
            print("\n🟢 Generating EASY problems...")
            easy = self.generate_problems_batch(subject, topic, easy_count, "easy")
            all_problems.extend(easy)
        
        if medium_count > 0:
            print("\n🟡 Generating MEDIUM problems...")
            medium = self.generate_problems_batch(subject, topic, medium_count, "medium")
            all_problems.extend(medium)
        
        if hard_count > 0:
            print("\n🔴 Generating HARD problems...")
            hard = self.generate_problems_batch(subject, topic, hard_count, "hard")
            all_problems.extend(hard)
        
        return all_problems
    
    def export_to_markdown(self, problems: List[PracticeProblem], output_file: str):
        """Export problems to a formatted markdown file."""
        md = f"# Practice Problems\n\n"
        md += f"**Total Problems:** {len(problems)}\n\n"
        md += "---\n\n"
        
        # Group by difficulty
        easy = [p for p in problems if p.difficulty == "easy"]
        medium = [p for p in problems if p.difficulty == "medium"]
        hard = [p for p in problems if p.difficulty == "hard"]
        
        for difficulty, problem_list, emoji in [
            ("Easy", easy, "🟢"),
            ("Medium", medium, "🟡"),
            ("Hard", hard, "🔴")
        ]:
            if problem_list:
                md += f"## {emoji} {difficulty} Problems\n\n"
                for idx, problem in enumerate(problem_list, 1):
                    md += f"### Problem {idx}\n\n"
                    md += f"**Type:** {problem.problem_type.upper()}\n\n"
                    md += f"{problem.question}\n\n"
                    
                    if problem.options:
                        md += "**Options:**\n"
                        for i, opt in enumerate(problem.options):
                            md += f"{chr(65+i)}. {opt}\n"
                        md += "\n"
                    
                    if problem.hints:
                        md += "<details>\n<summary>💡 Hints</summary>\n\n"
                        for hint in problem.hints:
                            md += f"- {hint}\n"
                        md += "\n</details>\n\n"
                    
                    md += "<details>\n<summary>✅ Solution</summary>\n\n"
                    md += f"{problem.solution}\n\n"
                    
                    if problem.solution_diagram:
                        md += "**Visual Representation:**\n\n"
                        md += f"```mermaid\n{problem.solution_diagram}\n```\n\n"
                    
                    md += "</details>\n\n"
                    md += "---\n\n"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md)
    
    def get_stats(self, problems: List[PracticeProblem]) -> dict:
        """Get statistics about practice problems."""
        total = len(problems)
        attempted = len([p for p in problems if p.attempted])
        correct = len([p for p in problems if p.correct is True])
        
        by_difficulty = {
            "easy": len([p for p in problems if p.difficulty == "easy"]),
            "medium": len([p for p in problems if p.difficulty == "medium"]),
            "hard": len([p for p in problems if p.difficulty == "hard"])
        }
        
        by_type = {}
        for problem in problems:
            by_type[problem.problem_type] = by_type.get(problem.problem_type, 0) + 1
        
        return {
            "total": total,
            "attempted": attempted,
            "correct": correct,
            "accuracy": (correct / max(1, attempted)) * 100,
            "by_difficulty": by_difficulty,
            "by_type": by_type
        }
