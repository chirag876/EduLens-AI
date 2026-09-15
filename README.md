

```
EduLens-AI
├─ .flake8
├─ .isort.cfg
├─ .pylintrc
├─ app
│  ├─ main.py
│  └─ server
│     ├─ config
│     │  ├─ config.py
│     │  └─ __init__.py
│     ├─ database
│     │  ├─ core_data.py
│     │  ├─ db.py
│     │  └─ __init__.py
│     ├─ embeddings
│     │  ├─ embedder.py
│     │  └─ __init__.py
│     ├─ encoder
│     │  ├─ json_encoder.py
│     │  └─ __init__.py
│     ├─ handler
│     │  ├─ error_handler.py
│     │  └─ __init__.py
│     ├─ http_client
│     │  ├─ http_client.py
│     │  └─ __init__.py
│     ├─ ingestion
│     │  ├─ pdf_ingestion.py
│     │  ├─ video_ingestion.py
│     │  └─ __init__.py
│     ├─ llm
│     │  ├─ generator.py
│     │  └─ __init__.py
│     ├─ logger
│     │  ├─ audit_logs.py
│     │  ├─ custom_logger.py
│     │  └─ __init__.py
│     ├─ middlewares
│     │  ├─ exceptions.py
│     │  ├─ headers.py
│     │  └─ request_gzip.py
│     ├─ models
│     │  ├─ ingestion_model.py
│     │  ├─ query_model.py
│     │  └─ __init__.py
│     ├─ personalization
│     │  ├─ personalizer.py
│     │  └─ __init__.py
│     ├─ processing
│     │  ├─ chunker.py
│     │  ├─ cleaner.py
│     │  └─ __init__.py
│     ├─ retrieval
│     │  ├─ retriever.py
│     │  └─ __init__.py
│     ├─ routes
│     │  ├─ ingestion.py
│     │  ├─ query.py
│     │  └─ __init__.py
│     ├─ safety
│     │  ├─ moderator.py
│     │  └─ __init__.py
│     ├─ services
│     │  └─ __init__.py
│     ├─ static
│     │  ├─ collections.py
│     │  ├─ constants.py
│     │  ├─ enums.py
│     │  ├─ error_identifier.py
│     │  ├─ localization.py
│     │  ├─ projections.py
│     │  └─ __init__.py
│     ├─ templates
│     │  ├─ system_prompt.txt
│     │  └─ __init__.py
│     ├─ utils
│     │  ├─ crypto_utils.py
│     │  ├─ date_utils.py
│     │  ├─ file_utils.py
│     │  ├─ json_utils.py
│     │  ├─ math_utils.py
│     │  ├─ password_utils.py
│     │  ├─ query_utils.py
│     │  ├─ token_util.py
│     │  └─ __init__.py
│     └─ vendor
│        └─ __init__.py
├─ check_chroma.py
├─ docs
│  ├─ Add_Source_Type.txt
│  ├─ Educational_AI_POC_End_to_End_Project_Documentation.docx
│  ├─ Educational_AI_POC_Flow_Architecture.png
│  ├─ Educational_AI_POC_Recommended_Tech_Stack_Costing.docx
│  ├─ Educational_AI_POC_Requirement_Document.docx
│  ├─ EduLens AI Dashboard Showcase.png
│  ├─ EduLens AI Platform UI Showcase.png
│  ├─ EduLens AI User Journeys and System Flow.png
│  ├─ Next Implementation.md
│  ├─ Production architecture.md
│  ├─ RAG_Ingestion_Architecture.pdf
│  └─ Remaining Checklist.md
├─ generate_requirements.py
├─ logs
├─ mypy.ini
├─ pyproject.toml
├─ README.md
├─ requirements.txt
└─ temp_videos

```