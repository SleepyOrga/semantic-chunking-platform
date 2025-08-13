import os
import pytest
import json
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from aio_pika import IncomingMessage
import asyncpg
import aio_pika
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MockInputData:
    """Mock input data for tagging agent tests"""
    
    @staticmethod
    def get_rabbitmq_message(title="", content="", chunk_id=None):
        """Create mock RabbitMQ message"""
        message_data = {
            "title": title,
            "content": content,
            "chunk_id": chunk_id or "chunk_001",
            "timestamp": "2024-01-15T10:30:00Z",
            "source": "document_processor"
        }
        
        mock_message = Mock(spec=IncomingMessage)
        mock_message.body = json.dumps(message_data).encode()
        mock_message.process = AsyncMock()
        mock_message.process.return_value.__aenter__ = AsyncMock()
        mock_message.process.return_value.__aexit__ = AsyncMock()
        
        return mock_message, message_data
    
    @staticmethod
    def get_sample_chunks():
        """Sample text chunks for testing"""
        return [
            {
                "title": "VPBank Loan Application",
                "content": "Customer John Doe has applied for a personal loan of 500 million VND with VPBank. The loan application includes income verification and credit history check.",
                "chunk_id": "chunk_001"
            },
            {
                "title": "Credit Card Application",
                "content": "New credit card application submitted for VPBank Platinum Card. Customer has monthly income of 20 million VND and existing banking relationship.",
                "chunk_id": "chunk_002"
            },
            {
                "title": "Account Opening",
                "content": "VPBank savings account opening for new customer. Required documents include ID card, proof of address, and income certificate.",
                "chunk_id": "chunk_003"
            },
            {
                "title": "Investment Advisory",
                "content": "Investment consultation session for VPBank private banking client. Discussion on portfolio diversification and risk management strategies.",
                "chunk_id": "chunk_004"
            },
            {
                "title": "Insurance Policy",
                "content": "VPBank life insurance policy application. Coverage amount 1 billion VND with 20-year term and premium payment schedule.",
                "chunk_id": "chunk_005"
            }
        ]
    
    @staticmethod
    def get_mock_tags():
        """Mock tags from database"""
        return [
            "banking", "loan", "credit_card", "personal_loan", "mortgage",
            "savings_account", "investment", "insurance", "vpbank",
            "customer_service", "application", "financial_product",
            "risk_management", "compliance", "documentation",
            "income_verification", "credit_history", "account_opening",
            "portfolio", "premium", "policy", "consultation"
        ]
    
    @staticmethod
    def get_mock_bedrock_responses():
        """Mock AWS Bedrock responses"""
        return {
            "tags_response": {
                "body": json.dumps({
                    "content": [{
                        "text": "banking, loan, vpbank, personal_loan, income_verification"
                    }]
                }).encode()
            },
            "propositions_response": {
                "body": json.dumps({
                    "content": [{
                        "text": """[
                            {
                                "proposition": "John Doe applied for a personal loan",
                                "confidence": 0.95,
                                "entities": ["John Doe", "personal loan"]
                            },
                            {
                                "proposition": "Loan amount is 500 million VND",
                                "confidence": 0.98,
                                "entities": ["500 million VND"]
                            },
                            {
                                "proposition": "VPBank processes loan applications",
                                "confidence": 0.92,
                                "entities": ["VPBank", "loan applications"]
                            }
                        ]"""
                    }]
                }).encode()
            }
        }
    
    @staticmethod
    def get_empty_chunk():
        """Empty chunk for edge case testing"""
        return {
            "title": "",
            "content": "",
            "chunk_id": "empty_chunk"
        }
    
    @staticmethod
    def get_large_chunk():
        """Large chunk for performance testing"""
        large_content = "VPBank financial services " * 1000
        return {
            "title": "Large Document Analysis",
            "content": large_content,
            "chunk_id": "large_chunk"
        }
    
    @staticmethod
    def get_special_characters_chunk():
        """Chunk with special characters for encoding testing"""
        return {
            "title": "Tài liệu tiếng Việt - VPBank",
            "content": "Khách hàng Nguyễn Văn A đã nộp đơn xin vay 500 triệu VNĐ tại VPBank. Tài liệu bao gồm: chứng minh thư, sổ hộ khẩu, và giấy chứng nhận thu nhập.",
            "chunk_id": "vietnamese_chunk"
        }
    
    @staticmethod
    def get_json_malformed_chunk():
        """Chunk that might cause JSON parsing issues"""
        return {
            "title": "Document with \"quotes\" and \\ backslashes",
            "content": "Content with special chars: {\"json\": \"value\"} and \\escaped\\path",
            "chunk_id": "malformed_chunk"
        }

