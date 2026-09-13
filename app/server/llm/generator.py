# =============================================================================
# LLM Answer Generation Module
# =============================================================================
#
# This module is responsible for generating student-friendly answers using
# retrieved curriculum content as the context for the LLM.
#
# It acts as the final generation layer of the RAG pipeline. Retrieved chunks
# from PDF documents and video transcripts are provided to the LLM, which uses
# them to generate a grounded answer to the student's question.
#
# Processing Flow:
#
#     Student Question
#          │
#          ▼
#     Retrieved Chunks
#          │
#          ▼
#     Build Context
#          │
#          ▼
#     Build Strict Prompt
#          │
#          ▼
#     Groq API
#     (Configured LLM Model)
#          │
#          ▼
#     Generate Answer
#          │
#          ▼
#     Attach Source References
#          │
#          ▼
#     Return Answer + Sources
#
# Key Responsibilities:
#
# 1. Groq Client Management
#    - Initializes the Groq API client using the configured API key.
#    - The client is initialized only once and the same instance is reused
#      across requests.
#    - This avoids unnecessary client initialization for every request.
#
# 2. Context Construction
#    - Combines the retrieved PDF and video chunks into a single context string.
#    - Each chunk is labeled with its source number, source type, and title.
#    - If no relevant chunks are available, an explicit empty-context message
#      is provided to the LLM.
#
# 3. Prompt Construction
#    - Builds a structured prompt containing the student's question and the
#      retrieved curriculum context.
#    - Optionally includes the student's grade level so that the language and
#      complexity can be adjusted accordingly.
#
# 4. Grounded Answer Generation
#    - Instructs the LLM to answer strictly using the provided curriculum
#      context.
#    - The prompt explicitly prevents the model from inventing information.
#    - If the required information is not present in the retrieved context,
#      the model is instructed to clearly state that it could not find the
#      answer in the curriculum.
#
# 5. Controlled LLM Generation
#    - Uses a low temperature of 0.3 to make responses more focused and
#      consistent rather than unnecessarily creative.
#    - Limits the generated response to a maximum of 1024 tokens.
#
# 6. Source References
#    - Collects source information from the retrieved chunks after generating
#      the answer.
#    - Duplicate URLs are removed so that the same source is returned only
#      once.
#    - Each source contains its title, source type, and URL.
#
# 7. Input Validation and Error Handling
#    - Rejects empty or whitespace-only questions before calling the LLM.
#    - Converts unexpected LLM generation failures into application-level
#      CustomHTTPException errors for consistent API error handling.
#
# =============================================================================

from groq import Groq

from app.server.config import config
from app.server.handler.error_handler import CustomHTTPException
from app.server.logger.custom_logger import logger
from app.server.static import error_identifier
from app.server.static.enums import GradeLevel
from typing import Optional
from fastapi import status
import templates as temp

# Initialize Groq client once
_groq_client = None


def get_groq_client() -> Groq:
    """
    Returns the Groq client instance.
    Initializes once and reuses across all requests (singleton pattern).

    Returns:
        Groq: The Groq client instance.
    """
    global _groq_client
    if _groq_client is None:
        logger.debug('Initializing Groq client')
        _groq_client = Groq(api_key=config.GROQ_API_KEY)
        logger.debug('Groq client initialized successfully')
    return _groq_client


def build_context(chunks: list[dict]) -> str:
    """
    Build a context string from retrieved chunks to pass to the LLM.

    Args:
        chunks (list[dict]): Retrieved chunks from ChromaDB with text and metadata.

    Returns:
        str: Formatted context string.
    """
    if not chunks:
        return 'No relevant content found in the curriculum.'

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source_type = chunk['metadata'].get('source_type', 'unknown')
        title = chunk['metadata'].get('title', 'Unknown Source')
        context_parts.append(
            f'[Source {i} — {source_type.upper()} — {title}]\n{chunk["text"]}'
        )

    return '\n\n---\n\n'.join(context_parts)


def build_prompt(question: str, context: str, grade_level: str = None) -> str:
    """
    Build the prompt for the LLM using the question and retrieved context.

    Args:
        question (str): The student's question.
        context (str): Retrieved curriculum context.
        grade_level (str, optional): Student's grade level for personalization.

    Returns:
        str: The formatted prompt.
    """
    grade_instruction = ''
    if grade_level:
        grade_instruction = f'The student is at {grade_level} level. Adjust your language and complexity accordingly.\n'

    prompt = f"""You are an educational AI assistant. Your job is to answer student questions 
strictly based on the curriculum content provided below. 

{grade_instruction}
IMPORTANT RULES:
- Only use information from the provided curriculum context.
- If the answer is not in the context, say: "I could not find this in the curriculum. Please refer to your teacher."
- Be clear, concise, and educational in your response.
- Do not make up information.

CURRICULUM CONTEXT:
{context}

STUDENT QUESTION:
{question}

ANSWER:"""

    return prompt


# generator.py
# def build_prompt(question: str, context: str,  grade_level: Optional[GradeLevel] = None) -> str:
#     prompt = temp.load_prompt_template()
#     return prompt.format(
#         institution_name=config.INSTITUTION_NAME,
#         language=config.CLIENT_LANGUAGE,
#         tone=config.CLIENT_TONE,
#         grade_level=grade_level.value if grade_level else "",
#         context=context,
#         question=question,
#     )


def generate_answer(question: str, chunks: list[dict], grade_level: str = None) -> dict:
    """
    Generate an answer for the student's question using retrieved curriculum chunks.

    Args:
        question (str): The student's question.
        chunks (list[dict]): Retrieved relevant chunks from ChromaDB.
        grade_level (str, optional): Student's grade level for personalization.

    Returns:
        dict: Generated answer with sources.
    """
    if not question or not question.strip():
        raise CustomHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Question cannot be empty for answer generation',
            identifier=error_identifier.UNPROCESS_ENTITY,
        )

    try:
        # Step 1: Build context from chunks
        context = build_context(chunks)

        # Step 2: Build prompt
        prompt = build_prompt(question, context, grade_level)

        # Step 3: Call Groq API
        logger.debug(f'Calling Groq API for question: {question[:80]}...')
        client = get_groq_client()

        response = client.chat.completions.create(
            model=config.GROQ_MODEL_NAME,
            messages=[
                {
                    'role': 'system',
                    'content': 'You are a helpful educational AI assistant for students.',
                },
                {
                    'role': 'user',
                    'content': prompt,
                },
            ],
            temperature=0.3,
            max_tokens=1024,
        )

        answer = response.choices[0].message.content.strip()
        logger.debug('Answer generated successfully')

        # Step 4: Build sources list
        sources = []
        seen_urls = set()
        for chunk in chunks:
            url = chunk['metadata'].get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                sources.append({
                    'title': chunk['metadata'].get('title', 'Unknown'),
                    'source_type': chunk['metadata'].get('source_type', 'unknown'),
                    'url': url,
                })

        return {
            'answer': answer,
            'sources': sources,
        }

    except CustomHTTPException:
        raise
    except Exception as error:
        raise CustomHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to generate answer: {str(error)}',
            identifier=error_identifier.LLM_GENERATION_FAILED,
        ) from error
