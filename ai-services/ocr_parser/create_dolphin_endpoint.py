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
    role = iam.get_role(RoleName='sagemaker_execution_role')['Role']['Arn']

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

# deploy the endpoint endpoint
predictor = huggingface_model.deploy(
    endpoint_name="dolphin-endpoint",
    initial_instance_count=1,
    instance_type="ml.g4dn.xlarge"
)
print("✅ Endpoint available at:", predictor.endpoint_name)
