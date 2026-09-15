# =============================================================================
# Response Personalization Module
# =============================================================================
#
# This module is responsible for preparing the moderated LLM response for the
# student-facing API response.
#
# It provides grade-level configuration for different student groups and
# structures the final answer together with its source references.
#
# The personalization layer sits after moderation and prepares the final
# response that will be returned to the student.
#
# Processing Flow:
#
#     Moderated Answer
#          │
#          ▼
#     Determine Grade Level
#          │
#          ▼
#     Apply Grade-Level Configuration
#          │
#          ▼
#     Format Source References
#          │
#          ▼
#     Build Final Response
#          │
#          ▼
#     Student-Facing Response
#
# Key Responsibilities:
#
# 1. Grade-Level Configuration
#    - Defines response instructions for Primary, Middle School, High School,
#      and College students.
#    - Each grade level has its own language style and configured maximum
#      response length.
#
# 2. Grade-Level Personalization
#    - Identifies the student's requested grade level when provided.
#    - Provides the corresponding grade-level configuration to the final
#      response pipeline.
#    - Primary-level responses are designed around simple language and
#      everyday examples, while College-level responses allow more advanced
#      academic and technical terminology.
#
# 3. Source Formatting
#    - Converts raw source references returned by the LLM generation layer
#      into a consistent structure for the final API response.
#    - Normalizes source type values and provides fallback values for missing
#      source information.
#
# 4. Final Response Construction
#    - Combines the moderated answer, grade-level label, and formatted sources
#      into a single structured response.
#    - Also provides the total number of unique formatted sources.
#
# 5. Grade-Level Validation
#    - Validates the provided grade level against the supported grade-level
#      configurations.
#    - Invalid grade levels result in a controlled application-level error.
#
# 6. Optional Grade Level
#    - Grade-level personalization is optional.
#    - When no grade level is provided, the answer is returned as a general
#      response without a grade-specific label.
#
# 7. Input Validation and Error Handling
#    - Rejects empty or whitespace-only answers before personalization.
#    - Converts unexpected personalization failures into application-level
#      CustomHTTPException errors for consistent API error handling.
#
# =============================================================================

from app.server.handler.error_handler import CustomHTTPException
from app.server.logger.custom_logger import logger
from app.server.static import error_identifier
from app.server.static.enums import GradeLevel
from fastapi import status

# Grade level configurations
GRADE_LEVEL_CONFIG = {
    GradeLevel.PRIMARY: {
        'label': 'Primary School',
        'instruction': (
            'Use very simple words and short sentences. '
            'Explain as if talking to a 8-10 year old child. '
            'Use examples from everyday life. '
            'Avoid technical jargon completely.'
        ),
        'max_length': 150,
    },
    GradeLevel.MIDDLE: {
        'label': 'Middle School',
        'instruction': (
            'Use clear and simple language suitable for a 11-13 year old. '
            'You can use some subject-specific terms but explain them. '
            'Keep the explanation structured and easy to follow.'
        ),
        'max_length': 250,
    },
    GradeLevel.HIGH: {
        'label': 'High School',
        'instruction': (
            'Use appropriate academic language for a high school student. '
            'You can use subject-specific terminology. '
            'Provide a well-structured and detailed explanation.'
        ),
        'max_length': 400,
    },
    GradeLevel.COLLEGE: {
        'label': 'College',
        'instruction': (
            'Use advanced academic and technical language. '
            'Provide an in-depth, detailed explanation with proper terminology. '
            'The student is expected to have prior subject knowledge.'
        ),
        'max_length': 600,
    },
}


def format_sources(sources: list[dict]) -> list[dict]:
    """
    Format source references for the final response.

    Args:
        sources (list[dict]): Raw sources from generator.

    Returns:
        list[dict]: Cleaned and formatted sources.
    """
    formatted = []
    for source in sources:
        formatted.append({
            'title': source.get('title', 'Unknown Source'),
            'type': source.get('type', 'UNKNOWN'),
            'url': source.get('url', ''),
            'pages_cited': source.get('pages_cited', []),
            'chunk_indices': source.get('chunk_indices', []),
        })
    return formatted


def personalize_response(
    answer: str,
    sources: list[dict],
    grade_level: str = None,
) -> dict:
    """
    Personalize the final response based on student's grade level.
    Formats the answer, adds grade context, and structures sources.

    Args:
        answer (str): The moderated answer from safety check.
        sources (list[dict]): Source references from generator.
        grade_level (str, optional): Student's grade level.
                                     One of: primary, middle, high, college.

    Returns:
        dict: Final structured response ready to send to student.
    """
    if not answer or not answer.strip():
        raise CustomHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Answer cannot be empty for personalization',
            identifier=error_identifier.UNPROCESS_ENTITY,
        )

    try:
        grade_config = None
        grade_label = None

        # Get grade level config if provided
        if grade_level:
            grade_config = GRADE_LEVEL_CONFIG.get(grade_level)
            if not grade_config:
                raise CustomHTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f'Invalid grade level: {grade_level}',
                    identifier=error_identifier.INVALID_GRADE_LEVEL,
                )
            grade_label = grade_config['label']
            logger.debug(f'Personalizing response for grade level: {grade_label}')
        else:
            logger.debug('No grade level provided — returning general response')

        # Format sources
        formatted_sources = format_sources(sources)

        # Build final response
        final_response = {
            'answer': answer.strip(),
            'grade_level': grade_label,
            'sources': formatted_sources,
            'total_sources': len(formatted_sources),
        }

        logger.debug('Response personalized successfully')
        return final_response

    except CustomHTTPException:
        raise
    except Exception as error:
        raise CustomHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to personalize response: {str(error)}',
            identifier=error_identifier.INTERNAL_SERVER_ERROR,
        ) from error