# WhatsApp Chat to JSONL Converter

This project provides a command-line tool for converting WhatsApp chat exports into JSONL (JSON Lines) format. This
formatted output can be used to fine-tune an OpenAI GPT model or other conversational AI applications. It includes
various utilities such as text cleaning, message moderation, and chat processing.

## Features

- **Chat Parsing:** Parses WhatsApp chat exports and extracts messages with timestamps, sender information, and content.
- **Moderation:** Optionally moderates chat messages using OpenAI's moderation API, filtering out inappropriate content.
- **Anonymization:** Anonymizes senders other than the assistant in the conversation.
- **Conversation Grouping:** Groups messages into conversations, handling time gaps and managing assistant/user message
  flows.
- **Paired Conversations:** Supports generating paired conversations for structured data preparation.
- **Output:** Writes the processed chat data to JSONL files for use in GPT model fine-tuning.
- **Logging:** Provides detailed logging for process tracing and debugging.

## Installation

### Prerequisites

- Python 3.8+
- `pip` package manager

### Setup

1. Clone the repository:

    ```bash
    git clone [<repository-url>](https://github.com/jaylann/WAC2J.git)
    cd WAC2J
    ```

2Install the package locally:

    ```bash
    pip install .
    ```

## Usage

### Command-line Interface

To run the chat processor, use the following command:

```bash
wac2j --sys-prompt "Your system prompt here" --name "AssistantName" input.txt
```

### Options

- `--sys-prompt`: **(Required)** System prompt to include in each conversation.
- `--name`: **(Required)** Name of the assistant in the chat.
- `--threshold`: Moderation threshold (default: `0.7`).
- `--api-key`: OpenAI API key (if not provided in `.env`).
- `--max-chars`: Maximum characters per conversation (default: `8000`).
- `--pairs`: Use paired mode for conversations.
- `--output`: Output file path (default: same as input with `.jsonl` extension).
- `--dir`: Directory containing input files to process.
- `--no-mod`: Skip moderation.
- `--merge`: Merge all JSONL files together.
- `input`: Input chat file path.

### Example

To process a single chat export file:

```bash
wac2j --sys-prompt "Your system prompt" --name "Assistant" --threshold 0.8 --output output.jsonl input.txt
```

To process all `.txt` files in a directory and merge them into a single JSONL file:

```bash
wac2j --sys-prompt "Your system prompt" --name "Assistant" --dir /path/to/chats --merge
```

## Extending the Project

This project is designed to be modular. You can easily extend the functionality by adding new models in the `models`
directory or additional processing functions in the `processing.py` file. One example use case would be the conversation
format. For example instead of using PersonX: PersonY: each time you could just remove it.

## Contributing

Feel free to fork this repository and create pull requests to improve the project. Make sure to write clear commit
messages and add comments to your code where necessary.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
