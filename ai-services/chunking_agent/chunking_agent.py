import os
import json
import re
import time
from dotenv import load_dotenv
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.session import get_session
from datasets import load_dataset
from nltk.stem import WordNetLemmatizer

# Load environment variables
load_dotenv()

# Claude Sonnet 4 APAC settings
REGION = os.getenv("AWS_REGION", "ap-southeast-2")
MODEL_ID = "apac.anthropic.claude-sonnet-4-20250514-v1:0"
BEDROCK_URL = f"https://bedrock-runtime.{REGION}.amazonaws.com/model/{MODEL_ID}/invoke"

# Load prompt
def load_prompt_template():
    with open("prompt.txt", "r") as f:
        return f.read()

# Claude chunking call using SigV4 + HTTPS
def call_claude_chunking(text: str):
    prompt_template = load_prompt_template()
    full_prompt = prompt_template.replace("{{text}}", text)

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "temperature": 0.3,
        "messages": [{
            "role": "user",
            "content": [{"type": "text", "text": full_prompt}]
        }]
    }

    session = get_session()
    credentials = session.get_credentials()
    aws_request = AWSRequest(
        method="POST",
        url=BEDROCK_URL,
        data=json.dumps(body),
        headers={"Content-Type": "application/json"}
    )
    SigV4Auth(credentials, "bedrock", REGION).add_auth(aws_request)

    response = requests.post(BEDROCK_URL, data=json.dumps(body), headers=dict(aws_request.headers))
    response.raise_for_status()
    result = response.json()

    return result['content'][0]['text']

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
      
lemmatizer = WordNetLemmatizer()

def normalize(word: str) -> str:
    return lemmatizer.lemmatize(word.lower())

def contains_answer(chunk_text: str, answer_text: str) -> bool:
    return normalize(answer_text) in normalize(chunk_text)

# 🔹 Chunk splitter with overlap
def split_with_overlap(text: str, chunk_size=1000, overlap=200):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i + chunk_size]
        chunks.append(" ".join(chunk))
        i += chunk_size - overlap
    return chunks

def evaluate():
    dataset = load_dataset("alex-apostolo/filtered-cuad", split="train[:1]")

    os.makedirs("split_chunks", exist_ok=True)
    all_results = []

    for i, sample in enumerate(dataset):
        text = sample["context"]
        answer_text = sample["answers"]["text"][0]
        question = sample["question"]

        print(f"\n🔄 Processing sample {i+1}/{len(dataset)} - {sample['id']}")

        try:
            # Step 1: Split with overlap
            raw_chunks = split_with_overlap(text, chunk_size=1000, overlap=200)

            # Save raw chunks to file
            with open(f"split_chunks/sample_{i}.txt", "w") as f:
                for j, c in enumerate(raw_chunks):
                    f.write(f"\n--- Chunk {j+1} ---\n{c}\n")
            
            # break

            os.makedirs("claude_raw_outputs", exist_ok=True)  # tạo folder nếu chưa có

            # Step 2: Send each chunk to Claude and collect semantic chunks
            semantic_chunks = []
            for j, chunk in enumerate(raw_chunks):
                output = call_claude_chunking(chunk)

                print(f"📦 Claude response (shortened): {output[:100]}...")

                # 🔽 Ghi toàn bộ Claude output vào file
                with open(f"claude_raw_outputs/sample_{i}_chunk_{j}.txt", "w", encoding="utf-8") as f_out:
                    f_out.write(output)

                # Trích xuất semantic chunks từ Claude
                semantic_chunks += extract_json(output)
                time.sleep(1.5)

            # # Step 3: Check if any chunk covers the answer
            # matched = any(contains_answer(chunk.get("content", ""), answer_text) for chunk in chunks)

            # # Debug: print matching chunks
            # matching_chunks = [
            #     chunk for chunk in chunks if answer_text in chunk.get("content", "")
            # ]
            # if not matching_chunks:
            #     print(f"⚠️ '{answer_text}' NOT FOUND in any chunk.")
            # else:
            #     print(f"✅ '{answer_text}' FOUND in chunks:")
            #     for match in matching_chunks:
            #         print(f"➡️  Section: {match['section_title']}")


            # all_results.append({
            #     "index": i,
            #     "question": question,
            #     "answer_text": answer_text,
            #     "matched": matched,
            #     "text_excerpt": text[:300],
            #     "semantic_chunks": semantic_chunks
            # })

        except Exception as e:
            all_results.append({
                "index": i,
                "question": question,
                "answer_text": answer_text,
                "matched": False,
                "error": str(e),
                "text_excerpt": text[:300]
            })
            # print(f"❌ Error in sample {i+1}: {e}")
            time.sleep(2.5)

    # # Evaluate accuracy
    # correct = sum(1 for r in all_results if r.get("matched"))
    # accuracy = correct / len(all_results)
    # print(f"\n✅ Accuracy: {accuracy:.2%} ({correct}/{len(all_results)})")

    # with open("cuad_chunk_eval_results.json", "w") as f:
    #     json.dump(all_results, f, indent=2)
    # print("📁 Saved results to cuad_chunk_eval_results.json")

if __name__ == "__main__":
    evaluate()
