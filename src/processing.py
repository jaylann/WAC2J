import json
import logging
import re
from datetime import datetime, timedelta
from itertools import groupby
from pathlib import Path
from typing import List, Dict, Any, Iterator

from .models.Conversation import Conversation
from .models.ProcessingContext import ProcessingContext
from .moderation import moderate_messages, ChatMessage
from .utils.logger import setup_logging
from .utils.text import clean_text_file

setup_logging()

def parse_chat_file(file_path: Path) -> List[ChatMessage]:
    """
    Parse a chat file and extract messages.

    Args:
        file_path (Path): Path to the chat file.

    Returns:
        List[ChatMessage]: List of parsed chat messages.

    Raises:
        IOError: If there's an error reading the file.
    """
    messages = []
    pattern = r'^\[(\d{2}\.\d{2}\.\d{4}, \d{2}:\d{2}:\d{2})\] ([^:]+): (.*)$'
    current_message = None

    try:
        with file_path.open('r', encoding='utf-8-sig') as file:
            for line_number, line in enumerate(file, 1):
                match = re.match(pattern, line.strip())
                if match:
                    if current_message:
                        messages.append(current_message)

                    timestamp_str, sender, content = match.groups()
                    try:
                        timestamp = datetime.strptime(timestamp_str, '%d.%m.%Y, %H:%M:%S')
                    except ValueError:
                        logging.warning(f"Invalid timestamp format at line {line_number}: {timestamp_str}")
                        continue

                    current_message = ChatMessage(sender=sender.strip(), timestamp=timestamp, content=content.strip())
                elif current_message:
                    current_message.content += f"\n{line.strip()}"
                else:
                    logging.warning(f"Skipping malformed line {line_number}: {line.strip()}")

        if current_message:
            messages.append(current_message)

    except IOError as e:
        logging.error(f"Error reading file {file_path}: {str(e)}")
        raise

    if not messages:
        logging.warning(f"No valid messages found in {file_path}")

    return messages


def sort_messages_by_timestamp(messages: List[ChatMessage]) -> List[ChatMessage]:
    """Sort messages by their timestamp."""
    return sorted(messages, key=lambda message: message.timestamp)


def process_chat_messages(messages: List[ChatMessage], api_key: str, threshold: float, no_mod: bool) -> List[
    ChatMessage]:
    """
    Process chat messages, applying moderation if required.

    Args:
        messages (List[ChatMessage]): List of chat messages to process.
        api_key (str): API key for moderation.
        threshold (float): Moderation threshold.
        no_mod (bool): If True, skip moderation.

    Returns:
        List[ChatMessage]: Processed and sorted list of chat messages.
    """
    logging.info(f"Total messages: {len(messages)}")
    if no_mod:
        return sort_messages_by_timestamp(messages)
    cleaned_messages = moderate_messages(messages, api_key, threshold)
    logging.info(f"Cleaned messages: {len(cleaned_messages)}")
    logging.info(f"Removed messages: {len(messages) - len(cleaned_messages)}")
    return sort_messages_by_timestamp(cleaned_messages)


def anonymize_sender(sender: str, assistant_name: str, context: ProcessingContext) -> str:
    """Anonymize the sender's name."""
    if sender == assistant_name:
        return sender
    if sender not in context.person_map:
        context.person_map[sender] = f"Person{context.person_index}"
        context.person_index += 1
    return context.person_map[sender]


def format_grouped_messages(messages: List[ChatMessage], role: str, assistant_name: str, context: ProcessingContext) -> \
        Dict[str, Any]:
    """Format grouped messages into a single message dict."""
    content = "\n".join(
        f"{anonymize_sender(msg.sender, assistant_name, context)}: {msg.content.removeprefix(f'{assistant_name}: ').strip()}"
        if role == "user" else msg.content.removeprefix(f"{assistant_name}: ").strip()
        for msg in messages
    )
    result = {"role": role, "content": content}
    if role == "assistant":
        result["weight"] = 1

    context.total_chars += len(content) + 7
    return result


