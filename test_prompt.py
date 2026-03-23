
import asyncio
from services.prompt_service import PromptService

async def main():
    ps = PromptService()
    prompt = await ps.build_prompt("a cowboy is riding a horse and a cigger in his mouth", "color", "intermediate")
    with open("prompt_out.txt", "w", encoding="utf-8") as f:
        f.write(prompt[0])

asyncio.run(main())