class TestTaggingAgentMocks:
    """Test class with various mock scenarios"""
    
    @pytest.fixture
    def mock_db_connection(self):
        """Mock database connection"""
        conn = AsyncMock(spec=asyncpg.Connection)
        conn.fetch = AsyncMock(return_value=[(tag,) for tag in MockInputData.get_mock_tags()])
        conn.close = AsyncMock()
        return conn
    
    @pytest.fixture
    def mock_bedrock_client(self):
        """Mock AWS Bedrock client"""
        client = Mock()
        responses = MockInputData.get_mock_bedrock_responses()
        client.invoke_model = Mock(return_value=responses["tags_response"])
        return client
    
    @pytest.fixture
    def sample_chunks(self):
        """Fixture providing sample chunks"""
        return MockInputData.get_sample_chunks()
    
    @pytest.fixture
    def mock_rabbitmq_messages(self):
        """Create mock RabbitMQ messages for testing"""
        messages = []
        for chunk in MockInputData.get_sample_chunks():
            mock_msg, data = MockInputData.get_rabbitmq_message(
                chunk["title"], 
                chunk["content"], 
                chunk["chunk_id"]
            )
            messages.append((mock_msg, data))
        return messages
    
    @pytest.fixture
    def mock_prompt_templates(self):
        """Mock prompt templates"""
        return {
            "tag": "Please tag the following text: {{text}}\nAvailable tags: {{tag_list}}",
            "propositions": "Extract propositions from: {{text}}"
        }
    
    def test_mock_data_structure(self, sample_chunks):
        """Test that mock data has correct structure"""
        assert len(sample_chunks) == 5
        for chunk in sample_chunks:
            assert "title" in chunk
            assert "content" in chunk
            assert "chunk_id" in chunk
            assert isinstance(chunk["title"], str)
            assert isinstance(chunk["content"], str)
    
    def test_mock_rabbitmq_message(self):
        """Test mock RabbitMQ message creation"""
        mock_msg, data = MockInputData.get_rabbitmq_message(
            "Test Title", 
            "Test Content",
            "test_chunk"
        )
        
        decoded_data = json.loads(mock_msg.body.decode())
        assert decoded_data["title"] == "Test Title"
        assert decoded_data["content"] == "Test Content"
        assert decoded_data["chunk_id"] == "test_chunk"
    
    def test_mock_bedrock_response(self):
        """Test mock Bedrock response structure"""
        responses = MockInputData.get_mock_bedrock_responses()
        
        # Test tags response
        tags_body = json.loads(responses["tags_response"]["body"].decode())
        assert "content" in tags_body
        assert len(tags_body["content"]) > 0
        
        # Test propositions response
        props_body = json.loads(responses["propositions_response"]["body"].decode())
        assert "content" in props_body
        propositions_text = props_body["content"][0]["text"]
        assert "[" in propositions_text  # Should contain JSON array
    
    def test_edge_cases(self):
        """Test edge case mock data"""
        # Empty chunk
        empty = MockInputData.get_empty_chunk()
        assert empty["title"] == ""
        assert empty["content"] == ""
        
        # Large chunk
        large = MockInputData.get_large_chunk()
        assert len(large["content"]) > 10000
        
        # Special characters
        special = MockInputData.get_special_characters_chunk()
        assert "Việt" in special["title"]
        assert "Nguyễn" in special["content"]
        
        # JSON problematic content
        json_chunk = MockInputData.get_json_malformed_chunk()
        assert "\"" in json_chunk["title"]
        assert "\\" in json_chunk["content"]
    
    @pytest.mark.asyncio
    async def test_async_mock_behavior(self, mock_db_connection):
        """Test async mock behavior"""
        # Test database fetch
        rows = await mock_db_connection.fetch("SELECT tag_name FROM tags;")
        assert len(rows) > 0
        
        # Test connection close
        await mock_db_connection.close()
        mock_db_connection.close.assert_called_once()

