import asyncio
import os
from typing import Optional
from browser_use import Agent, ChatOpenAI, Browser


class BrowserService:
    """Service for managing browser automation using browser-use"""

    def __init__(self):
        self.agent: Optional[Agent] = None

        # Configuration from environment
        self.headless = os.getenv("BROWSER_HEADLESS", "false").lower() == "true"
        self.width = int(os.getenv("BROWSER_WIDTH", "1920"))
        self.height = int(os.getenv("BROWSER_HEIGHT", "1080"))

    async def start(self):
        """Initialize browser-use agent with connection to existing Chrome debug port"""
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

            # Wait for Chrome debug port to be ready
            print("Waiting for Chrome debug port...")
            await self._wait_for_debug_port()

            # Create Browser instance to CONNECT to existing Chrome with debug port
            browser = Browser(
                cdp_url='http://localhost:9222'  # Connect to existing Chrome debug port
            )

            # Create agent - browser-use will connect to existing Chrome
            self.agent = Agent(
                task="",  # Will be set when executing tasks
                llm=llm,
                browser=browser
            )

            print("Browser service connected to existing Chrome on debug port 9222")

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

    async def _wait_for_debug_port(self, max_retries=10):
        """Wait for Chrome debug port to be ready"""
        import aiohttp

        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://localhost:9222/json/version", timeout=2) as response:
                        if response.status == 200:
                            data = await response.json()
                            print(f"Chrome debug port ready: {data.get('Browser', 'Unknown')}")
                            return
            except Exception as e:
                print(f"Attempt {attempt + 1}/{max_retries}: Chrome debug port not ready - {e}")
                await asyncio.sleep(2)

        raise Exception("Chrome debug port not available after maximum retries")

    def get_agent(self):
        """Get the browser-use agent instance"""
        return self.agent