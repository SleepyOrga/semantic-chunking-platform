from datasets import load_dataset

# Tải tập filtered-cuad
dataset = load_dataset("alex-apostolo/filtered-cuad", split="train")

# In 1 item mẫu và cấu trúc dữ liệu
print(dataset[0])
print(dataset.features)
