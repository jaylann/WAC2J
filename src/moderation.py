"""
Module for moderating chat messages using OpenAI's moderation API.

This module provides functionality to moderate chat messages in parallel,
applying rate limiting to API calls and filtering messages based on
moderation scores.
"""

import concurrent.futures
import logging
from typing import List, Tuple, Optional

from openai import OpenAI
from ratelimit import limits, sleep_and_retry
from tqdm import tqdm

from src.models.ChatMessage import ChatMessage
from src.models.ModerationResult import ModerationResult

# Constants for rate limiting
CALLS_PER_MINUTE = 1000
ONE_MINUTE = 60

@sleep_and_retry
@limits(calls=CALLS_PER_MINUTE, period=ONE_MINUTE)
def rate_limited_api_call(client: OpenAI, content: str):
    """
    Make a rate-limited API call to the OpenAI moderation endpoint.

    Args:
        client (OpenAI): The OpenAI client.
        content (str): The content to moderate.

    Returns:
        The API response.
    """
    return client.moderations.create(input=content)

def moderate_single_message(
        msg: ChatMessage,
        client: OpenAI,
        threshold: float
) -> Tuple[ChatMessage, Optional[List[Tuple[str, float]]]]:
    """
    Moderate a single message using the OpenAI API.

    Args:
        msg (ChatMessage): The message to moderate.
        client (OpenAI): The OpenAI client.
        threshold (float): The threshold for flagging content.

    Returns:
        Tuple[ChatMessage, Optional[List[Tuple[str, float]]]]: The original message and any flagged categories.
    """
    try:
        response = rate_limited_api_call(client, msg.content)
        result = ModerationResult(**response.results[0].model_dump())

        flagged_categories = [
            (category, score)
            for category, score in result.category_scores.items()
            if score > threshold
        ]

        return msg, flagged_categories if flagged_categories else None
    except Exception as e:
        logging.error(f"Error processing message: {str(e)}")
        return msg, None

def moderate_messages(
        messages: List[ChatMessage],
        api_key: Optional[str],
        threshold: float
) -> List[ChatMessage]:
    """
    Moderate a list of chat messages.

    Args:
        messages (List[ChatMessage]): The list of messages to moderate.
        api_key (Optional[str]): The OpenAI API key.
        threshold (float): The threshold for flagging content.

    Returns:
        List[ChatMessage]: The list of messages that passed moderation.
    """
    if not api_key:
        api_key = input("Enter your OpenAI API key (If you dont want to use moderation use --no-mod): ")

    client = OpenAI(api_key=api_key)
    cleaned_messages = []
    flagged_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        futures = {executor.submit(moderate_single_message, msg, client, threshold): msg for msg in messages}

        with tqdm(total=len(messages), desc="Moderating messages") as pbar:
            for future in concurrent.futures.as_completed(futures):
                msg, flagged_categories = future.result()
                if not flagged_categories:
                    cleaned_messages.append(msg)
                else:
                    flagged_count += 1
                pbar.update(1)

    logging.info(f"Moderation complete. {flagged_count} messages flagged and removed.")
    return cleaned_messages