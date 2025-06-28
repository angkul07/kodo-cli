import json
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.markdown import Markdown

from kodo.file_ops.reader import read_file_content
from kodo.file_ops.writer import write_file_content
from kodo.context_manager import ContextManager


class AgentState(Enum):
    PLANNING = "planning"
    ACTING = "acting"
    OBSERVING = "observing"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    FAILED = "failed"


class ActionType(Enum):
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    CREATE_FILE = "create_file"
    ANALYZE_CODE = "analyze_code"
    SEARCH_CODEBASE = "search_codebase"
    RUN_TESTS = "run_tests"


@dataclass
class Action:
    type: ActionType
    target: str
    content: str = ""
    reasoning: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ActionResult:
    success: bool
    output: str = ""
    error: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ExecutionPlan:
    goal: str
    steps: List[Action]
    estimated_complexity: int  # 1-10 scale
    safety_level: int  # 1-5 scale (5 = highest risk)
    reasoning: str = ""


class CodeAgent:
    """Intelligent Code Agent with planning, acting, and reflection capabilities"""
    
    def __init__(self, llm_manager, project_root: Path):
        self.llm_manager = llm_manager
        self.project_root = project_root
        self.context_manager = ContextManager(project_root)
        self.console = Console()
        
        # Agent state
        self.state = AgentState.PLANNING
        self.current_plan: Optional[ExecutionPlan] = None
        self.action_history: List[Tuple[Action, ActionResult]] = []
        self.memory: Dict[str, Any] = {}
        self.session_id = str(int(time.time()))
    
    def execute_goal(self, goal: str, auto_approve: bool = False) -> bool:
        """Main execution method - orchestrates the agent's work"""
        self.console.print(f"\n[bold blue]Code Agent activated[/bold blue]")
        self.console.print(f"[dim]Session: {self.session_id}[/dim]")
        
        try:
            # Planning phase
            self.state = AgentState.PLANNING
            plan = self._plan_execution(goal)
            
            if not self._validate_and_approve_plan(plan, auto_approve):
                return False
            
            self.current_plan = plan
            
            # Execution phase
            success = self._execute_plan()
            
            # Log session to history
            self._log_session_to_history()
            
            return success
            
        except Exception as e:
            self.console.print(f"[red]Agent error: {e}[/red]")
            self.state = AgentState.FAILED
            return False
    
    def _plan_execution(self, goal: str) -> ExecutionPlan:
        """Create an execution plan for the given goal"""
        self.console.print("\n[yellow]Planning phase...[/yellow]")
        
        # Get project context
        context = self.context_manager.get_context_for_query(goal)
        
        planning_prompt = f"""You are a code agent planning how to accomplish a goal. 

Goal: {goal}

Project Context:
{context}

Create a detailed execution plan with specific actions. You can ONLY use these action types:
- read_file: Read and analyze an existing file
- write_file: Modify content of an existing file  
- create_file: Create a new file with content
- analyze_code: Analyze code structure and patterns
- search_codebase: Search through project files

Return a JSON plan with this exact structure:
{{
    "reasoning": "Explanation of your approach",
    "estimated_complexity": 5,
    "safety_level": 3,
    "steps": [
        {{
            "type": "read_file",
            "target": "path/to/file.py",
            "content": "",
            "reasoning": "why this step is needed"
        }},
        {{
            "type": "create_file", 
            "target": "path/to/new_file.py",
            "content": "# File content here",
            "reasoning": "why this step is needed"
        }}
    ]
}}

IMPORTANT:
- Use ONLY the exact action types listed above
- estimated_complexity: number from 1-10
- safety_level: number from 1-5
- For write_file and create_file, include actual content
- Keep steps atomic and specific. Maximum 8 steps."""

        response = self.llm_manager.get_completion([
            {"role": "system", "content": "You are a helpful code agent that creates detailed execution plans."},
            {"role": "user", "content": planning_prompt}
        ])
        
        try:
            # Extract JSON from response
            plan_data = self._extract_json_from_response(response)
            
            # Convert to our objects with validation
            actions = []
            for step in plan_data.get("steps", []):
                try:
                    # Validate action type
                    action_type_str = step.get("type", "").lower()
                    
                    # Map to valid action types
                    if action_type_str == "read_file":
                        action_type = ActionType.READ_FILE
                    elif action_type_str == "write_file":
                        action_type = ActionType.WRITE_FILE
                    elif action_type_str == "create_file":
                        action_type = ActionType.CREATE_FILE
                    elif action_type_str == "analyze_code":
                        action_type = ActionType.ANALYZE_CODE
                    elif action_type_str == "search_codebase":
                        action_type = ActionType.SEARCH_CODEBASE
                    else:
                        self.console.print(f"[yellow]Warning: Invalid action type '{step.get('type')}', skipping step[/yellow]")
                        continue
                    
                    action = Action(
                        type=action_type,
                        target=step.get("target", ""),
                        content=step.get("content", ""),
                        reasoning=step.get("reasoning", "No reasoning provided")
                    )
                    actions.append(action)
                    
                except Exception as e:
                    self.console.print(f"[yellow]Warning: Skipping invalid step: {e}[/yellow]")
                    continue
            
            # Ensure we have at least one valid action
            if not actions:
                self.console.print("[yellow]No valid actions found, creating fallback plan[/yellow]")
                actions = [Action(ActionType.ANALYZE_CODE, ".", reasoning="Fallback analysis - no valid actions in plan")]
            
            plan = ExecutionPlan(
                goal=goal,
                steps=actions,
                estimated_complexity=max(1, min(10, int(plan_data.get("estimated_complexity", 5)))),
                safety_level=max(1, min(5, int(plan_data.get("safety_level", 3)))),
                reasoning=plan_data.get("reasoning", "AI-generated execution plan")
            )
            
            return plan
            
        except Exception as e:
            self.console.print(f"[red]Planning error: {e}[/red]")
            # Create a simple fallback plan
            return ExecutionPlan(
                goal=goal,
                steps=[Action(ActionType.ANALYZE_CODE, ".", reasoning="Fallback analysis due to planning error")],
                estimated_complexity=5,
                safety_level=3,
                reasoning=f"Fallback plan due to planning error: {str(e)}"
            )
    
    def _validate_and_approve_plan(self, plan: ExecutionPlan, auto_approve: bool) -> bool:
        """Validate the plan and get user approval if needed"""
        
        # Display the plan
        self._display_plan(plan)
        
        # Check safety constraints
        if plan.safety_level >= 4:
            self.console.print("\n[yellow]High-risk operations detected![/yellow]")
            if not auto_approve:
                from rich.prompt import Confirm
                if not Confirm.ask("This plan involves potentially risky operations. Continue?"):
                    return False
        
        # Get approval for moderate complexity
        if plan.estimated_complexity >= 7 and not auto_approve:
            from rich.prompt import Confirm
            if not Confirm.ask("This is a complex plan. Proceed with execution?"):
                return False
        
        return True
    
    def _display_plan(self, plan: ExecutionPlan):
        """Display the execution plan to the user"""
        
        # Create plan summary
        summary_table = Table(show_header=False, box=None)
        summary_table.add_column("", style="bold")
        summary_table.add_column("")
        
        summary_table.add_row("Goal:", plan.goal)
        summary_table.add_row("Reasoning:", plan.reasoning)
        summary_table.add_row("Complexity:", f"{plan.estimated_complexity}/10")
        summary_table.add_row("Safety Level:", f"{plan.safety_level}/5")
        summary_table.add_row("Steps:", str(len(plan.steps)))
        
        self.console.print(Panel(summary_table, title="Execution Plan", border_style="blue"))
        
        # Display steps
        steps_table = Table(show_header=True, header_style="bold magenta")
        steps_table.add_column("#", style="dim", width=3)
        steps_table.add_column("Action", style="cyan")
        steps_table.add_column("Target", style="green")
        steps_table.add_column("Reasoning", style="dim")
        
        for i, step in enumerate(plan.steps, 1):
            steps_table.add_row(
                str(i),
                step.type.value.replace("_", " ").title(),
                step.target,
                step.reasoning[:50] + "..." if len(step.reasoning) > 50 else step.reasoning
            )
        
        self.console.print(steps_table)
    
    def _execute_plan(self) -> bool:
        """Execute the planned actions"""
        self.console.print("\n[green]Execution phase...[/green]")
        
        success_count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            
            for i, action in enumerate(self.current_plan.steps):
                task = progress.add_task(f"Step {i+1}: {action.type.value}", total=1)
                
                self.state = AgentState.ACTING
                result = self._execute_action(action)
                self.action_history.append((action, result))
                
                self.state = AgentState.OBSERVING
                if result.success:
                    success_count += 1
                    progress.update(task, completed=1, description=f"Step {i+1}: {action.type.value}")
                else:
                    progress.update(task, completed=1, description=f"Step {i+1}: {action.type.value}")
                    
                    # Reflection and potential recovery
                    self.state = AgentState.REFLECTING
                    if not self._handle_action_failure(action, result):
                        self.console.print(f"[red]Failed to recover from error in step {i+1}[/red]")
                        break
        
        # Final state
        if success_count == len(self.current_plan.steps):
            self.state = AgentState.COMPLETED
            self.console.print("\n[bold green]All steps completed successfully![/bold green]")
            return True
        else:
            self.state = AgentState.FAILED
            self.console.print(f"\n[yellow]Completed {success_count}/{len(self.current_plan.steps)} steps[/yellow]")
            return False
    
    def _execute_action(self, action: Action) -> ActionResult:
        """Execute a single action"""
        
        try:
            if action.type == ActionType.READ_FILE:
                return self._read_file_action(action)
            elif action.type == ActionType.WRITE_FILE:
                return self._write_file_action(action)
            elif action.type == ActionType.CREATE_FILE:
                return self._create_file_action(action)
            elif action.type == ActionType.ANALYZE_CODE:
                return self._analyze_code_action(action)
            elif action.type == ActionType.SEARCH_CODEBASE:
                return self._search_codebase_action(action)
            else:
                return ActionResult(False, error=f"Unknown action type: {action.type}")
                
        except Exception as e:
            return ActionResult(False, error=str(e))
    
    def _read_file_action(self, action: Action) -> ActionResult:
        """Execute a read file action"""
        content = read_file_content(action.target)
        
        if content.startswith("Error:"):
            return ActionResult(False, error=content)
        
        # Store in memory for later use
        self.memory[f"file_content_{action.target}"] = content
        
        return ActionResult(True, output=f"Read {len(content)} characters from {action.target}")
    
    def _write_file_action(self, action: Action) -> ActionResult:
        """Execute a write file action"""
        if not action.content:
            return ActionResult(False, error="No content provided for write operation")
        
        success = write_file_content(action.target, action.content)
        
        if success:
            return ActionResult(True, output=f"Successfully wrote {len(action.content)} characters to {action.target}")
        else:
            return ActionResult(False, error=f"Failed to write to {action.target}")
    
    def _create_file_action(self, action: Action) -> ActionResult:
        """Execute a create file action"""
        file_path = Path(action.target)
        
        if file_path.exists():
            return ActionResult(False, error=f"File {action.target} already exists")
        
        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        success = write_file_content(action.target, action.content)
        
        if success:
            return ActionResult(True, output=f"Successfully created {action.target} with {len(action.content)} characters")
        else:
            return ActionResult(False, error=f"Failed to create {action.target}")
    
    def _analyze_code_action(self, action: Action) -> ActionResult:
        """Execute a code analysis action"""
        # Use the context manager for analysis
        context = self.context_manager.get_context_for_query(f"analyze {action.target}")
        
        analysis_prompt = f"""Analyze the following code/project structure:

Target: {action.target}
Context: {context}

Provide a concise analysis focusing on:
1. Code structure and organization
2. Potential issues or improvements
3. Dependencies and relationships
4. Key findings

Keep the analysis practical and actionable."""

        response = self.llm_manager.get_completion([
            {"role": "system", "content": "You are a code analyst providing concise, actionable insights."},
            {"role": "user", "content": analysis_prompt}
        ])
        
        # Store analysis in memory
        self.memory[f"analysis_{action.target}"] = response
        
        return ActionResult(True, output=response)
    
    def _search_codebase_action(self, action: Action) -> ActionResult:
        """Execute a codebase search action"""
        # Use context manager's search capabilities
        context = self.context_manager.get_context_for_query(action.target)
        
        return ActionResult(True, output=f"Search results for '{action.target}': {len(context)} characters of context found")
    
    def _handle_action_failure(self, action: Action, result: ActionResult) -> bool:
        """Handle action failure and attempt recovery"""
        
        self.console.print(f"\n[yellow]Attempting to recover from failure...[/yellow]")
        self.console.print(f"[dim]Error: {result.error}[/dim]")
        
        # Simple retry logic for file operations
        if action.type in [ActionType.READ_FILE, ActionType.WRITE_FILE]:
            # Could implement retry with different paths, permissions, etc.
            return False
        
        # For other types, could implement more sophisticated recovery
        return False
    
    def _extract_json_from_response(self, response: str) -> Dict:
        """Extract JSON from LLM response"""
        # Remove markdown code blocks if present
        clean_response = response.strip()
        
        if clean_response.startswith("```json"):
            clean_response = clean_response[7:]
        elif clean_response.startswith("```"):
            clean_response = clean_response[3:]
            
        if clean_response.endswith("```"):
            clean_response = clean_response[:-3]
        
        clean_response = clean_response.strip()
        
        # Try to find JSON in the response
        start_idx = clean_response.find('{')
        end_idx = clean_response.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            # Try to find JSON in original response as fallback
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx == -1 or end_idx == 0:
                raise ValueError(f"No JSON found in response. Response was: {response[:200]}...")
            json_str = response[start_idx:end_idx]
        else:
            json_str = clean_response[start_idx:end_idx]
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}. JSON was: {json_str[:200]}...")
    
    def _log_session_to_history(self):
        """Log the entire agent session to history"""
        session_summary = {
            "session_id": self.session_id,
            "goal": self.current_plan.goal if self.current_plan else "Unknown",
            "state": self.state.value,
            "steps_completed": len([r for _, r in self.action_history if r.success]),
            "total_steps": len(self.action_history),
            "complexity": self.current_plan.estimated_complexity if self.current_plan else 0,
        }
        
        files_involved = []
        for action, _ in self.action_history:
            if action.target not in files_involved:
                files_involved.append(action.target)
        
        self.context_manager.log_interaction(
            query=f"Agent Goal: {self.current_plan.goal if self.current_plan else 'Unknown'}",
            response_summary=f"Agent session completed with {session_summary['steps_completed']}/{session_summary['total_steps']} successful steps",
            files_involved=files_involved
        )
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current session"""
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "goal": self.current_plan.goal if self.current_plan else None,
            "steps_completed": len([r for _, r in self.action_history if r.success]),
            "total_steps": len(self.action_history),
            "memory_items": len(self.memory),
            "action_history": [(asdict(a), asdict(r)) for a, r in self.action_history]
        }
