
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from langchain_openai import ChatOpenAI
from langchain.callbacks.base import AsyncCallbackHandler
from langchain_community.document_loaders import PyMuPDFLoader, TextLoader, CSVLoader
from dotenv import load_dotenv
import tempfile, os, asyncio, json, io, pandas as pd
from typing import List

load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_KEY")
router = APIRouter()

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

def extract_batches_from_excel(file_bytes: bytes, batch_size: int = 10) -> List[List[str]]:
    try:
        df = pd.read_excel(io.BytesIO(file_bytes))

        if df.empty:
            raise ValueError("Uploaded Excel file is empty")

        row_texts = df.astype(str).apply(lambda row: " | ".join(row.values), axis=1).tolist()

        if not row_texts:
            raise ValueError("No usable rows found")

        return [row_texts[i:i + batch_size] for i in range(0, len(row_texts), batch_size)]

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse Excel: {str(e)}")


@router.post("/generate-stories-from-doc")
async def generate_stories_from_doc(file: UploadFile = File(...), story_count: int = 10):
    if story_count <= 0 or story_count > 500:
        raise HTTPException(status_code=400, detail="story_count must be between 1 and 500")

    file_ext = file.filename.lower().split('.')[-1]
    file_bytes = await file.read()

    # Load documents and split into batches
    if file_ext == 'pdf':
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, 'wb') as f:
            f.write(file_bytes)
        loader = PyMuPDFLoader(file_path)
        documents = loader.load()
        contents = [doc.page_content for doc in documents]
        batch_size = 2
        batches = [contents[i:i + batch_size] for i in range(0, len(contents), batch_size)]

    elif file_ext == 'txt':
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, 'wb') as f:
            f.write(file_bytes)
        loader = TextLoader(file_path)
        documents = loader.load()
        contents = [doc.page_content for doc in documents]
        batch_size = 2
        batches = [contents[i:i + batch_size] for i in range(0, len(contents), batch_size)]

    elif file_ext == 'csv':
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, 'wb') as f:
            f.write(file_bytes)
        loader = CSVLoader(file_path)
        documents = loader.load()
        contents = [doc.page_content for doc in documents]
        batch_size = 10
        batches = [contents[i:i + batch_size] for i in range(0, len(contents), batch_size)]

    elif file_ext == 'xlsx':
        batch_size = 10
        batches = extract_batches_from_excel(file_bytes, batch_size=batch_size)

    else:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    num_batches = min(len(batches), (story_count + batch_size - 1) // batch_size)
    print(f"Total batches: {num_batches}, Batch size: {batch_size}")

    async def batch_stream():
        yield '{"user_stories": ['

        generated_stories = []
        seen_titles = set()
        first_story = True
        model_name = "gpt-3.5-turbo"  # or "gpt-4"

        batch_index = 0
        retry_count = 0

        while len(generated_stories) < story_count:
            if batch_index >= len(batches):
                batch_index = 0

            current_batch = batches[batch_index]
            remaining = story_count - len(generated_stories)
            current_batch_size = min(batch_size, remaining)

            handler = StreamHandler()
            llm = ChatOpenAI(
                openai_api_key=OPENAI_KEY,
                model=model_name,
                streaming=True,
                callbacks=[handler],
                temperature=0.7,
            )

            prompt = f"""
You are a Business Analyst. From the following requirement, generate {current_batch_size} unique and creative Jira user stories in **STRICTLY** this JSON array format (no extra text):

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
- Do NOT return markdown or explanation.
- DO NOT wrap the array in an object.
- Ensure valid JSON array.
- Make sure stories are diverse and non-repetitive.
- Include any URL found in the requirement inside the **description** field of the user story.

Requirement: "{' '.join(current_batch)}"
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

            if buffer:
                try:
                    parsed_stories = json.loads(f"[{buffer}]")
                    added = 0
                    for story in parsed_stories:
                        title = story.get("title", "").strip().lower()
                        if title and title not in seen_titles and len(generated_stories) < story_count:
                            generated_stories.append(story)
                            seen_titles.add(title)
                            added += 1
                    if added == 0:
                        retry_count += 1
                    else:
                        retry_count = 0
                except json.JSONDecodeError:
                    print("⚠️ Skipping malformed output.")
                    retry_count += 1

            if retry_count > 3:
                break

            batch_index += 1

        for i, story in enumerate(generated_stories):
            if not first_story:
                yield ","
            yield json.dumps(story)
            first_story = False

        yield f'], "story_count": {len(generated_stories)},'
        yield f'"meta": {{"message": "Generated {len(generated_stories)} unique stories"}}'
        yield '}'

    return StreamingResponse(batch_stream(), media_type="application/json")
