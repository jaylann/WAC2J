import logging
import re
from pathlib import Path


def clean_text_file(input_file: Path, output_file: Path):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        cleaned_content = re.sub(r'[\u200E\u200F\u202A-\u202E]', '', content)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)

        logging.info(f"Successfully cleaned text file {input_file} and saved to {output_file}")
    except IOError as e:
        logging.error(f"Error cleaning text file {input_file}: {str(e)}")
        raise
