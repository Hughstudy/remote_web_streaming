import asyncio
import os
import uuid
from typing import Dict, AsyncGenerator, Optional
from openai import AsyncOpenAI
from browser_use import Agent, ChatOpenAI


class AIService:
    """Service for managing AI agents and task execution"""

    def __init__(self):
        self.openai_client: Optional[AsyncOpenAI] = None
        self.tasks: Dict[str, Dict] = {}
        self.agents: Dict[str, Agent] = {}
        self.current_running_task: Optional[str] = None

        # Initialize AI client (OpenRouter via OpenAI-compatible API)
        openai_api_key = os.getenv("OPENAI_API_KEY")
        openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

        if openai_api_key:
            self.openai_client = AsyncOpenAI(
                api_key=openai_api_key,
                base_url=openai_base_url
            )

    async def create_task(self, instruction: str) -> str:
        """Create a new AI task"""
        # Check if there's already a running task
        if self.current_running_task and self.current_running_task in self.tasks:
            current_task = self.tasks[self.current_running_task]
            if current_task["status"] == "running":
                raise ValueError("Cannot create new task: another task is currently running")

        task_id = str(uuid.uuid4())

        self.tasks[task_id] = {
            "id": task_id,
            "instruction": instruction,
            "status": "created",
            "steps": [],
            "result": None
        }

        return task_id

    async def execute_task(self, task_id: str) -> AsyncGenerator[Dict, None]:
        """Execute a task with browser-use agent"""
        if task_id not in self.tasks:
            yield {"type": "error", "message": "Task not found"}
            return

        # Check if another task is already running
        if self.current_running_task and self.current_running_task != task_id:
            yield {"type": "error", "message": "Another task is currently running"}
            return

        task = self.tasks[task_id]
        task["status"] = "running"
        self.current_running_task = task_id

        yield {
            "type": "task_update",
            "task_id": task_id,
            "status": "running",
            "message": "Starting task execution..."
        }

        try:
            # Create AI agent for this task
            if self.openai_client:
                openai_api_key = os.getenv("OPENAI_API_KEY")
                openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

                if not openai_api_key:
                    raise ValueError("No OPENAI_API_KEY configured")

                # Use Gemini 2.5 Flash model (works with both OpenAI and OpenRouter)
                model = "google/gemini-2.5-flash" if "openrouter" in openai_base_url else "gpt-4o"

                llm = ChatOpenAI(
                    model=model,
                    api_key=openai_api_key,
                    base_url=openai_base_url
                )

                agent = Agent(
                    task=task["instruction"],
                    llm=llm
                )

                self.agents[task_id] = agent

                # Execute the task and stream updates
                async for step in self._execute_agent_task(agent, task_id):
                    yield step

                # Mark task as completed
                task["status"] = "completed"
                self.current_running_task = None  # Clear running task
                yield {
                    "type": "task_complete",
                    "task_id": task_id,
                    "status": "completed"
                }

        except Exception as e:
            task["status"] = "failed"
            self.current_running_task = None  # Clear running task
            yield {
                "type": "error",
                "task_id": task_id,
                "message": f"Task execution failed: {str(e)}"
            }

    async def _execute_agent_task(self, agent: Agent, task_id: str) -> AsyncGenerator[Dict, None]:
        """Execute browser-use agent task with streaming updates"""
        try:
            # Yield start message
            yield {
                "type": "step_update",
                "task_id": task_id,
                "step_number": 1,
                "action": "initializing",
                "description": "Starting browser automation..."
            }

            # Run the agent
            history = await agent.run(max_steps=10)

            # Process and yield each step
            if history:
                for i, step in enumerate(history):
                    # Extract step information
                    action = getattr(step, 'action', 'unknown') if hasattr(step, 'action') else str(type(step).__name__)
                    result = getattr(step, 'result', '') if hasattr(step, 'result') else str(step)

                    step_data = {
                        "type": "step_update",
                        "task_id": task_id,
                        "step_number": i + 2,  # +2 because we start with initializing step
                        "action": action,
                        "description": result[:500] if result else f"Completed step {i+1}"  # Truncate long descriptions
                    }

                    self.tasks[task_id]["steps"].append(step_data)
                    yield step_data

                    # Small delay between steps
                    await asyncio.sleep(0.1)

            else:
                # If no history, yield a completion message
                yield {
                    "type": "step_update",
                    "task_id": task_id,
                    "step_number": 2,
                    "action": "completed",
                    "description": "Task completed successfully"
                }

        except Exception as e:
            error_msg = f"Agent execution error: {str(e)}"
            print(f"DEBUG: {error_msg}")  # Debug logging
            yield {
                "type": "step_error",
                "task_id": task_id,
                "message": error_msg
            }

    async def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get current task status"""
        return self.tasks.get(task_id)

    def is_task_running(self) -> bool:
        """Check if any task is currently running"""
        return (self.current_running_task is not None and
                self.current_running_task in self.tasks and
                self.tasks[self.current_running_task]["status"] == "running")

    def get_running_task_id(self) -> Optional[str]:
        """Get the ID of the currently running task"""
        if self.is_task_running():
            return self.current_running_task
        return None

    async def analyze_with_openai(self, prompt: str, screenshot_data: bytes = None) -> str:
        """Use OpenAI to analyze screenshot and provide next action"""
        if not self.openai_client:
            return "OpenAI client not available"

        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are an AI agent that controls web browsers. Analyze the current state and provide the next action to take."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            # Add screenshot if provided
            if screenshot_data:
                # Convert screenshot to base64 and add to message
                import base64
                screenshot_b64 = base64.b64encode(screenshot_data).decode()
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_b64}"
                            }
                        }
                    ]
                })

            # Use the same model selection logic
            openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            model = "google/gemini-2.5-flash" if "openrouter" in openai_base_url else "gpt-4o"

            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1000
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"OpenAI analysis error: {str(e)}"