# 🤖 MyCode Agent - Demo Guide

This guide demonstrates the powerful new **Agentic Mode** in MyCode CLI, which brings autonomous planning and execution capabilities to your coding workflow.

## 🚀 Quick Demo

### 1. Simple File Creation
```bash
python main.py agent "create a simple Python calculator with basic operations"
```

**What the agent will do:**
- Plan the structure of a calculator module
- Create `calculator.py` with add, subtract, multiply, divide functions
- Add input validation and error handling
- Create a simple CLI interface

### 2. Adding Tests
```bash
python main.py agent "add comprehensive tests for the calculator module"
```

**What the agent will do:**
- Analyze the existing calculator code
- Create `test_calculator.py` with pytest
- Test all functions including edge cases
- Add test for CLI interface

### 3. Documentation Generation
```bash
python main.py agent "create documentation for the calculator project"
```

**What the agent will do:**
- Analyze the codebase structure
- Generate `README.md` with usage examples
- Add docstrings to all functions
- Create API documentation

## 🎯 Advanced Examples

### Full Project Creation
```bash
python main.py agent "create a Flask web API for a todo list with database and authentication"
```

### Code Refactoring
```bash
python main.py agent "refactor the existing code to use object-oriented design patterns"
```

### Performance Optimization
```bash
python main.py agent "analyze and optimize the code for better performance"
```

## 🛡️ Safety Features

### Automatic Risk Assessment
The agent automatically evaluates each plan:
- **Safety Level 1-2**: Low risk operations (reading, analysis)
- **Safety Level 3**: Moderate risk (file modifications)
- **Safety Level 4-5**: High risk operations (deletions, system changes)

### User Approval Process
```
📋 Execution Plan
🎯 Goal: Create Flask API with authentication
🧠 Reasoning: Build REST API with JWT auth and database
📊 Complexity: 8/10
⚠️  Safety Level: 4/5  ← High risk operation
📝 Steps: 8

⚠️  High-risk operations detected!
This plan involves potentially risky operations. Continue? [y/N]
```

### Auto-Approve Mode
For trusted operations, use `--auto-approve`:
```bash
python main.py agent "add type hints to all functions" --auto-approve
```

## 📊 Session Monitoring

### Real-time Progress
```
⚡ Execution phase...
⠋ Step 1: Create File                 
✅ Step 1: Create File
⠋ Step 2: Write File
✅ Step 2: Write File
⠋ Step 3: Analyze Code
✅ Step 3: Analyze Code
```

### Session Summary
```
🎉 All steps completed successfully!
📊 Session Summary:
  • Steps completed: 6/6
  • Memory items: 12
  • Session ID: 1704123456
```

## 🔧 Agent Capabilities

### Planning Actions
- **`read_file`** - Read and analyze existing files
- **`write_file`** - Modify existing files
- **`create_file`** - Create new files with content
- **`analyze_code`** - Perform code analysis
- **`search_codebase`** - Search through project files

### Context Awareness
The agent uses your project's full context:
- AST analysis of existing code
- Project structure and patterns
- Development history
- File relationships and dependencies

### Memory Management
The agent maintains memory across actions:
- File contents for reference
- Analysis results
- Action history
- Learned patterns

## 🎪 Example Session Walkthrough

Let's create a simple web scraper project:

```bash
python main.py agent "create a web scraper that extracts article titles from news websites"
```

**Agent Planning:**
```
🤖 Code Agent activated
📋 Planning phase...

┌─ Execution Plan ─────────────────────────────────────────┐
│ 🎯 Goal: Create web scraper for news article titles     │
│ 🧠 Reasoning: Build requests + BeautifulSoup scraper     │
│ 📊 Complexity: 5/10                                      │
│ ⚠️  Safety Level: 2/5                                     │
│ 📝 Steps: 5                                               │
└───────────────────────────────────────────────────────────┘

 # │ Action     │ Target              │ Reasoning                    
───┼────────────┼─────────────────────┼──────────────────────────────
 1 │ Create File│ scraper.py          │ Main scraper module          
 2 │ Create File│ requirements.txt    │ Dependencies (requests, bs4) 
 3 │ Create File│ config.py           │ Configuration and URLs       
 4 │ Create File│ examples.py         │ Usage examples              
 5 │ Analyze Code│ .                  │ Validate project structure   
```

**Agent Execution:**
```
⚡ Execution phase...
✅ Step 1: Create File - Created scraper.py with ArticleScraper class
✅ Step 2: Create File - Added requirements.txt with requests, beautifulsoup4
✅ Step 3: Create File - Created config.py with news site URLs
✅ Step 4: Create File - Added examples.py with usage demonstrations
✅ Step 5: Analyze Code - Project structure validated, ready to use

🎉 All steps completed successfully!
```

## 🎭 Best Practices

### Clear Goal Specification
```bash
# ✅ Good - Specific and actionable
python main.py agent "create a RESTful API with CRUD operations for user management"

# ❌ Vague - Hard to plan
python main.py agent "make the code better"
```

### Incremental Development
```bash
# Start simple
python main.py agent "create basic project structure"

# Add features
python main.py agent "add user authentication"
python main.py agent "add database integration"
python main.py agent "add comprehensive tests"
```

### Safety First
- Review plans carefully for complex operations
- Use `--auto-approve` only for trusted, low-risk tasks
- Check agent history in `.mycode/context/history.md`

## 🚨 Limitations

- **Context Limits**: Large projects may hit token limits
- **Complex Logic**: Very complex business logic may need human guidance
- **External Dependencies**: Cannot install system packages or external services
- **Testing**: Cannot run tests automatically (yet!)

## 🔮 Future Enhancements

Coming soon:
- **Test Execution** - Run tests after code changes
- **Git Integration** - Automatic commits with meaningful messages
- **Code Review** - Self-review and validation
- **Multi-step Workflows** - Complex development pipelines

---

**Happy Coding with MyCode Agent! 🤖✨**
