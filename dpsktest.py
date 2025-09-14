# Please install OpenAI SDK first: `pip3 install openai`
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()
client = OpenAI(base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
    ],
    stream=False
)

print(response.choices[0].message.content)