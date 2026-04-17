---
created: '2026-04-17'
revision: 2
summary: Subword tokenization is a technique used in NLP to split raw text into discrete
  units (tokens) that a model consumes.
tags:
- nlp
- tokenization
- subword
title: Subword Tokenization
updated: '2026-04-17'
validator_passed: true
---

## Summary
Subword tokenization is a technique used in NLP to split raw text into discrete units (tokens) that a model consumes.
## Key Ideas
- Word-level: large vocabulary, poor coverage on rare words
- Character-level: small vocabulary, very long sequences
- Subword: learned merges on a [[Transformers]] training corpus
## Details
Subword tokenization choices directly affect compression, context length efficiency, and downstream task performance. Pretraining corpus and target languages shape the learned vocabulary.
## Related
- [[BPE vs WordPiece]]
- [[Tokenization]]
- [[Transformers]]