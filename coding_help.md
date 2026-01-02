# Gemini Study CLI: Coding Help

This guide will help you get started with the Gemini Study CLI, a tool designed to help you study more effectively using the power of Gemini AI.

## 1. Introduction

The Gemini Study CLI is a command-line application that helps you process your study materials, such as syllabuses and question banks, and generate study aids like mind maps and mnemonics. It uses the Gemini AI to understand your learning materials and provide you with structured information.

Since you mentioned you are not familiar with TypeScript and npm, you don't need to worry. This project is built with Python, so you won't need to use TypeScript or npm.

## 2. Setup

Follow these steps to set up the project on your local machine.

### 2.1. Install Dependencies

This project uses Python and has a list of dependencies in the `requirements.txt` file. You can install them using `pip`:

```bash
pip install -r requirements.txt
```

This command will install all the necessary Python libraries for the project to run.

### 2.2. Set Your Gemini API Key

The application uses the Gemini API to process your syllabus. You need to provide your API key for it to work. Although the full integration is still in progress, you can add your API key to the `core/gemini_processor.py` file.

1.  Open the file `D:\Study-AI-Agent\core\gemini_processor.py`.
2.  Find the `__init__` method within the `GeminiProcessor` class.
3.  You will see a line `self.api_key = api_key`. The API key is passed to the constructor, but for now, you can hardcode it for your own use. Modify the file as follows:

```python
from typing import Optional
# Around line 15 in core/gemini_processor.py

class GeminiProcessor:
    """
    Processes syllabus text using Gemini AI to extract structured data.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        # FOR NOW, YOU CAN ADD YOUR API KEY HERE
        self.api_key = "YOUR_GEMINI_API_KEY" 
        # import google.generativeai as genai
        # genai.configure(api_key=self.api_key)
        # self.model = genai.GenerativeModel('gemini-pro')
```

Replace `"YOUR_GEMINI_API_KEY"` with your actual Gemini API key.

**Important:** The current version of the app uses a placeholder for the Gemini API call. To make it work, you would need to complete the implementation in `core/gemini_processor.py`.

## 3. Running the CLI

The main entry point for the application is `cli.py`. You can run all commands from your terminal.

### 3.1. Initialize the Knowledge Base

First, you need to initialize the knowledge base. This will create the necessary database and folders.

```bash
python cli.py init
```

### 3.2. Create a Subject

This is the main feature of the application. You can create a new subject and process your syllabus.

Let's say you have a syllabus in a file named `my_syllabus.txt` and a question bank in `my_questions.txt`.

1.  **Create `my_syllabus.txt`:**
    Create a new file named `my_syllabus.txt` in the root of the project and add your syllabus content to it. For example:

    ```
    Introduction to Python
    - Variables and Data Types
    - Control Flow
    - Functions

    Advanced Python
    - Object-Oriented Programming
    - Decorators
    - Generators
    ```

2.  **Create `my_questions.txt`:**
    Create a new file named `my_questions.txt` and add your questions.

    ```
    What is a variable in Python?
    Explain the difference between a list and a tuple.
    ```

3.  **Run the `create-subject` command:**

    ```bash
    python cli.py create-subject "My Python Course" --syllabus-file my_syllabus.txt --question-bank @my_questions.txt
    ```

    This command will:
    *   Create a new subject named "My Python Course".
    *   Process `my_syllabus.txt` using the (placeholder) Gemini processor.
    *   Link the `my_questions.txt` file as a question bank.

### 3.3. List and Select Subjects

You can see all the subjects you have created:

```bash
python cli.py list-subjects
```

To work with a specific subject, you can select it:

```bash
python cli.py select-subject "My Python Course"
```

## 4. Manual Memory Management for Token Saving

You asked about memory management to save tokens. The current version of the project does not have an explicit conversation history management feature. However, you can manually implement this when you decide to extend the project's functionality.

The basic idea is to keep a list of the last few conversation turns (user messages and AI responses) and send them to the Gemini API with your new prompt. This gives the AI context about the conversation. To save tokens, you can limit the number of turns you keep in the history.

Here is a simple Python snippet to illustrate the concept:

```python
from collections import deque

# Keep a history of the last 5 conversation turns
conversation_history = deque(maxlen=5)

def add_to_history(role, text):
    """Adds a message to the conversation history."""
    conversation_history.append({"role": role, "text": text})

def get_prompt_with_history(new_prompt):
    """Creates a new prompt that includes the conversation history."""
    history_text = "\n".join([f"{turn['role']}: {turn['text']}" for turn in conversation_history])
    return f"{history_text}\nuser: {new_prompt}\nmodel:"

# Example usage:
add_to_history("user", "What is Python?")
add_to_history("model", "Python is a high-level, interpreted programming language.")

new_prompt = "Can you tell me more about its features?"
full_prompt = get_prompt_with_history(new_prompt)

print(full_prompt)

# When you call the Gemini API, you would send `full_prompt`.
# The `deque` with `maxlen` will automatically discard old messages, saving tokens.
```

You can integrate this logic into the `GeminiProcessor` when you are ready to implement the full Gemini API calls.

## 5. Example with Your Subject

Let's run the project with the sample files provided.

1.  **Initialize the project:**
    ```bash
    python cli.py init
    ```

2.  **Create a subject using the sample files:**
    The project includes `sample_syllabus.txt` and `sample_questions.txt`. Let's use them to create a "Computer Networks" subject.

    ```bash
    python cli.py create-subject "Computer Networks" --syllabus-file data/sample_syllabus.txt --question-bank @data/sample_questions.txt
    ```

3.  **List the subjects:**
    ```bash
    python cli.py list-subjects
    ```
    You should see "Computer Networks" in the list.

4.  **Explore the subject:**
    Now that you have a subject, you can use other commands like `list-topics` to see the processed syllabus.

    ```bash
    python cli.py list-topics
    ```

This should give you a good starting point to explore the project and its features. Feel free to experiment with different commands and your own study materials.
