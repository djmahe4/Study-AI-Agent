import sys
import time

def visualize_data(data):
    """A simple function to visualize data in the CLI with colors and dotted loading."""
    # ANSI escape codes for colors
    colors = ["\033[91m", "\033[92m", "\033[93m", "\033[94m", "\033[95m", "\033[96m"]
    reset = "\033[0m"

    for i, item in enumerate(data):
        color = colors[i % len(colors)]
        sys.stdout.write(f"{color}{item}{reset} ")

        # dotted loading effect
        for dot in range(3):
            sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(0.3)

        sys.stdout.write("\n")
        sys.stdout.flush()

    return
def single_line_viz(text):
    """Visualize a single line of text with a loading effect."""
    sys.stdout.write(text)
    for dot in range(3):
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(0.3)
    sys.stdout.write("\n")
    sys.stdout.flush()
    return
# Example usage
if __name__ == "__main__":
    visualize_data(["Topic 1: Introduction to RAG", "Topic 2: Vector Databases", "Topic 3: LLM Integration"])
    single_line_viz("Processing syllabus")