def get_previous_user_messages(prev_conversation: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
    """Get the most recent user messages from the previous conversation."""
    user_messages = []
    for message in reversed(prev_conversation[1:]):  # Skip system message
        if message["role"] == "assistant":
            break
        user_messages.append(message)
    return list(reversed(user_messages[-limit:]))


def process_message_group(is_assistant: bool, group: Iterator[ChatMessage], grouped_messages: List[ChatMessage],
                          current_conversation: List[Dict[str, Any]], assistant_name: str,
                          context: ProcessingContext) -> None:
    group_messages = list(group)
    logging.debug(f"Processing message group: {'assistant' if is_assistant else 'user'}, messages: {[msg.content for msg in group_messages]}")
    if is_assistant:
        if grouped_messages:
            formatted_user = format_grouped_messages(grouped_messages, "user", assistant_name, context)
            logging.debug(f"Appending formatted user messages: {formatted_user}")
            current_conversation.append(formatted_user)
            grouped_messages.clear()
        formatted_assistant = format_grouped_messages(group_messages, "assistant", assistant_name, context)
        logging.debug(f"Appending formatted assistant messages: {formatted_assistant}")
        current_conversation.append(formatted_assistant)
    else:
        grouped_messages.extend(group_messages)
        logging.debug(f"Extended grouped_messages: {[msg.content for msg in grouped_messages]}")



def finalize_conversation(current_conversation: List[Dict[str, Any]], conversations: List[Conversation],
                          system_prompt: str) -> None:
    """Finalize the current conversation and add it to the list of conversations."""
    carry = []
    real_convo = []
    for msg in current_conversation:
        if msg["role"] != "assistant":
            carry.append(msg)
        else:
            real_convo.extend(carry)
            real_convo.append(msg)
            carry = []
    if real_convo and any(msg["role"] == "assistant" for msg in real_convo):
        conversations.append(Conversation(messages=[{"role": "system", "content": system_prompt}] + real_convo))
    current_conversation.clear()
    current_conversation.extend(carry)


def process_chat(system_prompt: str, file_path: Path, threshold: float, api_key: str, max_chars: int, pairs: bool,
                 assistant_name: str, no_mod: bool) -> List[Conversation]:
    """
    Process the chat file and generate conversations.

    Args:
        system_prompt (str): System prompt to include in each conversation.
        file_path (Path): Path to the input chat file.
        threshold (float): Moderation threshold.
        api_key (str): API key for moderation.
        max_chars (int): Maximum number of characters per conversation.
        pairs (bool): If True, generate paired conversations.
        assistant_name (str): Name of the assistant in the chat.
        no_mod (bool): If True, skip moderation.

    Returns:
        List[Conversation]: List of processed conversations.
    """
    tmp_path = Path("tmp.txt")
    clean_text_file(file_path, tmp_path)
    chat_messages = sort_messages_by_timestamp(
        process_chat_messages(parse_chat_file(tmp_path), api_key, threshold, no_mod))
    tmp_path.unlink()
    conversations: List[Conversation] = []
    current_conversation: List[Dict[str, Any]] = []
    context = ProcessingContext()
    grouped_messages: List[ChatMessage] = []
    last_timestamp = None

    for is_assistant, group in groupby(chat_messages, key=lambda m: m.sender == assistant_name):
        group_messages = list(group)
        logging.debug(f"Processing {'assistant' if is_assistant else 'user'} group with {len(group_messages)} messages")

        # Handle time gaps
        if last_timestamp and (group_messages[0].timestamp - last_timestamp > timedelta(hours=6)):
            logging.debug("Time gap detected, finalizing current conversation")
            if grouped_messages:
                formatted_user = format_grouped_messages(grouped_messages, "user", assistant_name, context)
                logging.debug(f"Appending formatted user messages due to time gap: {formatted_user}")
                current_conversation.append(formatted_user)
                grouped_messages.clear()
            finalize_conversation(current_conversation, conversations, system_prompt)

        # If there's no current conversation and the group is assistant, add previous user messages
        if not current_conversation and is_assistant and conversations and not grouped_messages:
            logging.debug("No current conversation, assistant message detected, adding previous user messages")
            prev_conversation = conversations[-1].messages
            previous_user_msgs = get_previous_user_messages(prev_conversation)
            logging.debug(f"Previous user messages: {previous_user_msgs}")
            current_conversation.extend(previous_user_msgs)

        if is_assistant:
            if grouped_messages:
                logging.debug("Appending formatted user messages before assistant messages")
                formatted_user = format_grouped_messages(grouped_messages, "user", assistant_name, context)
                current_conversation.append(formatted_user)
                grouped_messages.clear()
            logging.debug("Appending formatted assistant messages")
            formatted_assistant = format_grouped_messages(group_messages, "assistant", assistant_name, context)
            current_conversation.append(formatted_assistant)
        else:
            logging.debug("Extending grouped_messages with user messages")
            grouped_messages.extend(group_messages)

        last_timestamp = group_messages[-1].timestamp
        logging.debug(f"Updated last_timestamp to {last_timestamp}")

        if context.total_chars > max_chars:
            logging.debug("Max characters exceeded, finalizing current conversation")
            finalize_conversation(current_conversation, conversations, system_prompt)
            context.total_chars = 0

    # Handle any remaining grouped_messages after the loop
    if grouped_messages:
        logging.debug("Appending remaining grouped user messages after loop")
        formatted_user = format_grouped_messages(grouped_messages, "user", assistant_name, context)
        current_conversation.append(formatted_user)
    finalize_conversation(current_conversation, conversations, system_prompt)

    if pairs:
        conversations = create_paired_conversations(conversations, system_prompt)

    logging.info(f"Total characters processed: {context.total_chars}")
    return conversations


def create_paired_conversations(conversations: List[Conversation], system_prompt: str) -> List[Conversation]:
    """Create paired conversations from the original conversations."""
    paired_conversations = []
    for conv in conversations:
        user_messages = [msg for msg in conv.messages if msg["role"] == "user"]
        assistant_messages = [msg for msg in conv.messages if msg["role"] == "assistant"]
        if user_messages and assistant_messages:
            paired_conversations.append(Conversation(messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "\n".join(msg["content"] for msg in user_messages)},
                assistant_messages[-1]  # last assistant message
            ]))
    return paired_conversations


