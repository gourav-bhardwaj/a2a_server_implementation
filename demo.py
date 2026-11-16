import os
import asyncio
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel, set_tracing_disabled
from dotenv import load_dotenv

load_dotenv(override=True)

# 1. Disable tracing to prevent the SDK from trying to push logs to OpenAI servers
set_tracing_disabled(True)

# 2. Configure the client to target Ollama
ollama_client = AsyncOpenAI(
    base_url="http://localhost:11434/v1",
    api_key=os.getenv("OLLAMA_API_KEY")  # A dummy key is required but ignored by Ollama
)

# 3. Create the model wrapper
local_model = OpenAIChatCompletionsModel(
    model="deepseek-r1:latest", 
    openai_client=ollama_client
)

# 4. Assign the model to your Agent
reasoning_agent = Agent(
    name="DeepSeek Reasoning Agent",
    instructions="You are a meticulous assistant. Show your reasoning step by step.",
    model=local_model
)

async def main():
    result = await Runner.run(reasoning_agent, "Explain the difference between a stack and a queue.")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
