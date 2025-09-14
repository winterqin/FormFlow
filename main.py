import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
from browser_use import Agent, Browser, ChatOpenAI


async def main():
    browser = Browser(
        headless=False,  # Show browser window
        window_size={'width': 1000, 'height': 700},  # Set window size
        allowed_domains=["*"]
    )

    llm = ChatOpenAI(
        model="deepseek-chat",
        temperature=0.0,
        base_url="https://api.deepseek.com/v1",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
    )

    agent = Agent(
        task="前往http://www.resumego.xyz/login页面,输入账号:qinwinter@qq.com密码: qwt123登录网站",
        browser=browser,
        use_vision=False,
        llm=llm
    )
    await agent.run()

asyncio.run(main())
