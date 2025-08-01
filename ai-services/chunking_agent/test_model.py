import boto3
import json
from botocore.exceptions import ClientError
from concurrent.futures import ThreadPoolExecutor, as_completed

# Cấu hình các model
models = {
    "us.anthropic.claude-3-5-haiku-20241022-v1:0": 20,
    "us.anthropic.claude-3-5-sonnet-20240620-v1:0": 10,
    "us.anthropic.claude-3-7-sonnet-20250219-v1:0": 4,
    "us.anthropic.claude-sonnet-4-20250514-v1:0": 2,
    # "us.anthropic.claude-opus-4-20250514-v1:0": 2,
    "us.anthropic.claude-3-sonnet-20240229-v1:0": 10
}

# Prompt test đơn giản
prompt = "Bạn có thể giới thiệu một vài lợi ích của AI trong ngành tài chính ngân hàng không?"

# Hàm gửi prompt đến từng model
def test_model(model_id):
    bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
    try:
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 200,
            "temperature": 0.0
        }

        response = bedrock.invoke_model(
            body=json.dumps(payload),
            modelId=model_id,
            accept="application/json",
            contentType="application/json"
        )

        output = json.loads(response['body'].read())
        result = f"\n✅ Model: {model_id}\n"
        for message in output.get("content", []):
            result += f"→ {message.get('text')}\n"
        return result

    except ClientError as e:
        return f"\n❌ Model: {model_id}\nLỗi: {e.response['Error']['Message']}"

# Sử dụng ThreadPoolExecutor để chạy song song
with ThreadPoolExecutor(max_workers=6) as executor:
    future_to_model = {executor.submit(test_model, model_id): model_id for model_id in models}
    for future in as_completed(future_to_model):
        print(future.result())
