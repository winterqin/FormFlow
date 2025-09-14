from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()
client = OpenAI()

completion = client.chat.completions.create(
  extra_body={},
  model="deepseek/deepseek-chat-v3.1:free",
  messages=[
    {
      "role": "user",
      "content": "hello"
    }
  ]
)
print(completion.choices[0].message.content)