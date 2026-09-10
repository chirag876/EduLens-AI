# Generic — exceptions.py mein use hoti hai
EXCEPTION_TOKEN_INVALID = 'Invalid access token'
EXCEPTION_UNAUTHORIZED_ACCESS = 'Unauthorized access'
EXCEPTION_FORBIDDEN_ACCESS = 'Insufficient permissions'

# EduLens specific
EXCEPTION_PDF_INGESTION_FAILED = 'Failed to process PDF content'
EXCEPTION_VIDEO_INGESTION_FAILED = 'Failed to process video content'
EXCEPTION_EMBEDDING_FAILED = 'Failed to generate embeddings'
EXCEPTION_RETRIEVAL_FAILED = 'Failed to retrieve relevant content'
EXCEPTION_LLM_GENERATION_FAILED = 'Failed to generate answer'
EXCEPTION_SAFETY_CHECK_FAILED = 'Content did not pass safety check'
EXCEPTION_CONTENT_NOT_FOUND = 'No relevant content found for your question'
EXCEPTION_INVALID_GRADE_LEVEL = 'Invalid grade level provided'
EXCEPTION_USERNAME_PASSWORD_INVALID = 'Incorrect username or password'