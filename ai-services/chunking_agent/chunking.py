import argparse
import asyncio
import json
import os
import re
import sys
import time
import random
from dotenv import load_dotenv
from langchain.text_splitter import MarkdownHeaderTextSplitter
import boto3
from pydantic import BaseModel, RootModel
from typing import List
from langchain.output_parsers import PydanticOutputParser

# --- Load environment variables ---
load_dotenv()

# --- Define Pydantic models (Pydantic v2 compatible) ---
class Chunk(BaseModel):
    title: str
    content: str
    raw_content: str = ""

class ChunkInList(BaseModel):
    title: str
    content: str


class ChunkList(RootModel[List[ChunkInList]]):
    pass

chunk_parser = PydanticOutputParser(pydantic_object=Chunk)
chunk_list_parser = PydanticOutputParser(pydantic_object=ChunkList)

# --- Lazy JSON Decoder to handle malformed escape sequences ---
class LazyDecoder(json.JSONDecoder):
    def decode(self, s, **kwargs):
        regex_replacements = [
            (re.compile(r'([^\\])\\([^\\])'), r'\\\\\\2'),
            (re.compile(r',\s*]'), r']'),
        ]
        for regex, replacement in regex_replacements:
            s = regex.sub(replacement, s)
        return super().decode(s, **kwargs)

# --- Robust JSON extraction helper ---
def extract_json_robust(text: str, return_type: str) -> dict | list | None:
    try:
        start_index = text.find('[' if return_type == 'list' else '{')
        end_index = text.rfind(']' if return_type == 'list' else '}') + 1
        json_str = text[start_index:end_index]
        data = json.loads(json_str, cls=LazyDecoder, strict=False)
        if return_type == "dict" and isinstance(data, list) and len(data) == 1:
            return data[0]
        return data
    except Exception as e:
        try:
            if return_type == "dict":
                title_pos = text.find('"title":')
                content_pos = text.find('"content":', title_pos)
                title_content = text[text.find('"', title_pos+len('"title:"')): text.find("\",", 0, content_pos)]
                for i in range(1, len(text)):
                    if text.find('}', len(text)-i) != -1:
                        end_index = text.find('}', len(text)-i)
                        break
                content_content = text[content_pos + len('"content":') + 2: end_index]
                return {
                    "title": title_content,
                    "content": content_content
                }
            return None
        except json.JSONDecodeError:
            print(json_str)
            print(f"Error parsing JSON: {e}")
            return None

# --- AWS and model config ---
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
MODEL_RE_CHUNKING_NAME = 'us.anthropic.claude-3-5-sonnet-20241022-v2:0'
MODEL_REWRITE_NAME = 'amazon.nova-lite-v1:0'

