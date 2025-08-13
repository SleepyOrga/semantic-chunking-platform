import boto3
import os
import time
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

# 🗑️ Helper to clean up existing endpoint resources
def cleanup_existing_endpoint(endpoint_name, sess):
    """Clean up existing endpoint, endpoint config, and model if they exist"""
    sagemaker_client = sess.sagemaker_client
    
    # Check if endpoint exists and delete it
    try:
        endpoint_desc = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
        print(f"🗑️ Deleting existing endpoint: {endpoint_name}")
        sagemaker_client.delete_endpoint(EndpointName=endpoint_name)
        
        # Wait for endpoint deletion
        print("⏳ Waiting for endpoint deletion...")
        waiter = sagemaker_client.get_waiter('endpoint_deleted')
        waiter.wait(EndpointName=endpoint_name)
        print("✅ Endpoint deleted successfully")
    except sagemaker_client.exceptions.ClientError as e:
        if "ValidationException" in str(e) and "does not exist" in str(e):
            print(f"ℹ️ Endpoint {endpoint_name} does not exist, skipping deletion")
        else:
            print(f"⚠️ Error deleting endpoint: {str(e)}")
    except Exception as e:
        print(f"⚠️ Unexpected error deleting endpoint: {str(e)}")
    
    # Check if endpoint config exists and delete it (independent of endpoint existence)
    try:
        endpoint_config_name = endpoint_name  # Usually same name
        sagemaker_client.describe_endpoint_config(EndpointConfigName=endpoint_config_name)
        print(f"🗑️ Deleting existing endpoint config: {endpoint_config_name}")
        sagemaker_client.delete_endpoint_config(EndpointConfigName=endpoint_config_name)
        print("✅ Endpoint config deleted successfully")
    except sagemaker_client.exceptions.ClientError as e:
        if "ValidationException" in str(e) and "does not exist" in str(e):
            print(f"ℹ️ Endpoint config {endpoint_config_name} does not exist, skipping deletion")
        else:
            print(f"⚠️ Error deleting endpoint config: {str(e)}")
    except Exception as e:
        print(f"⚠️ Unexpected error deleting endpoint config: {str(e)}")
    
    print("🔄 Cleanup completed, proceeding with deployment...")

# 🧠 3. Configure model
instance_type = "ml.c5.2xlarge"  # swap to "ml.g5.xlarge" for GPU
image_uri = get_image_uri(instance_type)
# Changed to a model that produces 1536 dimensions to match database schema
model_id = "sentence-transformers/all-mpnet-base-v2"  # This produces 768 dimensions - need different model
# Let's use a model that produces 1536 dimensions
model_id = "intfloat/multilingual-e5-large-instruct"  # This produces 1024 dimensions
# We need to find a model that produces 1536 dimensions or change the database

print(f"🤖 Using model: {model_id}")
print("⚠️  WARNING: Current model produces 1024 dimensions, but database expects 1536!")
print("   You need to either:")
print("   1. Change the database schema to expect 1024 dimensions")
print("   2. Use a different model that produces 1536 dimensions")

env = {"HF_MODEL_ID": model_id, "HF_API_TOKEN": os.environ["HUGGINGFACE_TOKEN"], "HUGGINGFACE_TOKEN": os.environ["HUGGINGFACE_TOKEN"], "POOLING": "mean" }

hf_model = HuggingFaceModel(
    role=role,
    image_uri=image_uri,
    env=env,
)

# 🚀 4. Deploy Endpoint
# Configuration: Set to True to reuse existing endpoint name (will delete existing), 
# False to create a new unique endpoint name
REUSE_ENDPOINT_NAME = True

if REUSE_ENDPOINT_NAME:
    endpoint_name = "embedding-endpoint"
    print(f"🚀 Creating endpoint with reused name: {endpoint_name}")
    # Clean up existing resources first
    cleanup_existing_endpoint(endpoint_name, sess)
else:
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    endpoint_name = f"embedding-endpoint-{timestamp}"
    print(f"🚀 Creating endpoint with unique name: {endpoint_name}")

predictor = hf_model.deploy(
    endpoint_name=endpoint_name,
    initial_instance_count=1,
    instance_type=instance_type
)
print("✅ Endpoint available at:", predictor.endpoint_name)
