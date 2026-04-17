---
created: '2026-04-17'
revision: 1
summary: The Transformer is a neural network architecture built entirely around attention,
  replacing recurrence and convolution for sequence modeling.
tags:
- deep-learning
- architecture
title: Transformers
updated: '2026-04-17'
validator_passed: true
---

## Summary
The Transformer is a neural network architecture built entirely around Attention Mechanism, replacing recurrence and convolution for sequence modeling.

## Key Ideas
- Encoder-decoder stack of self-attention + feed-forward layers
- Multi-head attention enables parallel attention subspaces
- Positional encodings inject order since attention is permutation-invariant
- Residual connections + LayerNorm stabilize deep stacks

## Details
Introduced in "Attention Is All You Need" (Vaswani et al., 2017), Transformers dominate modern NLP, vision, and multimodal models. The decoder-only variant underlies modern LLMs.

## Related

- [BPE vs WordPiece](bpe-vs-wordpiece)
- [[PPO Explanation]]
- [[Subword Tokenization]]
- [[Tokenization]]