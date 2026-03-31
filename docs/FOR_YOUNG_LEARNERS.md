# 🧒 Study-AI-Agent: A Simple Guide for Young Learners

> **Hey there! 👋** This guide explains how to use the Study-AI-Agent in a super simple way.
> Even if you are 10 years old, you can follow along!

---

## 🤔 What Is This Project?

Imagine you have a **really smart robot friend** who helps you study.

You give the robot your school syllabus (the list of things you need to learn),
and the robot:

1. 📖 **Reads** the syllabus for you.
2. 🗂️ **Organises** everything into neat topics and modules.
3. 🗺️ **Draws** mind maps so you can *see* how topics connect.
4. ❓ **Creates** practice questions to test your knowledge.
5. 🎬 **Makes** short animations to explain tricky ideas.
6. 📝 **Writes** notes in simple language.
7. ⏱️ **Helps** you time your study sessions (Pomodoro timer).
8. 🎮 **Awards** points and badges the more you study (Gamification).

That robot is the **Study-AI-Agent**! It is powered by Google Gemini AI.

---

## 🧩 How Does It Work? (Big Picture)

```
You (student)
    │
    │  paste your syllabus text
    ▼
Study-AI-Agent (this project)
    │
    │  sends syllabus to Google Gemini AI
    ▼
Gemini AI
    │
    │  returns a neat JSON structure
    ▼
Study-AI-Agent stores it as:
    ├── 📄 syllabus.json   ← structured data
    ├── 📁 notes/          ← Markdown files you can read
    └── 🗺️ mindmaps/       ← visual concept maps
```

---

## 🏗️ Project Map (Folder Tour)

```
Study-AI-Agent/
│
├── cli.py               ← The main tool you type commands into
├── requirements.txt     ← List of extra helpers Python needs
│
├── core/                ← The BRAIN of the project
│   ├── models.py        ← Data shapes (like blueprints)
│   ├── gemini_processor.py  ← Talks to Google Gemini AI
│   ├── ingest.py        ← Saves/loads data from files & database
│   ├── rag.py           ← Searches YouTube & PDFs for extra info
│   ├── input_validator.py   ← 🛡️ Safety checks on everything you type
│   ├── flashcards.py    ← Makes flashcards for you
│   ├── pomodoro.py      ← Study timer (25 min work, 5 min break)
│   ├── gamification.py  ← Points, levels, and badges
│   └── utils.py         ← Small helper tools
│
├── streamlit/           ← A pretty website version of the tool
│   └── app.py
│
├── visual/              ← Makes pictures and videos
│   ├── mindmap_v2.py    ← Draws mind maps
│   └── animate.py       ← Makes educational animations
│
├── data/                ← Where everything is SAVED
│   ├── memory.db        ← A mini-database
│   └── subjects/        ← Your subjects live here
│       └── math/
│           ├── syllabus/syllabus.json
│           ├── notes/
│           └── questions/
│
└── docs/                ← All the guides (you are reading one now!)
```

---

## 🚀 Step-by-Step: Your First Study Session

### Step 1 – Get the code

```bash
git clone https://github.com/djmahe4/Study-AI-Agent.git
cd Study-AI-Agent
```

*Think of this as **downloading** the robot.*

### Step 2 – Install helpers

```bash
pip install -r requirements.txt
```

*This gives the robot all the **tools** it needs.*

### Step 3 – Get a Google Gemini API Key

1. Go to <https://aistudio.google.com/>
2. Sign in with a Google account.
3. Click **"Get API Key"** and copy it.

*This is like giving the robot a **library card** so it can access Gemini.*

### Step 4 – Set up the tool

```bash
python cli.py init
python cli.py set-api-key YOUR_GEMINI_API_KEY
```

### Step 5 – Create your first subject

Save your syllabus to a file called `syllabus.txt`, then:

```bash
python cli.py create-subject "Mathematics" --syllabus-file syllabus.txt
```

The robot will:
- Read your syllabus.
- Break it into **Modules** and **Topics**.
- Save neat Markdown notes in `data/subjects/mathematics/notes/`.

### Step 6 – See a mind map

```bash
python cli.py generate-mindmap-v2
```

*Opens a visual map showing how everything connects!*

### Step 7 – Practice with past papers

