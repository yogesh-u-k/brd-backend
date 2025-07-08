from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.callbacks.base import AsyncCallbackHandler
from config import OPENAI_KEY
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()
router = APIRouter()

# Request model with story_count included
class JiraRequest(BaseModel):
    user_input: str
    story_count: int = 30  # default if user doesn't pass this

# Streaming handler
class StreamHandler(AsyncCallbackHandler):
    def __init__(self):
        self.queue = asyncio.Queue()

    async def on_llm_new_token(self, token: str, **kwargs):
        await self.queue.put(token)

    async def on_llm_end(self, response, **kwargs):
        await self.queue.put("[[END]]")

    async def stream(self):
        while True:
            token = await self.queue.get()
            if token == "[[END]]":
                break
            yield token

# Streaming endpoint
@router.post("/generate-jira-story-stream")
async def generate_jira_story_stream(payload: JiraRequest):
    user_input = payload.user_input.strip()
    target_story_count = payload.story_count

    if not user_input:
        raise HTTPException(status_code=400, detail="user_input is required")
    if target_story_count <= 0 or target_story_count > 500:
        raise HTTPException(status_code=400, detail="story_count must be between 1 and 500")

    batch_size = 10
    num_batches = target_story_count // batch_size
    remaining = target_story_count % batch_size

    async def batch_stream():
        yield '{"user_stories": ['

        for batch_num in range(num_batches + (1 if remaining else 0)):
            current_batch_size = remaining if (batch_num == num_batches and remaining) else batch_size

            handler = StreamHandler()
            llm = ChatOpenAI(
                openai_api_key=os.getenv("OPENAI_API_KEY", OPENAI_KEY),
                model="gpt-4",
                streaming=True,
                callbacks=[handler],
                temperature=0,
            )

            prompt = f"""
You are a Business Analyst. From the following requirement, generate {current_batch_size} unique and detailed Jira user stories in this format:

[
    {{
        "title": "...",
        "summary": "...",
        "story_type": "Feature|Bug|Task|Epic",
        "description": "...",
        "priority": "High|Medium|Low",
        "story_points": "1|2|3|5|8|13",
        "labels": ["label1", "label2"],
        "acceptance_criteria": [
            "Given/When/Then 1",
            "Given/When/Then 2"
        ]
    }}
]

Requirement: "{user_input}"

Only return the array. Do not wrap in any object or explanation.
            """.strip()

            messages = [{"role": "system", "content": prompt}]
            asyncio.create_task(llm.ainvoke(messages))

            story_started = False
            async for token in handler.stream():
                if token.strip().startswith("[") and not story_started:
                    token = token.lstrip("[").strip()
                    story_started = True
                elif token.strip().endswith("]"):
                    token = token.rstrip("]").strip()

                if token:
                    yield token

            if batch_num < num_batches + (1 if remaining else 0) - 1:
                yield ","

        yield f'], "meta": {{"message": "Generated {target_story_count} stories"}}'

    return StreamingResponse(batch_stream(), media_type="application/json")
