import asyncio
import os
from typing import Optional
from browser_use import Agent, ChatOpenAI
from playwright.async_api import async_playwright, Browser, BrowserContext, Page


class BrowserService:
    """Service for managing browser automation using browser-use"""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.agent: Optional[Agent] = None

        # Configuration from environment
        self.headless = os.getenv("BROWSER_HEADLESS", "false").lower() == "true"
        self.width = int(os.getenv("BROWSER_WIDTH", "1920"))
        self.height = int(os.getenv("BROWSER_HEIGHT", "1080"))

    async def start(self):
        """Initialize browser and browser-use agent"""
        try:
            # Start Playwright
            self.playwright = await async_playwright().start()

            # Launch browser with display settings for VNC
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    f"--window-size={self.width},{self.height}",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    "--no-sandbox",
                    "--disable-dev-shm-usage"
                ]
            )

            # Create browser context
            self.context = await self.browser.new_context(
                viewport={"width": self.width, "height": self.height}
            )

            # Create initial page
            self.page = await self.context.new_page()

            # Initialize browser-use agent with AI provider
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
                llm = None
                print("Warning: No AI API key configured")

            if llm:
                # Create agent that will use our browser instance
                self.agent = Agent(
                    task="",  # Will be set when executing tasks
                    llm=llm,
                    browser=self.browser  # Pass our browser instance
                )

            print("Browser service started successfully")

        except Exception as e:
            print(f"Error starting browser service: {e}")
            raise

    async def stop(self):
        """Clean up browser resources"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            print("Browser service stopped")
        except Exception as e:
            print(f"Error stopping browser service: {e}")

    async def navigate_to(self, url: str):
        """Navigate to a specific URL"""
        if self.page:
            await self.page.goto(url)
            return await self.page.url

    async def get_page_info(self):
        """Get current page information"""
        if self.page:
            return {
                "url": self.page.url,
                "title": await self.page.title(),
                "viewport": self.page.viewport_size
            }
        return None

    async def take_screenshot(self) -> bytes:
        """Take a screenshot of the current page"""
        if self.page:
            return await self.page.screenshot()
        return None

    def get_browser_instance(self):
        """Get the browser instance for agent use"""
        return self.browser