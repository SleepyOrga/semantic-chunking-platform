# inference.py

from transformers import AutoProcessor, VisionEncoderDecoderModel
import torch
from PIL import Image
import io
import json

class DOLPHIN:
    def __init__(self, model_id_or_path):
        self.processor = AutoProcessor.from_pretrained(model_id_or_path)
        self.model = VisionEncoderDecoderModel.from_pretrained(model_id_or_path)
        self.model.eval()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device).half()
        self.tokenizer = self.processor.tokenizer

    def chat(self, prompt, image):
        images = [image] if not isinstance(image, list) else image
        prompts = [prompt] if not isinstance(prompt, list) else prompt

        batch_inputs = self.processor(images, return_tensors="pt", padding=True)
        batch_pixel_values = batch_inputs.pixel_values.half().to(self.device)

        prompts = [f"<s>{p} <Answer/>" for p in prompts]
        batch_prompt_inputs = self.tokenizer(prompts, add_special_tokens=False, return_tensors="pt")

        batch_prompt_ids = batch_prompt_inputs.input_ids.to(self.device)
        batch_attention_mask = batch_prompt_inputs.attention_mask.to(self.device)

        outputs = self.model.generate(
            pixel_values=batch_pixel_values,
            decoder_input_ids=batch_prompt_ids,
            decoder_attention_mask=batch_attention_mask,
            max_length=4096,
            eos_token_id=self.tokenizer.eos_token_id,
            pad_token_id=self.tokenizer.pad_token_id,
            bad_words_ids=[[self.tokenizer.unk_token_id]],
        )

        sequences = self.tokenizer.batch_decode(outputs.sequences, skip_special_tokens=False)
        results = [seq.replace(p, "").replace("<pad>", "").replace("</s>", "").strip() for p, seq in zip(prompts, sequences)]

        return results[0] if len(results) == 1 else results


# Required SageMaker methods
_model = None

def model_fn(model_dir):
    global _model
    _model = DOLPHIN(model_id_or_path=model_dir)
    return _model

def input_fn(request_body, content_type='application/json'):
    data = json.loads(request_body)
    image_bytes = bytes(data['image'])  # should be base64 or binary in real use
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    prompt = data['prompt']
    return {"image": image, "prompt": prompt}

def predict_fn(input_data, model):
    return model.chat(prompt=input_data["prompt"], image=input_data["image"])

def output_fn(prediction, content_type='application/json'):
    return json.dumps({"output": prediction})