# Additional mock data for specific test scenarios
MOCK_ENVIRONMENT_VARS = {
    "DB_HOST": os.getenv('DB_HOST', 'localhost'),
    "DB_PORT": os.getenv('DB_PORT', '5432'),
    "DB_NAME": os.getenv('DB_NAME', 'test_db'),
    "DB_USER": os.getenv('DB_USER', 'test_user'),
    "DB_PASSWORD": os.getenv('DB_PASSWORD', 'test_password'),
    "AWS_ACCESS_KEY_ID": os.getenv('AWS_ACCESS_KEY_ID', 'test_access'),
    "AWS_SECRET_ACCESS_KEY": os.getenv('AWS_SECRET_ACCESS_KEY', 'test_secret'),
    "AWS_REGION": os.getenv('AWS_REGION', 'us-east-1'),
    "RABBITMQ_HOST": os.getenv('RABBITMQ_HOST', 'localhost'),
    "RABBITMQ_PORT": os.getenv('RABBITMQ_PORT', '5672'),
    "RABBITMQ_USER": os.getenv('RABBITMQ_USER', 'test_user'),
    "RABBITMQ_PASS": os.getenv('RABBITMQ_PASS', 'test_pass')
}

class MockDataProducer:
    """Producer class to send mock data to RabbitMQ"""
    
    def __init__(self):
        self.rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
        self.rabbitmq_port = int(os.getenv("RABBITMQ_PORT", 5672))
        self.rabbitmq_user = os.getenv("RABBITMQ_USER", "admin")
        self.rabbitmq_pass = os.getenv("RABBITMQ_PASS", "admin")
        self.amqp_url = f"amqp://{self.rabbitmq_user}:{self.rabbitmq_pass}@{self.rabbitmq_host}:{self.rabbitmq_port}/"
        self.input_queue = "tagging-input-queue"
    
    async def send_message(self, message_data):
        """Send a single message to RabbitMQ"""
        try:
            connection = await aio_pika.connect_robust(self.amqp_url)
            channel = await connection.channel()
            
            # Declare queue to ensure it exists
            queue = await channel.declare_queue(self.input_queue, durable=True)
            
            # Create message
            message = aio_pika.Message(
                json.dumps(message_data).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            
            # Send message
            await channel.default_exchange.publish(
                message,
                routing_key=self.input_queue
            )
            
            print(f"✅ Sent message: {message_data.get('chunk_id', 'unknown')}")
            
            await connection.close()
            
        except Exception as e:
            print(f"❌ Error sending message: {e}")
    
    async def send_batch_messages(self, messages):
        """Send multiple messages in batch"""
        try:
            connection = await aio_pika.connect_robust(self.amqp_url)
            channel = await connection.channel()
            
            # Declare queue to ensure it exists
            queue = await channel.declare_queue(self.input_queue, durable=True)
            
            for message_data in messages:
                message = aio_pika.Message(
                    json.dumps(message_data).encode(),
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                )
                
                await channel.default_exchange.publish(
                    message,
                    routing_key=self.input_queue
                )
                
                print(f"✅ Sent batch message: {message_data.get('chunk_id', 'unknown')}")
                
                # Small delay to avoid overwhelming the system
                await asyncio.sleep(0.1)
            
            await connection.close()
            print(f"✅ Sent {len(messages)} messages successfully")
            
        except Exception as e:
            print(f"❌ Error sending batch messages: {e}")
    
    async def send_sample_chunks(self):
        """Send all sample chunks"""
        chunks = MockInputData.get_sample_chunks()
        await self.send_batch_messages(chunks)
    
    async def send_edge_cases(self):
        """Send edge case test data"""
        edge_cases = [
            MockInputData.get_empty_chunk(),
            MockInputData.get_large_chunk(),
            MockInputData.get_special_characters_chunk(),
            MockInputData.get_json_malformed_chunk()
        ]
        await self.send_batch_messages(edge_cases)
    
    async def send_stress_test_data(self, count=100):
        """Send multiple copies of sample data for stress testing"""
        base_chunks = MockInputData.get_sample_chunks()
        stress_messages = []
        
        for i in range(count):
            for chunk in base_chunks:
                stress_chunk = chunk.copy()
                stress_chunk["chunk_id"] = f"{chunk['chunk_id']}_stress_{i}"
                stress_chunk["timestamp"] = f"2024-01-15T{10 + (i % 12):02d}:30:00Z"
                stress_messages.append(stress_chunk)
        
        print(f"🔄 Sending {len(stress_messages)} stress test messages...")
        await self.send_batch_messages(stress_messages)

async def send_mock_data_to_queue():
    """Main function to send mock data to tagging agent input queue"""
    producer = MockDataProducer()
    
    print("🚀 Starting mock data producer...")
    print(f"🔗 Connecting to: {producer.amqp_url}")
    print(f"📤 Target queue: {producer.input_queue}")
    
    try:
        # Send sample chunks
        print("\n📋 Sending sample chunks...")
        await producer.send_sample_chunks()
        
        # Send edge cases
        print("\n⚠️  Sending edge cases...")
        await producer.send_edge_cases()
        
        # Optional: Send stress test data (uncomment if needed)
        # print("\n🔥 Sending stress test data...")
        # await producer.send_stress_test_data(50)
        
        print("\n✅ All mock data sent successfully!")
        
    except Exception as e:
        print(f"❌ Error in mock data producer: {e}")

async def send_single_test_message():
    """Send a single test message for quick testing"""
    producer = MockDataProducer()
    
    test_message = {
        "title": "Test Message",
        "content": "This is a test message to verify the tagging agent is working properly.",
        "chunk_id": "test_001",
        "timestamp": "2024-01-15T10:30:00Z",
        "source": "test_producer"
    }
    
    print("📤 Sending single test message...")
    await producer.send_message(test_message)

async def continuous_mock_data_sender(interval=30, duration=300):
    """Send mock data continuously for testing"""
    producer = MockDataProducer()
    chunks = MockInputData.get_sample_chunks()
    
    print(f"🔄 Starting continuous sender (interval: {interval}s, duration: {duration}s)")
    
    start_time = asyncio.get_event_loop().time()
    message_count = 0
    
    while (asyncio.get_event_loop().time() - start_time) < duration:
        # Send a random chunk
        import random
        chunk = random.choice(chunks).copy()
        chunk["chunk_id"] = f"{chunk['chunk_id']}_continuous_{message_count}"
        chunk["timestamp"] = f"2024-01-15T{10 + (message_count % 12):02d}:30:00Z"
        
        await producer.send_message(chunk)
        message_count += 1
        
        await asyncio.sleep(interval)
    
    print(f"✅ Continuous sender finished. Sent {message_count} messages.")

if __name__ == "__main__":
    # Example usage of mock data
    chunks = MockInputData.get_sample_chunks()
    print(f"Generated {len(chunks)} sample chunks")
    
    tags = MockInputData.get_mock_tags()
    print(f"Generated {len(tags)} mock tags")
    
    responses = MockInputData.get_mock_bedrock_responses()
    print("Generated mock Bedrock responses")
    
    # Interactive menu
    print("\n" + "="*50)
    print("Mock Data Producer Menu:")
    print("1. Send all sample chunks")
    print("2. Send edge cases")
    print("3. Send single test message")
    print("4. Send stress test data")
    print("5. Start continuous sender")
    print("="*50)
    
    choice = input("Enter your choice (1-5): ").strip()
    
    if choice == "1":
        asyncio.run(send_mock_data_to_queue())
    elif choice == "2":
        async def send_edges():
            producer = MockDataProducer()
            await producer.send_edge_cases()
        asyncio.run(send_edges())
    elif choice == "3":
        asyncio.run(send_single_test_message())
    elif choice == "4":
        count = int(input("Enter number of stress messages (default 100): ") or "100")
        async def send_stress():
            producer = MockDataProducer()
            await producer.send_stress_test_data(count)
        asyncio.run(send_stress())
    elif choice == "5":
        interval = int(input("Enter interval in seconds (default 30): ") or "30")
        duration = int(input("Enter duration in seconds (default 300): ") or "300")
        asyncio.run(continuous_mock_data_sender(interval, duration))
    else:
        print("Invalid choice. Running default: send all sample chunks")
        asyncio.run(send_mock_data_to_queue())
