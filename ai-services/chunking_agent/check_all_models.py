import boto3

client = boto3.client("bedrock")
models = client.list_foundation_models()
for model in models["modelSummaries"]:
    if model["providerName"] == "Anthropic":
        print(model["modelId"])
