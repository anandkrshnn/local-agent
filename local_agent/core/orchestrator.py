"""
Agent Orchestrator - Multi-step reasoning and planning
Breaks down complex goals into executable task sequences
"""

import json
import asyncio
import uuid
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

@dataclass
class Task:
    """Individual task in execution plan"""
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    result: Any = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None

@dataclass
class ExecutionPlan:
    """Complete plan for goal execution"""
    goal: str
    tasks: List[Task]
    created_at: float = field(default_factory=time.time)
    status: str = "pending"  # pending, running, completed, failed

class AgentOrchestrator:
    """
    Orchestrates multi-step tasks for complex goals.
    Uses LLM to plan and execute task sequences.
    """
    
    def __init__(self, agent):
        self.agent = agent
        self.active_plans: Dict[float, ExecutionPlan] = {}
        self.plan_history: List[ExecutionPlan] = []
    
    async def plan(self, goal: str, max_tasks: int = 10) -> ExecutionPlan:
        """
        Break down goal into executable tasks using LLM
        """
        prompt = f"""You are a task planning AI. Break down the goal into a sequence of executable tasks.

Goal: {goal}

Rules:
1. Each task should be a single, actionable step.
2. Order by dependency.
3. Maximum {max_tasks} tasks.
4. Output ONLY the JSON block, no conversational text.

JSON Format:
{{
    "tasks": [
        {{
            "id": "task_1",
            "description": "read the file data.txt",
            "dependencies": []
        }},
        {{
            "id": "task_2", 
            "description": "write the analysis to report.txt",
            "dependencies": ["task_1"]
        }}
    ]
}}

Output JSON:"""
        
        try:
            # Use ModelRouter if available, otherwise fallback to basic generate
            if hasattr(self.agent, 'model_router'):
                response_obj = self.agent.model_router.route(prompt)
                response = response_obj.content
            else:
                response = await asyncio.to_thread(
                    self.agent.llm.generate, 
                    prompt,
                    temperature=0.3
                )
            
            # Extract JSON
            import re
            json_match = re.search(r'\{[^{}]*"tasks"[^{}]*\[.*?\]\s*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                # Try parsing entire response
                data = json.loads(response)
            
            tasks = []
            for task_data in data.get('tasks', []):
                task = Task(
                    id=task_data['id'],
                    description=task_data['description'],
                    dependencies=task_data.get('dependencies', [])
                )
                tasks.append(task)
            
            plan = ExecutionPlan(
                goal=goal,
                tasks=tasks
            )
            
            self.active_plans[plan.created_at] = plan
            return plan
            
        except Exception as e:
            # Fallback: create simple plan
            print(f"Planning error: {e}, using fallback plan")
            task = Task(
                id="task_1",
                description=goal
            )
            plan = ExecutionPlan(goal=goal, tasks=[task])
            self.active_plans[plan.created_at] = plan
            return plan
    
    async def execute(self, plan: ExecutionPlan, max_iterations: int = 20) -> Dict[str, Any]:
        """
        Execute a plan with dependency resolution
        """
        plan.status = "running"
        completed_tasks = set()
        task_results = {}
        task_errors = {}
        
        iteration = 0
        while len(completed_tasks) < len(plan.tasks) and iteration < max_iterations:
            iteration += 1
            
            # Find executable tasks (pending, dependencies met)
            executable = []
            for task in plan.tasks:
                if task.status != TaskStatus.PENDING:
                    continue
                
                # Check dependencies
                deps_met = all(dep in completed_tasks for dep in task.dependencies)
                if deps_met:
                    executable.append(task)
            
            if not executable:
                # Deadlock detection
                break
            
            # Execute tasks
            for task in executable:
                task.status = TaskStatus.IN_PROGRESS
                
                try:
                    # Execute the task using agent chat (running in a thread since chat is sync)
                    result = await asyncio.to_thread(
                        self.agent.chat,
                        task.description
                    )
                    
                    task.status = TaskStatus.COMPLETED
                    task.result = result
                    task.completed_at = time.time()
                    completed_tasks.add(task.id)
                    task_results[task.id] = result
                    
                    # Store in memory
                    self.agent.memory.store("task_completed", {
                        "plan_goal": plan.goal[:100],
                        "task_description": task.description,
                        "result": str(result)[:500]
                    })
                    
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    task_errors[task.id] = str(e)
                    
                    # Abort if critical
                    if "critical" in task.description.lower():
                        plan.status = "failed"
                        return {
                            "success": False,
                            "completed_tasks": len(completed_tasks),
                            "total_tasks": len(plan.tasks),
                            "results": task_results,
                            "errors": task_errors
                        }
        
        plan.status = "completed" if len(completed_tasks) == len(plan.tasks) else "partial"
        
        # Generate summary
        summary = await self._generate_summary(plan, task_results, task_errors)
        
        # Store in history
        self.plan_history.append(plan)
        
        return {
            "success": plan.status == "completed",
            "plan_id": plan.created_at,
            "completed_tasks": len(completed_tasks),
            "total_tasks": len(plan.tasks),
            "results": task_results,
            "errors": task_errors,
            "summary": summary
        }
    
    async def _generate_summary(self, plan: ExecutionPlan, results: Dict, errors: Dict) -> str:
        """Generate human-readable summary of execution"""
        if not results and not errors:
            return "No tasks were executed."
        
        prompt = f"""Goal: {plan.goal}

Completed tasks ({len(results)}):
{json.dumps(results, indent=2)[:1000]}

Failed tasks ({len(errors)}):
{json.dumps(errors, indent=2)[:500]}

Provide a concise summary of what was accomplished and any issues encountered.
"""
        
        try:
            if hasattr(self.agent, 'model_router'):
                response_obj = self.agent.model_router.route(prompt)
                return response_obj.content
            else:
                return await asyncio.to_thread(self.agent.llm.generate, prompt, temperature=0.5)
        except:
            return f"Completed {len(results)} of {len(plan.tasks)} tasks. {len(errors)} tasks failed."
    
    def get_status(self, plan_id: float = None) -> Dict:
        """Get status of active or recent plans"""
        if plan_id:
            plan = self.active_plans.get(plan_id)
            if plan:
                return {
                    "goal": plan.goal,
                    "status": plan.status,
                    "tasks": [
                        {
                            "id": t.id,
                            "description": t.description,
                            "status": t.status.value,
                            "error": t.error
                        }
                        for t in plan.tasks
                    ]
                }
            return {"error": "Plan not found"}
        
        return {
            "active_plans": len(self.active_plans),
            "total_plans": len(self.plan_history),
            "recent_plan": self.plan_history[-1].goal if self.plan_history else None
        }
