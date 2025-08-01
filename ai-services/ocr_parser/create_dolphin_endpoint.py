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
    iam = boto3.client('iam')
    role = iam.get_role(RoleName='AmazonSageMaker-ExecutionRole-20250712T042674')['Role']['Arn']

# 🔧 2. Helper to pick CPU/GPU TEI image
def get_image_uri(instance_type):
    key = "huggingface-tei" if instance_type.startswith(("ml.g", "ml.p")) else "huggingface-tei-cpu"
    return get_huggingface_llm_image_uri(key, version="1.2.3")


huggingface_model = HuggingFaceModel(
   model_data="s3://sagemaker-us-east-1-905418115981/custom_inference_6/Dolphin/model.tar.gz",       # path to your model and script
   role=role,                    # iam role with permissions to create an Endpoint
   transformers_version="4.48.0",  # transformers version used
   pytorch_version="2.3.0",        # pytorch version used
   py_version='py311',            # python version used
)


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
endpoint_name = "dolphin-endpoint"
cleanup_existing_endpoint(endpoint_name, sess)

# deploy the endpoint endpoint
predictor = huggingface_model.deploy(
    endpoint_name=endpoint_name,",
    initial_instance_count=1,
    instance_type="ml.g4dn.xlarge"
)
print("✅ Endpoint available at:", predictor.endpoint_name)
