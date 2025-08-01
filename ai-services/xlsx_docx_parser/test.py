import os
import pandas as pd
from typing import List, Dict

def read_xlsx_and_convert(filepath: str) -> Dict[str, List[str]]:
    xls = pd.ExcelFile(filepath)
    result = {}

    for sheetname in xls.sheet_names:
        df = xls.parse(sheetname, header=None, dtype=str)
        df = df.fillna("")
        lines = []

        current_table = []
        current_text_block = []

        for _, row in df.iterrows():
            row_vals = [str(cell).strip() for cell in row if str(cell).strip()]
            if not row_vals:
                # End of a block
                if current_table:
                    lines.extend(convert_table_to_sentences(current_table))
                    current_table = []
                    lines.append("\n")  # Add a blank line to separate blocks
                    
                if current_text_block:
                    lines.append("\n".join(current_text_block))
                    lines.append("\n")  # Add a blank line to separate blocks
                    current_text_block = []
                continue

            if is_probably_table_row(row):
                # Flush text block if needed
                if current_text_block:
                    lines.append(" ".join(current_text_block))
                    current_text_block = []

                current_table.append(row.tolist())
            else:
                # Flush table block if needed
                if current_table:
                    lines.extend(convert_table_to_sentences(current_table))
                    current_table = []
                current_text_block.append("\n".join(row_vals))

        # Flush any remaining data
        if current_table:
            lines.extend(convert_table_to_sentences(current_table))
        if current_text_block:
            lines.append("\n".join(current_text_block))

        result[sheetname] = lines
    return result


def is_probably_table_row(row, min_non_empty=2) -> bool:
    """
    A row is likely part of a table if it has enough non-empty cells
    and is consistent with tabular layout.
    """
    cells = [str(cell).strip() for cell in row]
    non_empty = sum(1 for cell in cells if cell)
    return non_empty >= min_non_empty


def convert_table_to_sentences(table_rows: List[List[str]]) -> List[str]:
    if not table_rows or len(table_rows) < 2:
        return []

    # Assume first row is header
    header = [str(cell).strip() for cell in table_rows[0]]
    sentences = []

    for row in table_rows[1:]:
        cells = [str(cell).strip() for cell in row]
        parts = []
        for col, val in zip(header, cells):
            if col and val:
                parts.append(f"{col}: {val}")
        sentence = ". ".join(parts)
        if sentence:
            sentences.append(sentence)
    return sentences


def save_to_text_files(sheet_data: Dict[str, List[str]], output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, f"output.txt"), "w", encoding="utf-8") as f:
        for sheetname, lines in sheet_data.items():
            f.write(f"# {sheetname}\n\n")
            for line in lines:
                f.write(line.strip() + "\n")
            f.write("\n")  # Add a blank line after each sheet


# --- Example usage ---
if __name__ == "__main__":
    filepath = "test_2.xlsx"  # Replace with your actual file path
    output_dir = "output_texts"

    sheet_data = read_xlsx_and_convert(filepath)
    save_to_text_files(sheet_data, output_dir)
