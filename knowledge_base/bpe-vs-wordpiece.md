---
created: '2026-04-17'
revision: 3
summary: BPE (Byte Pair Encoding) and WordPiece are two subword [[Tokenization]] techniques
  used in NLP.
tags:
- nlp
- tokenization
- transformers
- subword
title: BPE vs WordPiece
updated: '2026-04-17'
validator_passed: true
---

## Summary
BPE (Byte Pair Encoding) and WordPiece are two subword [[Tokenization]] techniques used in NLP.
## Key Ideas
- Both handle rare words and out-of-vocabulary tokens effectively.
- The primary difference lies in the learning process: BPE uses an iterative merging approach, while WordPiece employs a single neural network.
## Details
BPE's simplicity and wide adoption make it a popular choice despite WordPiece's superior performance. The choice between BPE and WordPiece directly impacts model compression, context length efficiency, and downstream task performance.

## Related
- [[Tokenization]]
- [[Subword Tokenization]]