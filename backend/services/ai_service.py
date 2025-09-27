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

        # Initialize AI client (OpenAI or OpenRouter)
        openai_api_key = os.getenv("OPENAI_API_KEY")
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

        if openai_api_key:
            # Use OpenAI directly
            self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        elif openrouter_api_key:
            # Use OpenRouter as OpenAI-compatible API
            self.openai_client = AsyncOpenAI(
                api_key=openrouter_api_key,
                base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
            )

    async def create_task(self, instruction: str) -> str:
        """Create a new AI task"""
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

        task = self.tasks[task_id]
        task["status"] = "running"

        yield {
            "type": "task_update",
            "task_id": task_id,
            "status": "running",
            "message": "Starting task execution..."
        }

        try:
            # Create AI agent for this task
            if self.openai_client:
                # Determine which API to use and set appropriate model
                openai_api_key = os.getenv("OPENAI_API_KEY")
                openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

                if openai_api_key:
                    # Use OpenAI directly
                    llm = ChatOpenAI(
                        model="gpt-4o",
                        api_key=openai_api_key
                    )
                elif openrouter_api_key:
                    # Use OpenRouter with Gemini 2.5 Flash (recommended)
                    llm = ChatOpenAI(
                        model="google/gemini-2.5-flash",  # Gemini 2.5 Flash via OpenRouter
                        api_key=openrouter_api_key,
                        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
                    )
                else:
                    raise ValueError("No AI API key configured")

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
                yield {
                    "type": "task_complete",
                    "task_id": task_id,
                    "status": "completed"
                }

        except Exception as e:
            task["status"] = "failed"
            yield {
                "type": "error",
                "task_id": task_id,
                "message": f"Task execution failed: {str(e)}"
            }

    async def _execute_agent_task(self, agent: Agent, task_id: str) -> AsyncGenerator[Dict, None]:
        """Execute browser-use agent task with streaming updates"""
        try:
            # Run the agent and capture steps
            history = await agent.run(max_steps=20)

            # Stream each step as it completes
            for i, step in enumerate(history):
                step_data = {
                    "type": "step_update",
                    "task_id": task_id,
                    "step_number": i + 1,
                    "action": step.get("action", "unknown"),
                    "description": step.get("result", ""),
                    "screenshot": None  # Could add screenshot data here
                }

                self.tasks[task_id]["steps"].append(step_data)
                yield step_data

                # Small delay to show progress
                await asyncio.sleep(0.5)

        except Exception as e:
            yield {
                "type": "step_error",
                "task_id": task_id,
                "message": f"Agent execution error: {str(e)}"
            }

    async def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get current task status"""
        return self.tasks.get(task_id)

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

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=1000
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"OpenAI analysis error: {str(e)}"