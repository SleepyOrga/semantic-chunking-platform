#!/usr/bin/env python3
"""
SageMaker Endpoint Management Script
Provides easy commands to manage embedding endpoints
"""

import boto3
import os
import sys
import argparse
from dotenv import load_dotenv

load_dotenv()

region_name = os.getenv("AWS_REGION", "us-east-1")
sagemaker_client = boto3.client('sagemaker', region_name=region_name)

def list_endpoints():
    """List all SageMaker endpoints with details"""
    try:
        response = sagemaker_client.list_endpoints()
        endpoints = response['Endpoints']
        
        if not endpoints:
            print("📝 No SageMaker endpoints found")
            return
        
        print(f"📊 SageMaker Endpoints ({len(endpoints)} total)")
        print("=" * 80)
        
        for endpoint in endpoints:
            name = endpoint['EndpointName']
            status = endpoint['EndpointStatus']
            created = endpoint['CreationTime'].strftime('%Y-%m-%d %H:%M:%S')
            
            # Get additional details
            try:
                details = sagemaker_client.describe_endpoint(EndpointName=name)
                instance_type = details['ProductionVariants'][0]['InstanceType']
                instance_count = details['ProductionVariants'][0]['CurrentInstanceCount']
                
                print(f"🚀 {name}")
                print(f"   Status: {status}")
                print(f"   Created: {created}")
                print(f"   Instance: {instance_type} (x{instance_count})")
                print()
            except Exception as e:
                print(f"🚀 {name} - {status} - {created} [Details unavailable]")
                
    except Exception as e:
        print(f"❌ Error listing endpoints: {e}")

def get_endpoint_status(endpoint_name):
    """Get status of a specific endpoint"""
    try:
        response = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
        
        print(f"📍 Endpoint: {endpoint_name}")
        print(f"   Status: {response['EndpointStatus']}")
        print(f"   Created: {response['CreationTime'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Updated: {response['LastModifiedTime'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        for variant in response['ProductionVariants']:
            print(f"   Variant: {variant['VariantName']}")
            print(f"     Instance Type: {variant['InstanceType']}")
            print(f"     Instance Count: {variant['CurrentInstanceCount']}")
            print(f"     Weight: {variant['CurrentWeight']}")
        
        return True
        
    except sagemaker_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ValidationException':
            print(f"❌ Endpoint '{endpoint_name}' does not exist")
        else:
            print(f"❌ Error describing endpoint: {e}")
        return False

def estimate_cost(endpoint_name):
    """Estimate hourly cost of running endpoint"""
    try:
        response = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
        
        # Rough cost estimates per hour (USD) - these are approximate
        cost_per_hour = {
            'ml.t2.medium': 0.047,
            'ml.t2.large': 0.094,
            'ml.t2.xlarge': 0.188,
            'ml.m5.large': 0.115,
            'ml.m5.xlarge': 0.230,
            'ml.m5.2xlarge': 0.461,
            'ml.m5.4xlarge': 0.922,
            'ml.c5.large': 0.102,
            'ml.c5.xlarge': 0.204,
            'ml.c5.2xlarge': 0.408,
            'ml.c5.4xlarge': 0.816,
            'ml.g4dn.xlarge': 0.736,
            'ml.g4dn.2xlarge': 1.180,
            'ml.g5.xlarge': 1.408,
            'ml.g5.2xlarge': 2.270,
        }
        
        total_cost = 0
        print(f"💰 Cost Estimate for {endpoint_name}:")
        
        for variant in response['ProductionVariants']:
            instance_type = variant['InstanceType']
            instance_count = variant['CurrentInstanceCount']
            
            hourly_cost = cost_per_hour.get(instance_type, 0.5)  # Default estimate
            variant_cost = hourly_cost * instance_count
            total_cost += variant_cost
            
            print(f"   {instance_type} x{instance_count}: ${variant_cost:.3f}/hour")
        
        print(f"   Total: ${total_cost:.3f}/hour (${total_cost * 24:.2f}/day)")
        print("   ⚠️ These are approximate costs, check AWS pricing for exact rates")
        
    except Exception as e:
        print(f"❌ Error estimating cost: {e}")

def main():
    parser = argparse.ArgumentParser(description='SageMaker Endpoint Management')
    parser.add_argument('command', choices=['list', 'status', 'cost', 'create', 'delete'], 
                       help='Command to execute')
    parser.add_argument('--endpoint', '-e', help='Endpoint name (required for status, cost, delete)')
    parser.add_argument('--force', '-f', action='store_true', help='Force deletion without confirmation')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        list_endpoints()
    
    elif args.command == 'status':
        if not args.endpoint:
            print("❌ --endpoint required for status command")
            sys.exit(1)
        get_endpoint_status(args.endpoint)
    
    elif args.command == 'cost':
        if not args.endpoint:
            print("❌ --endpoint required for cost command")
            sys.exit(1)
        estimate_cost(args.endpoint)
    
    elif args.command == 'create':
        print("🚀 To create an endpoint, run:")
        print("   python create_endpoints.py")
    
    elif args.command == 'delete':
        if not args.endpoint:
            print("❌ --endpoint required for delete command")
            sys.exit(1)
        
        if not args.force:
            confirm = input(f"⚠️ Delete endpoint '{args.endpoint}'? (yes/no): ")
            if confirm.lower() not in ['yes', 'y']:
                print("❌ Deletion cancelled")
                sys.exit(0)
        
        print(f"🗑️ Deleting endpoint: {args.endpoint}")
        os.system(f"python delete_endpoints.py {args.endpoint}")

if __name__ == "__main__":
    main()
