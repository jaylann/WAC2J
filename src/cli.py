# chat_processor/cli.py
import argparse
import os
from dotenv import load_dotenv

def parse_arguments():
    load_dotenv(".env")

    parser = argparse.ArgumentParser(description="Process chat messages and format them into conversations.")
    parser.add_argument("-s", "--sys-prompt", required=True, help="System prompt to use")
    parser.add_argument("-t", "--threshold", type=float, default=0.7, help="Threshold for moderation (default: 0.7)")
    parser.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY"), help="OpenAI API key")
    parser.add_argument("-m", "--max-chars", type=int, default=8000, help="Maximum characters per conversation")
    parser.add_argument("-p", "--pairs", action="store_true", help="Use pairs mode for conversations")
    parser.add_argument("-n", "--name", required=True, help="Name of the assistant in the chat")
    parser.add_argument("-o", "--output", help="Output file path (default: same as input with .jsonl extension)")
    parser.add_argument("-d", "--dir", help="Directory containing input files to process")
    parser.add_argument("--no-mod", action="store_true", help="If true doesnt do moderation")
    parser.add_argument("--merge", action="store_true", help="Merge all jsonl files together")
    parser.add_argument("input", nargs="?", help="Input chat file path")

    args = parser.parse_args()

    if not args.dir and not args.input:
        parser.error("Either -d/--dir or an input file must be provided")

    return args