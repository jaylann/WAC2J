#!/usr/bin/env python3
"""
Main script for the chat processor application.

This script handles the command-line interface and orchestrates the processing
of chat files, either individually or in bulk from a directory.
"""

import logging
import sys

from pydantic import ValidationError

from src.models.ProcessingArgs import ProcessingArgs
from src.utils.logger import setup_logging
from .cli import parse_arguments
from .processing import process_and_write_chat


def process_single_file(args: ProcessingArgs) -> None:
    """
    Process a single input file and write the results to an output file.

    Args:
        args (ProcessingArgs): Validated command-line arguments.

    Raises:
        Exception: If there's an error during processing.
    """
    output_file = args.output or args.input.with_suffix('.jsonl')

    try:
        process_and_write_chat(
            args.sys_prompt,
            args.input,
            output_file,
            args.threshold,
            args.api_key,
            args.max_chars,
            args.pairs,
            args.name,
            args.no_mod,
            args.merge
        )
        logging.info(f"Successfully processed {args.input} and saved to {output_file}")
    except Exception as e:
        logging.error(f"Error processing {args.input}: {str(e)}")
        raise


def process_directory(args: ProcessingArgs) -> None:
    """
    Process all .txt files in the specified directory and write results to an output directory.

    Args:
        args (ProcessingArgs): Validated command-line arguments.

    Raises:
        Exception: If there's an error during processing.
    """
    input_dir = args.dir
    output_dir = input_dir / "output"
    output_dir.mkdir(exist_ok=True)

    for input_file in input_dir.glob("*.txt"):
        if not args.merge:
            output_file = output_dir / input_file.with_suffix('.jsonl').name
        else:
            output_file = output_dir / "output.jsonl"
        try:
            process_and_write_chat(
                args.sys_prompt,
                input_file,
                output_file,
                args.threshold,
                args.api_key,
                args.max_chars,
                args.pairs,
                args.name,
                args.no_mod,
                args.merge
            )
            logging.info(f"Successfully processed {input_file} and saved to {output_file}")
        except Exception as e:
            logging.error(f"Error processing {input_file}: {str(e)}")


def main() -> int:
    """
    Main function to run the chat processor application.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    setup_logging()

    try:
        cli_args = parse_arguments()
        args = ProcessingArgs(**vars(cli_args))
    except ValidationError as e:
        logging.error(f"Invalid arguments: {e}")
        return 1

    try:
        if args.dir:
            process_directory(args)
        else:
            process_single_file(args)
        return 0
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