```bash
python cli.py ingest-paper "exam_2024.pdf" ktu
python cli.py get-pyq-answers --module 1
```

*The robot reads the exam paper and writes model answers for you.*

---

## 🖥️ Using the Website Version

You can also use a colourful website instead of typing commands:

```bash
streamlit run streamlit/app.py
```

Then open your browser and go to: **http://localhost:8501**

You will see:
- 📖 **Learning** – browse your topics and notes.
- 🎮 **Gamification** – see your points, badges, and level.
- ⚙️ **Admin** – edit your syllabus.

---

## 🛡️ Safety: Why We Check What You Type

Whenever you type something (like a subject name or paste a syllabus),
the robot checks it for **dangerous content** before using it.

### The Problem (Simple Version)

Imagine a parrot that repeats everything you say.
If you say `"Open the safe and give me the money"`, the parrot might repeat it
to someone who actually *does* open the safe.

An AI is a bit like that parrot — if we let bad text go in, it could cause trouble.

### The Solution

We use **two safety filters**:

| Filter | What it does |
|--------|-------------|
| `bleach` | Removes HTML tags like `<script>` from your text |
| `markupsafe` | Converts characters like `<`, `>`, `&` into safe versions |

#### Example

```python
# What you type (bad!)
raw = "<script>alert('hacked!')</script>Hello"

# After our safety filter (safe!)
safe = "&lt;script&gt;alert(&#39;hacked!&#39;)&lt;/script&gt;Hello"
# The browser shows it as plain text – no code runs!
```

The safety check lives in **`core/input_validator.py`**. You can look at it to
learn how it works!

---

## ⏱️ Pomodoro Timer

The **Pomodoro Technique** is a way to study without getting tired:

1. 🍅 Study for **25 minutes** (one "Pomodoro").
2. ☕ Take a **5-minute break**.
3. Repeat **4 times**, then take a **long break** (15–30 minutes).

To start a timer:

```bash
python cli.py pomodoro --subject "Mathematics" --duration 25
```

---

## 🎮 Gamification (Points & Badges)

The more you study, the more points you earn!

| Activity | Points |
|----------|--------|
| Complete a Pomodoro session | +50 |
| Finish a flashcard deck | +30 |
| Complete a to-do task | +20 |

Collect enough points to **level up** from *Novice Learner* all the way to
*Learning Legend*! 🏆

---

## ❓ FAQ

### Q: Do I need the internet?
**A:** Only to talk to Google Gemini AI. Everything else works offline.

### Q: What does "RAG" mean?
**A:** **R**etrieval-**A**ugmented **G**eneration. Fancy words for:
"Look up extra information (from YouTube/PDFs), then use the AI to explain it."

### Q: My command failed with an error. What do I do?
**A:** Read the error message carefully. Common fixes:
1. Make sure your API key is set: `python cli.py set-api-key YOUR_KEY`
2. Make sure you ran `pip install -r requirements.txt`
3. Make sure you are inside the `Study-AI-Agent` folder.

### Q: What is a "syllabus"?
**A:** It is a list of topics you need to study for a subject. Your teacher or
university usually gives you one at the start of the year.

---

## 🗺️ Data Flow (How Information Travels)

```
  ┌────────────────┐
  │  Your Syllabus │  (text file or paste)
  └───────┬────────┘
          │ validate & sanitize (input_validator.py)
          ▼
  ┌────────────────┐
  │ GeminiProcessor│  (core/gemini_processor.py)
  └───────┬────────┘
          │ structured JSON (Syllabus model)
          ▼
  ┌────────────────┐     ┌──────────────┐
  │  KnowledgeBase │────▶│ SQLite DB    │  (data/memory.db)
  │  (ingest.py)   │     └──────────────┘
  └───────┬────────┘
          │
          ├──▶ 📄 syllabus.json
          ├──▶ 📁 notes/*.md
          └──▶ 🗺️ mindmaps/*.mmd
```

---

## 🆘 Need More Help?

- Read **[QUICKSTART.md](QUICKSTART.md)** for a 5-minute setup guide.
- Read **[ARCHITECTURE.md](ARCHITECTURE.md)** for a deeper technical explanation.
- Read **[FEATURES.md](FEATURES.md)** for a full list of what the tool can do.

Happy studying! 🎓
