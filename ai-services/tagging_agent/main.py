import os
import json
import re
import time
from dotenv import load_dotenv
import boto3
import aiohttp

# Load environment variables
load_dotenv()

import asyncio
import aio_pika
import asyncpg
import ast

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:4000")

async def fetch_tags():
    """Fetch tags from the backend API"""
    async with aiohttp.ClientSession() as session:
        try:
            # You can add search parameter if needed
            async with session.get(f"{BACKEND_URL}/tags") as response:
                if response.status == 200:
                    tags_data = await response.json()
                    # Extract tag names from the response
                    if isinstance(tags_data, list):
                        return [tag.get("name", str(tag)) if isinstance(tag, dict) else str(tag) for tag in tags_data]
                    else:
                        return []
                else:
                    print(f"Failed to fetch tags, status: {response.status}")
                    return []
        except Exception as e:
            print(f"Error fetching tags: {e}")
            # Fallback to hardcoded tags
            return [
                "banking", "loan", "credit_card", "personal_loan", "mortgage",
                "savings_account", "investment", "insurance", "vpbank",
                "customer_service", "application", "financial_product",
                "risk_management", "compliance", "documentation",
                "income_verification", "credit_history", "account_opening",
                "portfolio", "premium", "policy", "consultation"
            ]

async def send_chunk_to_backend(chunk_id: str, tags: list):
    """Send chunk data with tags to the backend /chunks endpoint"""
    async with aiohttp.ClientSession() as session:
        payload = {
            "id": chunk_id,
            "tags": tags
        }
        try:
            async with session.put(f"{BACKEND_URL}/chunks", json=payload) as response:
                if response.status == 200:
                    print(f"Successfully sent chunk {chunk_id} to backend")
                else:
                    print(f"Failed to send chunk {chunk_id}, status: {response.status}")
        except Exception as e:
            print(f"Error sending chunk to backend: {e}")

async def send_chunk_component_to_backend(chunk_id: str, component_index: int, content: str):
    """Send chunk component (proposition) to the backend /chunk-component endpoint"""
    async with aiohttp.ClientSession() as session:
        payload = {
            "chunk_id": chunk_id,
            "component_index": component_index,
            "content": content
        }
        try:
            async with session.post(f"{BACKEND_URL}/chunk-component", json=payload) as response:
                if response.status == 200:
                    print(f"Successfully sent component {component_index} for chunk {chunk_id}")
                    # Get the response to extract the created component ID
                    response_data = await response.json()
                    component_id = response_data.get("id")
                    return component_id
                else:
                    print(f"Failed to send component {component_index} for chunk {chunk_id}, status: {response.status}")
                    return None
        except Exception as e:
            print(f"Error sending chunk component to backend: {e}")
            return None

async def publish_to_embedding_queue(connection, component_id: str, content: str):
    """Publish proposition to embedding queue"""
    try:
        channel = await connection.channel()
        queue = await channel.declare_queue(EMBEDDING_QUEUE, durable=True)
        
        message_payload = {
            "id": component_id,
            "content": content,
            "type": "proposition"  # Specify type for clarity
        }
        
        message = aio_pika.Message(
            json.dumps(message_payload).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        
        await channel.default_exchange.publish(message, routing_key=EMBEDDING_QUEUE)
        print(f"Published proposition {component_id} to embedding queue")
        
    except Exception as e:
        print(f"Error publishing to embedding queue: {e}")

async def create_new_tag(tag_name: str):
    """Create a new tag in the backend"""
    async with aiohttp.ClientSession() as session:
        payload = {
            "name": tag_name
        }
        try:
            async with session.post(f"{BACKEND_URL}/tags", json=payload) as response:
                if response.status == 200:
                    print(f"Successfully created new tag: {tag_name}")
                else:
                    print(f"Failed to create tag {tag_name}, status: {response.status}")
        except Exception as e:
            print(f"Error creating new tag: {e}")

async def process_message(msg: aio_pika.IncomingMessage):
    async with msg.process(ignore_processed=True):
        chunk = json.loads(msg.body.decode())
        chunk_id = chunk.get("chunk_id", "")
        title = chunk.get("title", "")
        content = chunk.get("content", "")
        print(content)
        # Fetch tags and process both tags and propositions concurrently
        tags_task = fetch_tags()
        tags_llm_task = call_tags_llm_async(content, await tags_task)
        propositions_task = call_proposition_llm_async(f"Title: {title} Content: {content}")
        
        # Wait for both operations to complete
        tagged_dict, propositions = await asyncio.gather(tags_llm_task, propositions_task)

        # Ensure tagged_dict is a dict, not a string
        if isinstance(tagged_dict, str):
            try:
                tagged_dict = json.loads(tagged_dict)
            except Exception:
                try:
                    tagged_dict = ast.literal_eval(tagged_dict)
                except Exception:
                    print("Failed to parse tags LLM output as JSON or Python dict. Output was:", tagged_dict)
                    tagged_dict = {"exist_tags": [], "new_tags": []}

        # Parse tags from LLM response and send to backend
        try:
            all_tags = []
            exist_tags = tagged_dict.get("exist_tags", [])
            new_tags = tagged_dict.get("new_tags", [])
            
            # Create new tags first
            for new_tag in new_tags:
                await create_new_tag(new_tag)
            
            # Combine all tags
            all_tags.extend(exist_tags)
            all_tags.extend(new_tags)
            
            # Send to backend
            await send_chunk_to_backend(chunk_id, all_tags)
            
        except Exception as e:
            print(f"Error processing tags: {e}")

        # Parse propositions and send to backend
        try:
            # Try to extract JSON array from propositions
            propositions_list = extract_json(propositions)
            
            # Send each proposition as a chunk component
            for index, proposition in enumerate(propositions_list):
                if isinstance(proposition, dict):
                    prop_content = proposition.get("content", proposition.get("text", str(proposition)))
                else:
                    prop_content = str(proposition)
                
                # Send to backend and get component ID
                component_id = await send_chunk_component_to_backend(chunk_id, index, prop_content)
                
                # If component was created successfully, publish to embedding queue
                if component_id:
                    await publish_to_embedding_queue(msg.channel.connection, component_id, prop_content)
                
        except Exception as e:
            print(f"Error processing propositions: {e}")
            # Fallback: split by lines and send each as component
            prop_lines = [line.strip() for line in propositions.split('\n') if line.strip()]
            for index, line in enumerate(prop_lines):
                component_id = await send_chunk_component_to_backend(chunk_id, index, line)
                
                # If component was created successfully, publish to embedding queue
                if component_id:
                    await publish_to_embedding_queue(msg.channel.connection, component_id, line)

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
EMBEDDING_QUEUE = "embedding-queue"

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
        with open("last_claude_output.txt", "w", encoding="utf-8") as f:
            f.write(output)
        raise ValueError("Claude output does not contain valid JSON array")

    raw_json = match.group(0)

    # 👉 Sửa lỗi escape bằng cách thay \ → \\ trước khi load
    try:
        cleaned_json = re.sub(r'\\(?![nrt"\\/])', r'\\\\', raw_json)
        return json.loads(cleaned_json)
    except Exception as e:
        with open("last_claude_output_raw.txt", "w", encoding="utf-8") as f:
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