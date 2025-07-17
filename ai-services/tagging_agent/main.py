import os
import json
import re
import time
from dotenv import load_dotenv
import boto3

# Load environment variables
load_dotenv()

import asyncio
import aio_pika
import asyncpg

async def fetch_tags():
    return [
            "banking", "loan", "credit_card", "personal_loan", "mortgage",
            "savings_account", "investment", "insurance", "vpbank",
            "customer_service", "application", "financial_product",
            "risk_management", "compliance", "documentation",
            "income_verification", "credit_history", "account_opening",
            "portfolio", "premium", "policy", "consultation"
        ]
    conn = await asyncpg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', 5432),
        database=os.getenv('DB_NAME', 'app_db'),
        user=os.getenv('DB_USER', 'app_user'),
        password=os.getenv('DB_PASSWORD', 'secret123')
    )
    try:
        rows = await conn.fetch("SELECT tag_name FROM tags;")
        return [row[0] for row in rows]
    finally:
        await conn.close()

async def process_message(msg: aio_pika.IncomingMessage):
    async with msg.process(ignore_processed=True):
        chunk = json.loads(msg.body.decode())
        title = chunk.get("title", "")
        content = chunk.get("content", "")
        print(content)
        # Fetch tags and process both tags and propositions concurrently
        tags_task = fetch_tags()
        tags_llm_task = call_tags_llm_async(content, await tags_task)
        propositions_task = call_proposition_llm_async(f"Title: {title} Content: {content}")
        
        # Wait for both operations to complete
        tagged_text, propositions = await asyncio.gather(tags_llm_task, propositions_task)

        print("Tagged:", tagged_text)
        print("Propositions:", propositions)
        # TODO: store or forward results

# Claude Sonnet 4 APAC settings
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
MODEL_NAME = 'amazon.nova-lite-v1:0'

# RabbitMQ config
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "52.65.216.159")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "admin")

AMQP_URL = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"


TAGGING_INPUT_QUEUE = "tagging-input-queue"
TAGGING_OUTPUT_QUEUE = "tagging-output-queue"

client = boto3.client("bedrock-runtime", region_name=AWS_REGION,
                      aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

# Load prompt
def load_prompt_template(type_prompt: str) -> str:
    with open(f"{type_prompt}.txt", "r") as f:
        return f.read()

async def call_tags_llm_async(text: str, tags: list):
    system_prompt = "You are a tagging agent that assigns relevant tags to text chunks."
    prompt = load_prompt_template("tags")
    prompt = prompt.replace("{{text}}", text).replace("{{tag_list}}", ", ".join(tags))
    body = json.dumps({
        "schemaVersion": "messages-v1",
        "messages": [
            {"role": "user", "content": [{"text": prompt}]}
        ],
        "system": [{"text": system_prompt}],
        "inferenceConfig": {"maxTokens": 1000, "temperature":0.5}
    })
    
    loop = asyncio.get_event_loop()
    response = response = await loop.run_in_executor(
        None,
        lambda: client.invoke_model(
            modelId=MODEL_NAME,
            body=body,
            contentType="application/json",
            accept="application/json"
        )
    )

    response_body = json.loads(response.get("body").read())
    tags = response_body["output"]["message"]["content"][0].get("text")
    return tags

async def call_proposition_llm_async(text: str):
    prompt = load_prompt_template("propositions")
    prompt = prompt.replace("{{text}}", text)
    system_prompt = "You are a proposition agent that generates propositions based on text chunks."
    body = json.dumps({
        "schemaVersion": "messages-v1",
        "messages": [
            {"role": "user", "content": [{"text": prompt}]}
        ],
        "system": [{"text": system_prompt}],
        "inferenceConfig": {"maxTokens": 5000, "temperature":0.0}
    })
    
    loop = asyncio.get_event_loop()
    response = response = await loop.run_in_executor(
        None,
        lambda: client.invoke_model(
            modelId=MODEL_NAME,
            body=body,
            contentType="application/json",
            accept="application/json"
        )
    )

    response_body = json.loads(response.get("body").read())
    propositions = response_body["output"]["message"]["content"][0].get("text")
    return propositions

# Extract JSON array from Claude output
def extract_json(output: str):
    match = re.search(r"\[\s*{.*?}\s*]", output, re.DOTALL)
    if not match:
        with open("last_claude_output.txt", "w") as f:
            f.write(output)
        raise ValueError("Claude output does not contain valid JSON array")

    raw_json = match.group(0)

    # 👉 Sửa lỗi escape bằng cách thay \ → \\ trước khi load
    try:
        cleaned_json = re.sub(r'\\(?![nrt"\\/])', r'\\\\', raw_json)
        return json.loads(cleaned_json)
    except Exception as e:
        with open("last_claude_output_raw.txt", "w") as f:
            f.write(raw_json)
        raise ValueError(f"❌ Failed to parse cleaned JSON: {e}")
    
async def main():
    print(AMQP_URL)
    conn = await aio_pika.connect_robust(AMQP_URL)
    ch = await conn.channel()
    q = await ch.declare_queue(TAGGING_INPUT_QUEUE, durable=True)
    await q.consume(process_message)
    print("Agent listening…")
    
    try:
        await asyncio.Future()  # Run forever
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())