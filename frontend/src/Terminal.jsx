import { useState, useEffect, useRef } from 'react'
import './Terminal.css'

const Terminal = () => {
  const [history, setHistory] = useState([])
  const [currentInput, setCurrentInput] = useState('')
  const [commandHistory, setCommandHistory] = useState([])
  const [historyIndex, setHistoryIndex] = useState(-1)
  const inputRef = useRef(null)
  const terminalRef = useRef(null)

  useEffect(() => {
    // Display welcome message on load
    addOutput([
      '╔════════════════════════════════════════════════════════════╗',
      '║                  AI LEARNING ENGINE CLI                    ║',
      '║                    Version 1.0.0                           ║',
      '╚════════════════════════════════════════════════════════════╝',
      '',
      'Welcome to the AI-Augmented Intelligent Learning Engine!',
      'Type "help" to see available commands.',
      ''
    ])
    inputRef.current?.focus()
  }, [])

  useEffect(() => {
    // Auto scroll to bottom
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [history])

  const addOutput = (output) => {
    setHistory(prev => [...prev, { type: 'output', content: output }])
  }

  const addCommand = (command) => {
    setHistory(prev => [...prev, { type: 'command', content: command }])
  }

  const processCommand = (input) => {
    const trimmedInput = input.trim()
    if (!trimmedInput) return

    addCommand(trimmedInput)
    setCommandHistory(prev => [...prev, trimmedInput])

    const [command, ...args] = trimmedInput.split(' ')

    switch (command.toLowerCase()) {
      case 'help':
        handleHelp()
        break
      case 'subjects':
        handleSubjects()
        break
      case 'select':
        handleSelectSubject(args)
        break
      case 'create-subject':
        handleCreateSubject(args)
        break
      case 'topics':
        handleTopics(args)
        break
      case 'add-topic':
        handleAddTopic(args)
        break
      case 'questions':
        handleQuestions(args)
        break
      case 'quiz':
        handleQuiz(args)
        break
      case 'mindmap':
        handleMindmap(args)
        break
      case 'mnemonic':
        handleMnemonic(args)
        break
      case 'differences':
        handleDifferences(args)
        break
      case 'animate':
        handleAnimate(args)
        break
      case 'clear':
        setHistory([])
        break
      case 'exit':
        addOutput(['Goodbye! Thanks for learning with us. 👋'])
        break
      default:
        addOutput([`Command not found: ${command}`, 'Type "help" for available commands.'])
    }
  }

  const handleHelp = () => {
    addOutput([
      '',
      '📚 Available Commands:',
      '═══════════════════════════════════════════════════════',
      '',
      '  help                     - Show this help message',
      '  subjects                 - List all subjects',
      '  select <subject>         - Select a subject to work with',
      '  create-subject <name>    - Create new subject (use Python CLI)',
      '  topics [list]            - List all topics',
      '  add-topic <name>         - Add a new topic (interactive)',
      '  questions [topic]        - List questions for a topic',
      '  quiz [topic]             - Start a quiz session',
      '  mindmap                  - Generate mind map',
      '  mnemonic <topic>         - Generate mnemonic for topic',
      '  differences <example>    - Show difference table',
      '                             Examples: tcp_vs_udp, stack_vs_queue',
      '  animate <type>           - Create animation',
      '                             Types: tcp, stack',
      '  clear                    - Clear terminal',
      '  exit                     - Exit the application',
      '',
      '═══════════════════════════════════════════════════════',
      ''
    ])
  }

  const handleSubjects = () => {
    // Simulated subjects
    const subjects = [
      { name: 'Machine Learning', folder: 'data/subjects/machine_learning', hasQBank: true },
      { name: 'Data Structures', folder: 'data/subjects/data_structures', hasQBank: false },
      { name: 'Computer Networks', folder: 'data/subjects/computer_networks', hasQBank: true }
    ]

    if (subjects.length === 0) {
      addOutput(['', 'No subjects found. Create one with Python CLI:', '  python cli.py create-subject "Subject Name"', ''])
      return
    }

    const output = [
      '',
      '📚 Available Subjects:',
      '─────────────────────────────────────────────────────',
      ''
    ]

    subjects.forEach((subj, index) => {
      output.push(`${index + 1}. ${subj.name}`)
      output.push(`   📁 ${subj.folder}`)
      output.push(`   ${subj.hasQBank ? '✓' : '✗'} Question Bank`)
      output.push('')
    })

    output.push('─────────────────────────────────────────────────────')
    output.push('Use "select <subject-name>" to choose a subject')
    output.push('')

    addOutput(output)
  }

  const handleSelectSubject = (args) => {
    if (args.length === 0) {
      addOutput([
        '',
        '⚠️  Usage: select <subject-name>',
        'Example: select "Machine Learning"',
        ''
      ])
      return
    }

    const subjectName = args.join(' ')
    addOutput([
      '',
      `✅ Selected subject: ${subjectName}`,
      'All commands will now operate in context of this subject.',
      ''
    ])
  }

  const handleCreateSubject = (args) => {
    addOutput([
      '',
      '⚠️  To create a subject, use the Python CLI:',
      '',
      'python cli.py create-subject "Subject Name" \\',
      '  --syllabus-file syllabus.txt \\',
      '  --question-bank @questions.pdf',
      '',
      'Or interactively:',
      'python cli.py create-subject "Subject Name"',
      ''
    ])
  }

  const handleTopics = (args) => {
    // Simulated topics data
    const topics = [
      { name: 'TCP/IP Protocol', summary: 'Transport layer protocol for reliable communication', keyPoints: 3 },
      { name: 'Data Structures', summary: 'Fundamental structures for organizing data', keyPoints: 5 },
      { name: 'Machine Learning', summary: 'Algorithms that learn from data', keyPoints: 4 }
    ]

    if (topics.length === 0) {
      addOutput(['', 'No topics found. Use "add-topic" to create one.', ''])
      return
    }

    const output = [
      '',
      '📚 Topics in Knowledge Base:',
      '─────────────────────────────────────────────────────',
      ''
    ]

    topics.forEach((topic, index) => {
      output.push(`${index + 1}. ${topic.name}`)
      output.push(`   ${topic.summary}`)
      output.push(`   Key Points: ${topic.keyPoints}`)
      output.push('')
    })

    output.push('─────────────────────────────────────────────────────')
    output.push('')

    addOutput(output)
  }

  const handleAddTopic = (args) => {
    if (args.length === 0) {
      addOutput([
        '',
        '⚠️  Usage: add-topic <topic-name>',
        'Example: add-topic "Neural Networks"',
        ''
      ])
      return
    }

    const topicName = args.join(' ')
    addOutput([
      '',
      `✅ Topic "${topicName}" added successfully!`,
      'Use the Python CLI for full topic management with:',
      `   python cli.py add-topic "${topicName}" --summary "..." --key-points "..."`,
      ''
    ])
  }

  const handleQuestions = (args) => {
    const questions = [
      { topic: 'TCP/IP Protocol', question: 'What are the three steps of TCP handshake?', difficulty: 'medium' },
      { topic: 'Data Structures', question: 'Explain the difference between Stack and Queue', difficulty: 'easy' }
    ]

    const topic = args.join(' ')
    const filtered = topic ? questions.filter(q => q.topic.toLowerCase().includes(topic.toLowerCase())) : questions

    if (filtered.length === 0) {
      addOutput(['', 'No questions found.', ''])
      return
    }

    const output = [
      '',
      `❓ Questions${topic ? ` for "${topic}"` : ''}:`,
      '─────────────────────────────────────────────────────',
      ''
    ]

    filtered.forEach((q, index) => {
      output.push(`${index + 1}. [${q.difficulty.toUpperCase()}] ${q.topic}`)
      output.push(`   ${q.question}`)
      output.push('')
    })

    output.push('─────────────────────────────────────────────────────')
    output.push('')

    addOutput(output)
  }

  const handleQuiz = (args) => {
    addOutput([
      '',
      '🎯 Starting Quiz Mode...',
      '',
      'Question 1: What does TCP stand for?',
      '',
      'Enter your answer or type "exit" to quit quiz mode.',
      ''
    ])
  }

  const handleMindmap = (args) => {
    addOutput([
      '',
      '🗺️  Generating Mind Map...',
      '',
      '                 [My Learning Path]',
      '                        |',
      '          ┌─────────────┼─────────────┐',
      '          │             │             │',
      '    [TCP/IP Protocol] [Data Structures] [Machine Learning]',
      '          |             |             |',
      '     [Handshake]   [Stack & Queue]  [Supervised]',
      '     [Ports]       [Trees]          [Unsupervised]',
      '',
      '✅ Mind map generated!',
      'Export to file: python cli.py generate-mindmap',
      ''
    ])
  }

  const handleMnemonic = (args) => {
    if (args.length === 0) {
      addOutput([
        '',
        '⚠️  Usage: mnemonic <topic-name>',
        'Example: mnemonic "TCP Handshake"',
        ''
      ])
      return
    }

    addOutput([
      '',
      '🧠 Mnemonic Generator',
      '─────────────────────────────────────────────────────',
      '',
      'Topic: TCP Handshake',
      'Technique: Acronym',
      'Mnemonic: SYN-SA',
      '',
      'Explanation:',
      '  S - SYN (Synchronize)',
      '  Y - Your',
      '  N - Network',
      '  S - Sends',
      '  A - Acknowledgment',
      '',
      '─────────────────────────────────────────────────────',
      ''
    ])
  }

  const handleDifferences = (args) => {
    const example = args[0] || 'tcp_vs_udp'

    if (example === 'tcp_vs_udp') {
      addOutput([
        '',
        '📊 TCP vs UDP Comparison',
        '═══════════════════════════════════════════════════════',
        '',
        '┌─────────────────┬──────────────────┬──────────────────┐',
        '│ Aspect          │ TCP              │ UDP              │',
        '├─────────────────┼──────────────────┼──────────────────┤',
        '│ Connection      │ Connection-based │ Connectionless   │',
        '│ Reliability     │ Reliable         │ Unreliable       │',
        '│ Speed           │ Slower           │ Faster           │',
        '│ Use Case        │ File transfer    │ Streaming, Gaming│',
        '└─────────────────┴──────────────────┴──────────────────┘',
        '',
        '═══════════════════════════════════════════════════════',
        ''
      ])
    } else if (example === 'stack_vs_queue') {
      addOutput([
        '',
        '📊 Stack vs Queue Comparison',
        '═══════════════════════════════════════════════════════',
        '',
        '┌─────────────────┬──────────────────┬──────────────────┐',
        '│ Aspect          │ Stack            │ Queue            │',
        '├─────────────────┼──────────────────┼──────────────────┤',
        '│ Order           │ LIFO             │ FIFO             │',
        '│ Operations      │ Push, Pop        │ Enqueue, Dequeue │',
        '│ Use Case        │ Function calls   │ Task scheduling  │',
        '└─────────────────┴──────────────────┴──────────────────┘',
        '',
        '═══════════════════════════════════════════════════════',
        ''
      ])
    } else {
      addOutput([
        '',
        '⚠️  Available examples: tcp_vs_udp, stack_vs_queue',
        ''
      ])
    }
  }

  const handleAnimate = (args) => {
    const type = args[0] || 'tcp'

    addOutput([
      '',
      `🎬 Creating ${type.toUpperCase()} animation...`,
      '',
      '  [████████████████████████████] 100%',
      '',
      `✅ Animation created at: data/animations/${type}.mp4`,
      '',
      'To generate actual animation files, use:',
      `   python cli.py create-animation ${type}`,
      ''
    ])
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      processCommand(currentInput)
      setCurrentInput('')
      setHistoryIndex(-1)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (commandHistory.length > 0) {
        const newIndex = historyIndex === -1 
          ? commandHistory.length - 1 
          : Math.max(0, historyIndex - 1)
        setHistoryIndex(newIndex)
        setCurrentInput(commandHistory[newIndex])
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (historyIndex >= 0) {
        const newIndex = historyIndex + 1
        if (newIndex >= commandHistory.length) {
          setHistoryIndex(-1)
          setCurrentInput('')
        } else {
          setHistoryIndex(newIndex)
          setCurrentInput(commandHistory[newIndex])
        }
      }
    }
  }

  return (
    <div className="terminal-container" onClick={() => inputRef.current?.focus()}>
      <div className="terminal-header">
        <div className="terminal-buttons">
          <span className="button close"></span>
          <span className="button minimize"></span>
          <span className="button maximize"></span>
        </div>
        <div className="terminal-title">AI Learning Engine CLI</div>
      </div>
      
      <div className="terminal-body" ref={terminalRef}>
        {history.map((item, index) => (
          <div key={index} className={`terminal-line ${item.type}`}>
            {item.type === 'command' ? (
              <div className="command-line">
                <span className="prompt">$</span>
                <span className="command-text">{item.content}</span>
              </div>
            ) : (
              Array.isArray(item.content) ? (
                item.content.map((line, lineIndex) => (
                  <div key={lineIndex} className="output-line">{line}</div>
                ))
              ) : (
                <div className="output-line">{item.content}</div>
              )
            )}
          </div>
        ))}
        
        <div className="terminal-input-line">
          <span className="prompt">$</span>
          <input
            ref={inputRef}
            type="text"
            className="terminal-input"
            value={currentInput}
            onChange={(e) => setCurrentInput(e.target.value)}
            onKeyDown={handleKeyDown}
            autoFocus
            spellCheck={false}
          />
          <span className="cursor">█</span>
        </div>
      </div>
    </div>
  )
}

export default Terminal
