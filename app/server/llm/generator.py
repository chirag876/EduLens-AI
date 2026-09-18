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

from groq import Groq

from app.server.config import config
from app.server.handler.error_handler import CustomHTTPException
from app.server.logger.custom_logger import logger
from app.server.static import error_identifier
from app.server.static.enums import GradeLevel
from typing import Optional
from fastapi import status
import app.server.templates as temp

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

# llm/generator.py

def build_sources(chunks: list[dict]) -> list[dict]:
    """
    Build a deduplicated list of sources with full citation details.
    Groups chunks by URL and collects all unique page numbers per source.
 
    Args:
        chunks (list[dict]): Retrieved chunks from ChromaDB.
 
    Returns:
        list[dict]: List of sources with title, type, url, pages cited.
    """
    sources_map = {}

    for chunk in chunks:
        # Debug print to verify ChromaDB retrieval
        metadata = chunk.get('metadata', {}) or {}
        
        url = metadata.get('url', '')
        title = metadata.get('title', 'Unknown')
        
        # Source type extraction handling
        source_type = metadata.get('source_type', 'PDF')
        if hasattr(source_type, 'value'):
            source_type = source_type.value
            
        page_number = metadata.get('page_number', None)
        chunk_index = metadata.get('chunk_index', None)

        if url not in sources_map:
            sources_map[url] = {
                'title': title,
                'type': str(source_type).upper(),
                'url': url,
                'pages_cited': [],
                'chunk_indices': [],
            }

        # Page numbers safely append
        if page_number is not None:
            try:
                p_num = int(float(str(page_number)))
                if p_num not in sources_map[url]['pages_cited']:
                    sources_map[url]['pages_cited'].append(p_num)
            except (ValueError, TypeError):
                pass

        # Chunk indices safely append
        if chunk_index is not None:
            try:
                c_idx = int(chunk_index)
                if c_idx not in sources_map[url]['chunk_indices']:
                    sources_map[url]['chunk_indices'].append(c_idx)
            except (ValueError, TypeError):
                pass

    # Final sorting
    sources = []
    for source in sources_map.values():
        source['pages_cited'] = sorted(source['pages_cited'])
        source['chunk_indices'] = sorted(source['chunk_indices'])
        sources.append(source)

    return sources

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
        # sources = []
        # seen_urls = set()
        # for chunk in chunks:
        #     url = chunk['metadata'].get('url', '')
        #     if url and url not in seen_urls:
        #         seen_urls.add(url)
        #         sources.append({
        #             'title': chunk['metadata'].get('title', 'Unknown'),
        #             'source_type': chunk['metadata'].get('source_type', 'unknown'),
        #             'url': url,
        #         })
        sources = build_sources(chunks)
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
