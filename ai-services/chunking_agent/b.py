from excel_preprocessing_steps import ExcelPreprocessor

# Step 1: Read content from a.md
with open("a.md", "r", encoding="utf-8") as f:
    markdown_content = f.read()

# Step 2: Instantiate the preprocessor
preprocessor = ExcelPreprocessor()

# Step 3: Run preprocessing
enhanced_content, metadata = preprocessor.preprocess_excel_markdown(markdown_content)

# Step 4: Output results
print("=== Enhanced Markdown Content ===\n")
print(enhanced_content)

print("\n=== Metadata ===\n")
for key, value in metadata.items():
    print(f"{key}: {value}")

# Optional: Save enhanced content to a new file
with open("a_enhanced.md", "w", encoding="utf-8") as f:
    f.write(enhanced_content)
