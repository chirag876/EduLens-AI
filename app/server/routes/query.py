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

# Current Response
# {
#   "answer": "**Photosynthesis** is the process by which green plants, algae, and some bacteria turn sunlight into chemical energy. It happens in two main stages:\n\n1. **Light‑dependent reactions**  \n   * Occur in the thylakoid membranes of chloroplasts.  \n   * A photon hits the antenna pigments of photosystem II, exciting electrons that travel through an electron‑transport chain.  \n   * This chain pumps hydrogen ions into the thylakoid interior, creating a high‑concentration gradient.  \n   * The gradient drives ATP synthase to produce ATP, and the electrons ultimately reduce NADP⁺ to NADPH.  \n   * Oxygen is released as a waste product when water is split to replace the lost electrons.\n\n2. **Calvin cycle (light‑independent reactions)**  \n   * Takes place in the stroma of the chloroplast.  \n   * Uses the ATP and NADPH produced above to fix carbon dioxide (CO₂) into a stable, energy‑rich molecule, glyceraldehyde‑3‑phosphate (G3P).  \n   * G3P can be converted into glucose, sucrose, or other carbohydrates, which store the energy captured from the sun.\n\n**Overall,** photosynthesis uses solar energy, CO₂, and water to produce carbohydrates (high‑energy sugars) and releases oxygen. The basic chemical equation is:\n\n\\[\n6\\,\\text{CO}_2 + 6\\,\\text{H}_2\\text{O} + \\text{light energy} \\;\\longrightarrow\\; C_6H_{12}O_6 + 6\\,\\text{O}_2\n\\]\n\nThis process is essential for life on Earth because it supplies the energy and organic molecules that all organisms need.",
#   "grade_level": "High School",
#   "sources": [
#     {
#       "title": "OpenStax Biology 2e",
#       "type": "PDF",
#       "url": "https://assets.openstax.org/oscms-prodcms/media/documents/Biology-2e_-_WEB.pdf?_gl=1*1wwfh03*_gcl_au*ODM1MTQwMDk1LjE3ODkwOTczMDYuLS4tLjE3ODkwOTczMDYuMTYxNTg2MDc1MS4xNzg5MDk3MzA2LjE3ODkwOTc1MDE.*_ga*NDYwMzc2NjY0LjE3ODkwOTczMDc.*_ga_T746F8B0QC*czE3ODkwOTczMDYkbzEkZzEkdDE3ODkwOTc1MDEkajE0JGwwJGgxMjU3OTkzNzY2"
#     }
#   ],
#   "total_sources": 1
# }
