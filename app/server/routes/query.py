from typing import Any

from fastapi import APIRouter

from app.server.llm.generator import generate_answer
from app.server.models.query_model import QueryRequest, QueryResponse
from app.server.personalization.personalizer import personalize_response
from app.server.retrieval.retriever import retrieve_relevant_chunks
from app.server.safety.moderator import moderate_answer

router = APIRouter()


@router.post('/query', summary='Ask a question based on the curriculum', response_model=QueryResponse)
async def query_route(params: QueryRequest) -> dict[str, Any]:
    # Step 1: Retrieve relevant chunks from ChromaDB
    chunks = retrieve_relevant_chunks(
        question=params.question,
        source_type=params.source_type,
    )

    # Step 2: Generate answer using Groq LLM
    generated = generate_answer(
        question=params.question,
        chunks=chunks,
        grade_level=params.grade_level,
    )

    # Step 3: Moderate the answer
    moderated = moderate_answer(
        answer=generated['answer'],
        chunks=chunks,
    )

    # Step 4: Personalize and structure final response
    final_response = personalize_response(
        answer=moderated['final_answer'],
        sources=generated['sources'],
        grade_level=params.grade_level,
    )

    return final_response