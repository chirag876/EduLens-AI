# =============================================================================
# Answer Safety and Moderation Module
# =============================================================================
#
# This module is responsible for validating AI-generated answers before they
# are returned to the student.
#
# The moderation layer acts as a final safety and quality gate between the
# LLM generation layer and the student-facing response.
#
# It checks whether the generated answer is sufficiently useful, safe,
# curriculum-focused, and relevant to the retrieved content.
#
# Processing Flow:
#
#     Generated Answer
#          │
#          ▼
#     Length Check
#          │
#          ▼
#     Harmful Content Check
#          │
#          ▼
#     Off-Curriculum Check
#          │
#          ▼
#     Relevance Check
#          │
#          ├── Failed → Safe Fallback Response
#          │
#          └── Passed → Return Original Answer
#
# Key Responsibilities:
#
# 1. Minimum Length Validation
#    - Checks whether the generated answer contains enough content to be
#      considered potentially useful.
#    - Answers shorter than the configured minimum length are rejected and
#      replaced with a polite fallback response.
#
# 2. Harmful Content Detection
#    - Performs a basic keyword-based safety check on the generated answer.
#    - Detects configured keywords associated with potentially harmful or
#      inappropriate content.
#    - If harmful content is detected, the original answer is not returned
#      to the student.
#
# 3. Off-Curriculum Detection
#    - Checks for predefined phrases that indicate the LLM may have moved
#      away from its intended educational role or curriculum context.
#    - Examples include references to being an AI, language model, or
#      external AI systems.
#
# 4. Curriculum Relevance Check
#    - Compares meaningful words from the generated answer with words present
#      in the retrieved curriculum chunks.
#    - Uses word overlap as a basic heuristic to determine whether the answer
#      is related to the retrieved content.
#    - At least three overlapping words are required for the answer to pass
#      the relevance check.
#
# 5. Sequential Safety Checks
#    - Checks are executed in a fixed sequence.
#    - The first failed check immediately returns an appropriate safe fallback
#      response instead of continuing with the remaining checks.
#
# 6. Safe Fallback Responses
#    - A failed moderation check does not return an application error to the
#      student.
#    - Instead, a polite and context-appropriate fallback message is returned.
#    - This keeps moderation failures user-friendly while preventing the
#      potentially unsuitable generated answer from being displayed.
#
# 7. Final Answer Validation
#    - If the answer passes all applicable checks, the original generated
#      answer is returned unchanged.
#
# 8. Input Validation and Error Handling
#    - Rejects empty or whitespace-only answers before running moderation.
#    - Unexpected moderation failures are converted into application-level
#      CustomHTTPException errors for consistent API error handling.
#
# =============================================================================

import re

from app.server.handler.error_handler import CustomHTTPException
from app.server.logger.custom_logger import logger
from app.server.static import error_identifier
from fastapi import status

# Keywords that indicate the LLM went off-curriculum
OFF_CURRICULUM_PHRASES = [
    'as an ai',
    'as a language model',
    'i am not able to',
    'i cannot provide',
    'i don\'t have access',
    'my training data',
    'openai',
    'chatgpt',
    'gpt-4',
    'anthropic',
    'claude',
]

# Harmful content keywords — basic filter
HARMFUL_KEYWORDS = [
    'violence',
    'weapon',
    'drug',
    'illegal',
    'explicit',
    'abuse',
    'hate',
    'suicide',
    'self-harm',
]

# Minimum answer length — if too short, likely not useful
MIN_ANSWER_LENGTH = 20


def check_harmful_content(text: str) -> bool:
    """
    Check if the text contains harmful content.

    Args:
        text (str): The text to check.

    Returns:
        bool: True if harmful content detected, False otherwise.
    """
    text_lower = text.lower()
    for keyword in HARMFUL_KEYWORDS:
        if keyword in text_lower:
            logger.debug(f'Harmful keyword detected: {keyword}')
            return True
    return False


def check_off_curriculum(text: str) -> bool:
    """
    Check if the LLM response went off-curriculum or broke character.

    Args:
        text (str): The generated answer text.

    Returns:
        bool: True if off-curriculum detected, False otherwise.
    """
    text_lower = text.lower()
    for phrase in OFF_CURRICULUM_PHRASES:
        if phrase in text_lower:
            logger.debug(f'Off-curriculum phrase detected: {phrase}')
            return True
    return False


def check_relevance(answer: str, chunks: list[dict]) -> bool:
    """
    Basic relevance check — verify the answer has some overlap
    with the retrieved curriculum chunks.

    Args:
        answer (str): The generated answer.
        chunks (list[dict]): Retrieved curriculum chunks.

    Returns:
        bool: True if answer seems relevant, False otherwise.
    """
    if not chunks:
        return False

    # Extract key words from chunks (words longer than 4 chars)
    chunk_words = set()
    for chunk in chunks:
        words = re.findall(r'\b\w{5,}\b', chunk['text'].lower())
        chunk_words.update(words)

    # Check overlap with answer words
    answer_words = set(re.findall(r'\b\w{5,}\b', answer.lower()))
    overlap = chunk_words.intersection(answer_words)

    # At least 3 words should overlap for relevance
    is_relevant = len(overlap) >= 3
    if not is_relevant:
        logger.debug(f'Low relevance detected — only {len(overlap)} overlapping words')
    return is_relevant


def moderate_answer(answer: str, chunks: list[dict]) -> dict:
    """
    Run all safety and relevance checks on the generated answer.

    Args:
        answer (str): The LLM-generated answer.
        chunks (list[dict]): Retrieved curriculum chunks used for generation.

    Returns:
        dict: Moderation result with status and final answer.
    """
    if not answer or not answer.strip():
        raise CustomHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Answer cannot be empty for moderation',
            identifier=error_identifier.UNPROCESS_ENTITY,
        )

    try:
        # Check 1: Minimum length
        if len(answer.strip()) < MIN_ANSWER_LENGTH:
            logger.debug('Answer too short — failed moderation')
            return {
                'passed': False,
                'reason': 'Answer too short',
                'final_answer': 'I could not generate a proper answer. Please rephrase your question.',
            }

        # Check 2: Harmful content
        if check_harmful_content(answer):
            logger.debug('Answer failed harmful content check')
            return {
                'passed': False,
                'reason': 'Harmful content detected',
                'final_answer': 'I am not able to provide this information. Please contact your teacher.',
            }

        # Check 3: Off-curriculum detection
        if check_off_curriculum(answer):
            logger.debug('Answer failed off-curriculum check')
            return {
                'passed': False,
                'reason': 'Off-curriculum response detected',
                'final_answer': 'I could not find a reliable answer in the curriculum. Please refer to your teacher.',
            }

        # Check 4: Relevance check
        if chunks and not check_relevance(answer, chunks):
            logger.debug('Answer failed relevance check')
            return {
                'passed': False,
                'reason': 'Answer not relevant to curriculum content',
                'final_answer': 'I could not find relevant information in the curriculum for your question.',
            }

        logger.debug('Answer passed all moderation checks')
        return {
            'passed': True,
            'reason': None,
            'final_answer': answer,
        }

    except CustomHTTPException:
        raise
    except Exception as error:
        raise CustomHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to moderate answer: {str(error)}',
            identifier=error_identifier.SAFETY_CHECK_FAILED,
        ) from error