def process_and_write_chat(system_prompt: str, file_path: Path, output_file: Path, threshold: float, api_key: str,
                           max_chars: int, pairs: bool, assistant_name: str, no_mod: bool, merge: bool) -> None:
    """
    Process the chat file and write the result to an output file.

    Args:
        system_prompt (str): System prompt to include in each conversation.
        file_path (Path): Path to the input chat file.
        output_file (Path): Path to the output file.
        threshold (float): Moderation threshold.
        api_key (str): API key for moderation.
        max_chars (int): Maximum number of characters per conversation.
        pairs (bool): If True, generate paired conversations.
        assistant_name (str): Name of the assistant in the chat.
        no_mod (bool): If True, skip moderation.
        merge (bool): If True, append to the output file instead of overwriting.

    Raises:
        Exception: If there's an error processing the chat or writing the output.
    """
    try:
        result = process_chat(system_prompt, file_path, threshold, api_key, max_chars, pairs, assistant_name, no_mod)

        # Determine the file mode based on the merge flag
        file_mode = "a" if merge else "w"

        # Ensure the parent directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with output_file.open(file_mode, encoding="utf-8") as f:
            for conv in result:
                # Convert each conversation dictionary to a JSON string
                json_str = json.dumps(conv.model_dump(), default=str)
                # Write the JSON string to the file, followed by a newline character
                f.write(json_str + '\n')

        action = "appended to" if merge else "written to"
        logging.info(f"Successfully {action} {output_file}")

    except Exception as e:
        logging.error(f"Error processing chat {file_path}: {str(e)}")
        raise
