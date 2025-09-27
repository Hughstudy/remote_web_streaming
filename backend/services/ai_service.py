import asyncio
import os
import uuid
from typing import Dict, AsyncGenerator, Optional
from openai import AsyncOpenAI


class AIService:
    """Service for managing AI agents and task execution"""

    def __init__(self, browser_service=None):
        self.openai_client: Optional[AsyncOpenAI] = None
        self.tasks: Dict[str, Dict] = {}
        self.current_running_task: Optional[str] = None
        self.browser_service = browser_service

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
            # Use the centralized browser service
            if not self.browser_service:
                raise ValueError("Browser service not available")

            # Execute the task and stream updates
            async for step in self._execute_browser_task(task["instruction"], task_id):
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

    async def _execute_browser_task(self, instruction: str, task_id: str) -> AsyncGenerator[Dict, None]:
        """Execute browser task using centralized browser service with streaming updates"""
        try:
            # Yield start message
            yield {
                "type": "step_update",
                "task_id": task_id,
                "step_number": 1,
                "action": "initializing",
                "description": "Starting browser automation with browser-use agent..."
            }

            # Execute task using browser service
            result = await self.browser_service.execute_task(instruction, max_steps=10)

            # Yield completion message
            yield {
                "type": "step_update",
                "task_id": task_id,
                "step_number": 2,
                "action": "completed",
                "description": f"Task completed successfully. Result: {str(result)[:200] if result else 'No result returned'}"
            }

            # Store the result
            self.tasks[task_id]["result"] = result

        except Exception as e:
            error_msg = f"Browser task execution error: {str(e)}"
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