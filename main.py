import asyncio
import os

from browser_use.llm.deepseek.chat import ChatDeepSeek
from dotenv import load_dotenv
from browser_use import Agent, Browser

load_dotenv()
import logging

logging.basicConfig(level=logging.DEBUG)


async def main():
    browser = Browser(
        headless=False,  # Show browser window
        window_size={'width': 1000, 'height': 700},  # Set window size
        allowed_domains=["*"]
    )

    # dpsk_llm = ChatOpenAI(
    #     model="deepseek-chat",
    #     temperature=0.0,
    #     base_url="https://api.deepseek.com/v1",
    #     api_key=os.getenv("DEEPSEEK_API_KEY"),
    # )

    openrouter_llm = ChatDeepSeek(
        temperature=0.0,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        model="deepseek/deepseek-chat-v3.1:free",
    )
    # Define a form filling task
    task = """
        Go to https://httpbin.org/forms/post and fill out the contact form with:
        - Customer name: John Doe
        - Telephone: 555-123-4567
        - Email: john.doe@example.com
        - Size: Medium
        - Topping: cheese
        - Delivery time: now
        - Comments: This is a test form submission

        Then submit the form and tell me what response you get.
        """
    agent = Agent(
        task=task,
        browser=browser,
        use_vision=False,
        llm=openrouter_llm
    )
    await agent.run()


asyncio.run(main())
