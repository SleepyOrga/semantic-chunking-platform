


import boto3
import os
from sagemaker.huggingface import HuggingFaceModel, get_huggingface_llm_image_uri
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

region_name = os.getenv("AWS_REGION", "us-east-1")
os.environ["AWS_DEFAULT_REGION"] = region_name

# 🧩 1. Setup session and role
boto_sess = boto3.session.Session(region_name="us-east-1")
import sagemaker

sess = sagemaker.Session(boto_session=boto_sess)
try:
    role = sagemaker.get_execution_role()
except ValueError:
    role = boto3.client("iam").get_role(RoleName="AmazonSageMaker-ExecutionRole-20250712T042674")["Role"]["Arn"]

# 🔧 2. Helper to pick CPU/GPU TEI image
def get_image_uri(instance_type):
    key = "huggingface-tei" if instance_type.startswith(("ml.g", "ml.p")) else "huggingface-tei-cpu"
    return get_huggingface_llm_image_uri(key, version="1.2.3")

# 🧠 3. Configure model
instance_type = "ml.c5.2xlarge"  # swap to "ml.g5.xlarge" for GPU
image_uri = get_image_uri(instance_type)
model_id = "BAAI/bge-reranker-large"  # or sentence-transformers/paraphrase‑xlm‑r‑multilingual‑v1

env = {"HF_MODEL_ID": model_id, "HF_API_TOKEN": os.environ["HUGGINGFACE_TOKEN"], "HUGGINGFACE_TOKEN": os.environ["HUGGINGFACE_TOKEN"], "POOLING": "mean" }

hf_model = HuggingFaceModel(
    role=role,
    image_uri=image_uri,
    env=env,
)

# 🚀 4. Deploy Endpoint
predictor = hf_model.deploy(
    endpoint_name="reranker-endpoint",
    initial_instance_count=1,
    instance_type=instance_type
)
print("✅ Endpoint available at:", predictor.endpoint_name)
