import os

def read_markdown_files(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                print(f"\n=== {file_path} ===\n")
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        print(content)
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

if __name__ == "__main__":
    folder = input("Enter folder path: ").strip()
    read_markdown_files(folder)