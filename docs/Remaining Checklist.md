# Remaining Checklist

## Citation
- [ ] Add page number metadata during PDF ingestion.
- [ ] Carry page number metadata through chunking and storage.
- [ ] Return page number and chunk index in source references.
- [ ] Re-ingest existing documents after citation metadata changes.
- [ ] Test citations against retrieved chunks and source locations.

## Confidence Score
- [ ] Implement internal confidence-score calculation.
- [ ] Calculate retrieval relevance score.
- [ ] Calculate answer grounding score.
- [ ] Calculate answer completeness/length score.
- [ ] Combine components into a weighted confidence score.
- [ ] Log the confidence score internally.
- [ ] Keep the confidence score internal for now; do not expose it in the client response.
- [ ] Validate the scoring approach with representative questions before treating it as an accuracy measure.

## Prompt Caching
- [ ] Keep the current file/template-based prompt approach for the POC.
- [ ] Avoid a database lookup for every request unless production requirements justify it.
- [ ] Add prompt caching if prompts/configuration are moved to a database.
- [ ] Define cache invalidation/TTL for production prompt configuration.
- [ ] Keep developer-controlled base/safety rules separate from client-configurable settings.


## Additional Production Items
- [ ] Payment integration
- [ ] Audit logs
- [ ] Google Drive source integration
- [ ] Local File Implementation