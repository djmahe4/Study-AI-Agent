import json
from pathlib import Path
from datetime import datetime

def sync_subjects():
    base_dir = Path("data/subjects")
    subjects_file = base_dir / "subjects.json"
    
    found_subjects = []
    
    # Iterate over directories
    for p in base_dir.iterdir():
        if p.is_dir():
            # Check for syllabus
            syllabus_dir = p / "syllabus"
            if not syllabus_dir.exists():
                continue
                
            # Find syllabus file
            syllabus_path = None
            for s in syllabus_dir.glob("*.json"):
                syllabus_path = str(s).replace("\\", "/")
                break
                
            if not syllabus_path:
                print(f"Skipping {p.name}: No syllabus found")
                continue
                
            # Create entry
            # Convert snake_case to Title Case for name
            name = p.name.replace("_", " ").title()
            
            entry = {
                "name": name,
                "folder_path": str(p).replace("\\", "/"),
                "syllabus_path": syllabus_path,
                "question_bank_path": None, # Reset or detect?
                "created_at": datetime.now().isoformat()
            }
            found_subjects.append(entry)
            print(f"Found subject: {name}")

    # Write back
    with open(subjects_file, "w") as f:
        json.dump(found_subjects, f, indent=2)
        
    print(f"Synced {len(found_subjects)} subjects to {subjects_file}")

if __name__ == "__main__":
    sync_subjects()