client = boto3.client("bedrock-runtime", region_name=AWS_REGION,
                      aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

semaphore = asyncio.Semaphore(15)

async def retry_with_backoff(fn, retries=5):
    for i in range(retries):
        try:
            return await fn()
        except Exception as e:
            if "ThrottlingException" in str(e):
                wait = (2 ** i) + random.uniform(0, 1)
                print(f"⏳ Throttled. Retry {i+1}/{retries} in {wait:.2f}s")
                await asyncio.sleep(wait)
            else:
                raise e
    raise RuntimeError("Max retries exceeded")

class LlmChunker:
    def __init__(self, window_size=8000, overlap=100):
        self.window_size = window_size
        self.overlap = overlap
        self.splitter = MarkdownHeaderTextSplitter(
            [("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3")],
            strip_headers=False
        )

    def _create_prompt(self, task, text):
        if task == 'splitting':
            num_chunks = len(text) // 10000 + 1
            system_prompt = """
            You are a helpful assistant that performs semantic chunking.
            """
            prompt = f"""
            {text}
            Split the section above into semantic chunks.
            Return a list of JSON objects:
            {{"title": str, "content": str}}
            Rules:
            - No extra text.
            - Preserve original content.
            - Escape all JSON properly.
            - Maximum {num_chunks} chunks.

            Example of a valid output structure:
            [
            {{"title": "Title of First Chunk", "content": "Content of the first chunk..."}},
            {{"title": "Title of Second Chunk", "content": "Content of the second chunk..."}}
            ]
            """
            max_token = 8192
        else:
            system_prompt = """
            You are a helpful assistant that rewrite the title, remove unnecessary characters and fix OCR errors. You always return json result only.
            """
            prompt = f"""
            {text}
            Rewrite the title of this section, remove unnecessary tokens and fix OCR errors.
            Return ONLY a JSON object with two fields: "title" (string) and "content" (string). 
            Do NOT return markdown or explanation text.
            - Rules:
            1. Do not remove text, only symbols of markdown.
            2. Change the wrong words that cause by OCR process.
            3. Crucially, you must ensure that all special characters within the JSON string values, especially backslashes (\\) and double quotes (\"), are properly escaped to create a syntactically valid JSON string. For example, any literal backslash \\ in the content must be represented as \\\\ in the final JSON output."
            Return json with 2 key title (str) and content (str).
            Example of a valid output structure:
            {{"title": "New title of the Chunk", "content": "Cleaned content of the chunk..."}}
            """
            max_token = 5120
        return system_prompt, prompt, max_token

    async def call_model(self, model_id, prompt_body):
        async with semaphore:
            return await asyncio.get_event_loop().run_in_executor(
                None, lambda: client.invoke_model(**prompt_body, modelId=model_id)
            )

    async def split_section(self, section):
        system_prompt, prompt, max_token = self._create_prompt("splitting", section["content"])
        body = json.dumps({
            "max_tokens": max_token,
            "system": [{"type": "text", "text": system_prompt}],
            "messages": [{"role": "user", "content": prompt}],
            "anthropic_version": "bedrock-2023-05-31"
        })
        return await retry_with_backoff(lambda: self._parse_split(section, body))

    async def _parse_split(self, section, body):
        response = await self.call_model(MODEL_RE_CHUNKING_NAME, {"body": body})
        response_body = json.loads(response.get("body").read())
        parsed = chunk_list_parser.parse(response_body.get("content")[0].get("text"))
        return parsed.root if parsed else []

    async def rewrite_chunk(self, chunk):
        system_prompt, prompt, max_token = self._create_prompt("rewriting", chunk.get("content", ""))
        body = json.dumps({
            "schemaVersion": "messages-v1",
            "messages": [
                {"role": "user", "content": [{"text": prompt}]}
            ],
            "system": [{"text": system_prompt}],
            "inferenceConfig": {"maxTokens":max_token, "temperature":0.5}
        })
        return await retry_with_backoff(lambda: self._parse_rewrite(chunk, body))

    async def _parse_rewrite(self, chunk, native_request):
        response = await self.call_model(MODEL_REWRITE_NAME, {"body": native_request})
        response_body = json.loads(response.get("body").read())
        raw_text = response_body["output"]["message"]["content"][0]["text"]
        extracted = extract_json_robust(raw_text, return_type="dict")
        if extracted is None:
            print("❌ Failed to extract JSON from model output:")
            print(raw_text)
            return None
        result = Chunk(**extracted)
        result.raw_content = chunk.get("content", "")
        return result

    async def chunk(self, text):
        start_time = time.time()
        if not text.strip():
            return []

        initial_segments = self.splitter.split_text(text)
        if " ".join(initial_segments[0].metadata.values()).strip() == "":
            content = initial_segments.pop(0).page_content
            initial_segments[0].page_content = f"{content}\n{initial_segments[0].page_content}"

        all_sections = [{
            "title": " ".join(seg.metadata.values()),
            "content": seg.page_content
        } for seg in initial_segments]

        split_tasks, rewrite_tasks = [], []
        for section in all_sections:
            if len(section["content"]) < 10000:
                rewrite_tasks.append(asyncio.create_task(self.rewrite_chunk(section)))
            else:
                split_tasks.append(asyncio.create_task(self.split_section(section)))

        split_results = await asyncio.gather(*split_tasks)
        for i, chunks in enumerate(split_results):
            if not isinstance(chunks, list):
                print(f"⚠️ Item at index {i} is not a list of chunks: {chunks}")
                continue
            for chunk in chunks:
                if isinstance(chunk, ChunkInList):
                    chunk = {"title": chunk.title, "content": chunk.content}
                    rewrite_tasks.append(asyncio.create_task(self.rewrite_chunk(chunk)))
                elif isinstance(chunk, Chunk) or isinstance(chunk, dict):
                    rewrite_tasks.append(asyncio.create_task(self.rewrite_chunk(chunk)))
                else:
                    print(f"❌ Unexpected chunk: {chunk}")


        final_chunks = await asyncio.gather(*rewrite_tasks)
        end_time = time.time()
        print(f"\n⏱️ Total processing time: {end_time - start_time:.2f} seconds")
        return [chunk for chunk in final_chunks if chunk]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("-o", "--output", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    with open(args.input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    chunker = LlmChunker()
    final_chunks = asyncio.run(chunker.chunk(content))

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            if args.json:
                json.dump([chunk.model_dump() for chunk in final_chunks], f, indent=2)
            else:
                for chunk in final_chunks:
                    f.write(f"--- Title: {chunk.title} ---\n{chunk.content}\n\n")
        print(f"Saved {len(final_chunks)} chunks to {args.output}")

if __name__ == "__main__":
    main()
