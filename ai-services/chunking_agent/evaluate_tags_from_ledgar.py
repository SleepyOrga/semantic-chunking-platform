import os
import json
import re
import time
from dotenv import load_dotenv
import boto3
from datasets import load_dataset
from nltk.stem import WordNetLemmatizer


# Load .env
load_dotenv()

# Claude API setup
bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name=os.getenv('AWS_REGION'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

def load_prompt_template():
    with open("prompt.txt", "r") as f:
        return f.read()

def call_claude_chunking(text: str):
    prompt_template = load_prompt_template()
    full_prompt = prompt_template.replace("{{text}}", text)

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "temperature": 0.3,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": full_prompt
                    }
                ]
            }
        ]
    }

    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"

    response = bedrock.invoke_model(
        modelId=model_id,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )

    result = json.loads(response['body'].read())
    return result['content'][0]['text']

def extract_json(output: str):
    match = re.search(r"\[\s*{.*}\s*]", output, re.DOTALL)
    if not match:
        raise ValueError("Claude output does not contain valid JSON array")
    json_text = match.group(0)
    return json.loads(json_text)


lemmatizer = WordNetLemmatizer()

def normalize(word: str) -> str:
    return lemmatizer.lemmatize(word.lower())

def smart_match(true_label: str, predicted_tags: list[str]) -> bool:
    norm_true = normalize(true_label)
    norm_tags = [normalize(t) for t in predicted_tags]
    return norm_true in norm_tags


def evaluate():
    dataset = load_dataset("lex_glue", "ledgar", split="train[:50]")

    all_results = []
    label_names = dataset.features["label"].names
    for i, sample in enumerate(dataset):
        text = sample["text"]
        true_label = label_names[sample["label"]].lower()

        print(f"\n🔄 Processing sample {i+1}/{len(dataset)}...")

        try:
            output = call_claude_chunking(text)
            chunks = extract_json(output)

            predicted_tags = []
            for chunk in chunks:
                predicted_tags.extend(chunk.get("tags", []))

            predicted_tags = [t.lower() for t in predicted_tags]
            tag_matched = smart_match(true_label, predicted_tags)


            all_results.append({
                "index": i,
                "true_label": true_label,
                "predicted_tags": predicted_tags,
                "matched": tag_matched,
                "text_excerpt": text[:300],
                "raw_output": output
            })

            time.sleep(1.5)  # tránh rate limit

        except Exception as e:
            all_results.append({
                "index": i,
                "true_label": true_label,
                "predicted_tags": [],
                "matched": False,
                "error": str(e),
                "text_excerpt": text[:300]
            })
            print(f"❌ Error in sample {i+1}: {e}")
            time.sleep(2.5)

    # Evaluate accuracy
    correct = sum(1 for r in all_results if r.get("matched"))
    accuracy = correct / len(all_results)
    print(f"\n✅ Accuracy: {accuracy:.2%} ({correct}/{len(all_results)})")

    with open("chunk_eval_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print("📁 Saved results to chunk_eval_results.json")

if __name__ == "__main__":
    evaluate()
