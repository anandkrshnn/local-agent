"""
Agent Team Orchestrator for Sprint 6
Implements the Blackboard pattern for multi-agent collaboration
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field

@dataclass
class TeamMember:
    role: str
    specialty: str
    model: str = "phi3:mini"
    personality: str = "helpful and concise"

@dataclass
class TaskResult:
    agent_role: str
    output: str
    success: bool
    time_taken: float
    timestamp: datetime = field(default_factory=datetime.now)

class AgentTeam:
    """
    Orchestrates a team of specialized agents to solve complex tasks.
    Uses a Shared Blackboard for communication and context sharing.
    """
    
    def __init__(self, team_id: str = "default_team"):
        self.team_id = team_id
        self.blackboard: Dict[str, Any] = {}
        self.results: List[TaskResult] = []
        self.members: Dict[str, TeamMember] = {}
        self.performance: Dict[str, List[float]] = {}
        
        # Initialize default team
        self._setup_default_team()

    def _setup_default_team(self):
        self.members["planner"] = TeamMember("planner", "task decomposition and strategy")
        self.members["researcher"] = TeamMember("researcher", "document analysis and fact-finding")
        self.members["coder"] = TeamMember("coder", "code generation and debugging")
        self.members["reviewer"] = TeamMember("reviewer", "quality assurance and optimization")

    async def orchestrate(self, user_request: str) -> str:
        """
        Main orchestration loop:
        1. Plan -> 2. Research/Execute -> 3. Review -> 4. Final Result
        """
        start_time = time.time()
        print(f"👥 Team {self.team_id} starting orchestration for: {user_request[:50]}...")
        
        # 1. Planning Step
        plan = await self._run_agent_task("planner", f"Create a step-by-step plan for: {user_request}")
        self.blackboard["current_plan"] = plan
        
        # 2. Execution Step (Simplified for demo)
        # In a real system, we'd loop through the plan steps
        execution_result = await self._run_agent_task("coder", f"Execute this plan: {plan}")
        self.blackboard["execution_output"] = execution_result
        
        # 3. Review Step
        final_review = await self._run_agent_task("reviewer", f"Critique and finalize this output: {execution_result}")
        
        duration = time.time() - start_time
        print(f"✅ Team {self.team_id} completed task in {duration:.2f}s")
        
        return final_review

    async def _run_agent_task(self, role: str, task: str) -> str:
        """Simulates calling a specialized agent"""
        agent = self.members.get(role)
        if not agent:
            raise ValueError(f"Agent role {role} not found in team")
            
        # Here we would call the Orchestrator/Broker with the agent's specific system prompt
        # and the blackboard context.
        # For this prototype, we'll simulate the response.
        
        # Simulate local SLM latency
        await asyncio.sleep(0.5)
        
        result_text = f"[{role.upper()} OUTPUT] Processed task: {task[:50]}..."
        self.results.append(TaskResult(role, result_text, True, 0.5))
        
        # Track performance
        if role not in self.performance: self.performance[role] = []
        self.performance[role].append(0.5)
        
        return result_text

    def get_team_stats(self) -> Dict:
        """Get summary of team performance"""
        return {
            "team_id": self.team_id,
            "total_tasks": len(self.results),
            "members": list(self.members.keys()),
            "avg_latency": sum(r.time_taken for r in self.results) / len(self.results) if self.results else 0
        }

# Singleton instance
agent_team = AgentTeam()
