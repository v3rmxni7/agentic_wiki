---
created: '2026-04-17'
revision: 3
summary: Tokenization splits raw text into discrete units (tokens) that a model consumes.
  Modern LLMs use [[Subword Tokenization]] to balance vocabulary size and sequence
  length.
tags:
- nlp
- preprocessing
- tokenization
- subword
title: Tokenization
updated: '2026-04-17'
validator_passed: true
---

## Summary
Tokenization splits raw text into discrete units (tokens) that a model consumes. Modern LLMs use [[Subword Tokenization]] to balance vocabulary size and sequence length.

## Key Ideas
- Word-level: large vocabulary, poor coverage on rare words
- Character-level: small vocabulary, very long sequences
- [[Subword]] (such as [[BPE vs WordPiece|BPE]] and [[WordPiece|WordPiece]]), [[Unigram]],  kv-cache: learned merges on a training corpus
- Byte-level variants handle any UTF-8 input

## Details
Tokenization choices directly affect compression, context length efficiency, and downstream task performance. Pretraining corpus and target languages shape the learned vocabulary.

## Related

- [[Subword Tokenization]]
- [[BPE vs WordPiece]]
- [[Transformers]]