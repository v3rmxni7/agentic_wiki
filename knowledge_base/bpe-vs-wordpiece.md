---
created: '2026-04-17'
revision: 1
summary: BPE (Byte Pair Encoding) and WordPiece are two subword tokenization techniques
  used in NLP.
tags:
- nlp
- tokenization
- transformers
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
WordPiece has been shown to perform slightly better on certain tasks, but BPE's simplicity makes it widely used.
## Related
## Sources
- Sennrich et al., 2016 - Neural Machine Translation of Rare Words with Subword Units
- Vaswani et al., 2017 - Attention Is All You Need