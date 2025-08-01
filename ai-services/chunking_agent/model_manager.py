import time
from typing import Dict, Optional
from dataclasses import dataclass
import logging
from document_classifier import DocumentClassifier

logger = logging.getLogger("ModelManager")

@dataclass
class ModelConfig:
    model_id: str
    requests_per_minute: int
    last_request_time: float = 0
    request_count: int = 0

class ModelManager:
    def __init__(self):
        self.models: Dict[str, ModelConfig] = {
            # US region models
            "us.anthropic.claude-3-5-haiku-20241022-v1:0": ModelConfig(
                model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
                requests_per_minute=20  # Fastest model
            ),
            "us.anthropic.claude-3-5-sonnet-20240620-v1:0": ModelConfig(
                model_id="us.anthropic.claude-3-5-sonnet-20240620-v1:0",
                requests_per_minute=10
            ),
            "us.anthropic.claude-3-7-sonnet-20250219-v1:0": ModelConfig(
                model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                requests_per_minute=4
            ),
            "us.anthropic.claude-sonnet-4-20250514-v1:0": ModelConfig(
                model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
                requests_per_minute=2
            ),
            "us.anthropic.claude-opus-4-20250514-v1:0": ModelConfig(
                model_id="us.anthropic.claude-opus-4-20250514-v1:0",
                requests_per_minute=2
            ),
            "us.anthropic.claude-3-sonnet-20240229-v1:0": ModelConfig(
                model_id="us.anthropic.claude-3-sonnet-20240229-v1:0",
                requests_per_minute=10
            )
        }
        
        self.document_classifier = DocumentClassifier()
        
        self.current_model: Optional[str] = None
        self.last_rotation_time = time.time()

    def _can_use_model(self, model_config: ModelConfig) -> bool:
        current_time = time.time()
        time_diff = current_time - model_config.last_request_time
        
        # Reset counter if a minute has passed
        if time_diff >= 60:
            model_config.request_count = 0
            model_config.last_request_time = current_time
            return True
            
        return model_config.request_count < model_config.requests_per_minute

    def get_available_model(self, content: Optional[str] = None) -> Optional[str]:
        # If content is provided, detect document type and get recommended models
        recommended_models = {}
        if content:
            doc_type = self.document_classifier.detect_document_type(content)
            recommended_models = self.document_classifier.get_recommended_models(doc_type)
            logger.info(f"Detected document type: {doc_type.value}")
            logger.info(f"Recommended models for {doc_type.value}: {recommended_models}")
        
        # Try current model first if it exists, can be used, and is recommended
        print(f"[DEBUG] Current model: {self.current_model}")
        if self.current_model and self._can_use_model(self.models[self.current_model]):
            if not recommended_models or self.current_model in recommended_models:
                model_config = self.models[self.current_model]
                model_config.request_count += 1
                model_config.last_request_time = time.time()
                return self.current_model

        # Find model with highest requests_per_minute that can be used
        if recommended_models:
            available_models = sorted(
                [self.models[m] for m in recommended_models if m in self.models],
                key=lambda x: (-x.requests_per_minute, x.last_request_time)
            )
        else:
            available_models = sorted(
                self.models.values(),
                key=lambda x: (-x.requests_per_minute, x.last_request_time)
            )
        
        for model_config in available_models:
            if self._can_use_model(model_config):
                self.current_model = model_config.model_id
                model_config.request_count += 1
                model_config.last_request_time = time.time()
                return model_config.model_id
        
        # If no model is available, wait for the one with shortest wait time
        min_wait_time = float('inf')
        best_model = None
        
        for model_config in self.models.values():
            if model_config.request_count >= model_config.requests_per_minute:
                wait_time = 60 - (time.time() - model_config.last_request_time)
                if wait_time < min_wait_time:
                    min_wait_time = wait_time
                    best_model = model_config.model_id
        
        if best_model:
            time.sleep(max(0, min_wait_time))
            return self.get_available_model()
        
        return None

    def release_model(self, model_id: str):
        """Mark a model as done with its current request"""
        if model_id in self.models:
            self.models[model_id].last_request_time = time.time()
