#!/usr/bin/env python3
"""
flashcard_session.py – Interactive terminal flashcard runner.

Lightweight helper for the active-recall-tester skill.
Reads a JSON flashcard deck (list of {front, back} objects) and runs
an interactive quiz session, tracking correct/incorrect/skipped answers.

Usage:
    python skills/active-recall-tester/scripts/flashcard_session.py deck.json
"""

import sys
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT))

from core.input_validator import sanitize_question_text


def keyword_overlap(user_answer: str, model_answer: str, threshold: float = 0.6) -> bool:
    """Return True if user answer shares >= threshold fraction of model answer keywords."""
    model_words = set(w.lower() for w in model_answer.split() if len(w) > 3)
    user_words = set(w.lower() for w in user_answer.split() if len(w) > 3)
    if not model_words:
        return bool(user_words)
    overlap = len(model_words & user_words) / len(model_words)
    return overlap >= threshold


def run_session(cards: list) -> dict:
    """Run an interactive flashcard session. Returns session stats."""
    correct = incorrect = skipped = 0
    results = []

    for i, card in enumerate(cards, 1):
        front = card.get("front", "?")
        back = card.get("back", "?")

        print(f"\n--- Card {i}/{len(cards)} ---")
        print(f"Q: {front}")
        try:
            raw_answer = input("Your answer (or ENTER to skip): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSession interrupted.")
            break

        clean_answer = sanitize_question_text(raw_answer)

        if not clean_answer:
            skipped += 1
            status = "skipped"
        elif keyword_overlap(clean_answer, back):
            correct += 1
            status = "correct"
            print("✅ Correct!")
        else:
            incorrect += 1
            status = "incorrect"
            print(f"❌ Incorrect. Model answer: {back}")

        results.append({"card": i, "question": front, "status": status})

    total = correct + incorrect + skipped
    retention = round(correct / max(total - skipped, 1) * 100, 1)

    print(f"\n=== Session Complete ===")
    print(f"Correct: {correct}  |  Incorrect: {incorrect}  |  Skipped: {skipped}")
    print(f"Retention Score: {retention}%")

    if incorrect > 0:
        print("\nReview these cards again in 3 days:")
        for r in results:
            if r["status"] == "incorrect":
                print(f"  - Card {r['card']}: {r['question'][:60]}")

    return {"correct": correct, "incorrect": incorrect, "skipped": skipped, "retention": retention}


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: flashcard_session.py <deck.json>")
        sys.exit(1)

    deck_path = sys.argv[1]
    try:
        data = json.loads(Path(deck_path).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error reading deck file: {e}")
        sys.exit(1)

    if not isinstance(data, list):
        data = data.get("cards", [])

    if not data:
        print("No cards found in deck file.")
        sys.exit(1)

    run_session(data)


if __name__ == "__main__":
    main()
