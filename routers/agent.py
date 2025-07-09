from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.callbacks.base import AsyncCallbackHandler
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_KEY")

router = APIRouter()

class JiraRequest(BaseModel):
    user_input: str
    story_count: int = 10


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


@router.post("/generate-jira-story-stream")
async def generate_jira_story_stream(payload: JiraRequest):
    user_input = payload.user_input.strip()
    story_count = payload.story_count

    if not user_input:
        raise HTTPException(status_code=400, detail="user_input is required")
    if story_count <= 0 or story_count > 500:
        raise HTTPException(status_code=400, detail="story_count must be between 1 and 500")

    batch_size = 10
    num_batches = story_count // batch_size
    remaining = story_count % batch_size

    async def batch_stream():
        yield '{"user_stories": ['

        first_story = True

        for batch_num in range(num_batches + (1 if remaining else 0)):
            current_batch_size = (
                remaining if (batch_num == num_batches and remaining) else batch_size
            )

            handler = StreamHandler()
            llm = ChatOpenAI(
                openai_api_key=OPENAI_KEY,
                model="gpt-4",
                streaming=True,
                callbacks=[handler],
                temperature=0,
            )

            prompt = f"""
You are a Business Analyst. From the following requirement, generate {current_batch_size} unique and detailed Jira user stories in **STRICTLY** this JSON array format (no extra text):

[
  {{
    "title": "Short descriptive title (max 50 characters)",
    "issue_type": "frontend|backend|database|devops|qa|Python developer",
    "story_type": "Feature|Bug|Task|Epic",
    "description": "Detailed description of what needs to be implemented",
    "priority": "High|Medium|Low",
    "story_points": "1|2|3|5|8|13",
    "labels": ["label1", "label2", "label3"],
    "acceptance_criteria": [
      "Given/When/Then criterion 1",
      "Given/When/Then criterion 2"
    ]
  }},
  ...
]

IMPORTANT:
- Do NOT return markdown or additional explanation.
- DO NOT wrap the array in an object or return any surrounding text.
- Ensure each story is clean JSON.

Requirement: "{user_input}"
            """.strip()

            try:
                await asyncio.wait_for(llm.ainvoke([{"role": "user", "content": prompt}]), timeout=120)
            except asyncio.TimeoutError:
                await handler.queue.put("[[END]]")

            buffer = ""
            async for token in handler.stream():
                buffer += token

            buffer = buffer.strip()
            if buffer.startswith("["):
                buffer = buffer[1:]
            if buffer.endswith("]"):
                buffer = buffer[:-1]

            # Insert comma if not first story
            if buffer:
                if not first_story:
                    yield ","
                yield buffer
                first_story = False

        # Final meta object
        yield '],'  # Close the user_stories array
        yield f'"story_count": {story_count},'
        yield f'"meta": {{"message": "Generated {story_count} stories"}}'
        yield '}'

    return StreamingResponse(batch_stream(), media_type="application/json")
