import asyncio
import os
from typing import Optional
from browser_use import Agent, ChatOpenAI, BrowserProfile


class BrowserService:
    """Service for managing browser automation using browser-use"""

    def __init__(self):
        self.agent: Optional[Agent] = None

        # Configuration from environment
        self.headless = os.getenv("BROWSER_HEADLESS", "false").lower() == "true"
        self.width = int(os.getenv("BROWSER_WIDTH", "1920"))
        self.height = int(os.getenv("BROWSER_HEIGHT", "1080"))

    async def start(self):
        """Initialize browser-use agent with VNC display configuration"""
        try:
            # Ensure browser runs on VNC display
            os.environ["DISPLAY"] = ":1"

            # Initialize browser-use agent with AI provider
            openai_api_key = os.getenv("OPENAI_API_KEY")
            openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

            if openai_api_key:
                # Use Gemini 2.5 Flash model (works with both OpenAI and OpenRouter)
                model = "google/gemini-2.5-flash" if "openrouter" in openai_base_url else "gpt-4o"

                llm = ChatOpenAI(
                    model=model,
                    api_key=openai_api_key,
                    base_url=openai_base_url
                )
            else:
                raise Exception("No OPENAI_API_KEY configured")

            # Create browser profile for VNC display
            browser_profile = BrowserProfile(
                headless=self.headless,
                window_size={'width': self.width, 'height': self.height},
                viewport={'width': self.width, 'height': self.height},
                env={'DISPLAY': ':1'},  # Ensure VNC display
                args=[
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    "--no-sandbox",
                    "--disable-dev-shm-usage"
                ],
                keep_alive=True  # Keep browser running between tasks
            )

            # Create agent - browser-use will handle browser creation
            self.agent = Agent(
                task="",  # Will be set when executing tasks
                llm=llm,
                browser_profile=browser_profile
            )

            print("Browser service started successfully with browser-use")

        except Exception as e:
            print(f"Error starting browser service: {e}")
            raise

    async def stop(self):
        """Clean up browser resources"""
        try:
            # browser-use handles browser cleanup internally
            if self.agent:
                # Gracefully close agent if it has cleanup methods
                pass
            print("Browser service stopped")
        except Exception as e:
            print(f"Error stopping browser service: {e}")

    async def execute_task(self, instruction: str, max_steps: int = 10):
        """Execute a task using browser-use agent"""
        if not self.agent:
            raise Exception("Browser service not started")

        try:
            # Update agent task
            self.agent.task = instruction

            # Execute the task
            result = await self.agent.run(max_steps=max_steps)
            return result
        except Exception as e:
            print(f"Error executing task: {e}")
            raise

    def get_agent(self):
        """Get the browser-use agent instance"""
        return self.agent