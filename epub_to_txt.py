import os
import argparse
from ebooklib import epub
from bs4 import BeautifulSoup
import warnings

def epub_to_text(epub_path):
    # Suppress specific warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="ebooklib.epub")
    warnings.filterwarnings("ignore", category=FutureWarning, module="ebooklib.epub")
    
    book = epub.read_epub(epub_path)
    text = []

    for item in book.get_items():
        if item.get_type() == 9:  # 9 corresponds to ITEM_DOCUMENT in ebooklib
            soup = BeautifulSoup(item.get_body_content(), 'html.parser')
            text.append(soup.get_text())

    return '\n'.join(text)

def save_text_to_file(text, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)

def main(epub_path):
    # Extract the base name of the input file
    base_name = os.path.splitext(os.path.basename(epub_path))[0]
    # Create the output text file path
    output_text_path = f"{base_name}.txt"

    # Extract text and save to file
    text = epub_to_text(epub_path)
    save_text_to_file(text, output_text_path)

    print(f"Text extracted and saved to {output_text_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert EPUB to Text")
    parser.add_argument("epub_path", help="Path to the EPUB file")
    args = parser.parse_args()

    main(args.epub_path)