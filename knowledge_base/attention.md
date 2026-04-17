---
created: '2026-04-17'
revision: 0
summary: Attention is a mechanism that lets a model weight different parts of its
  input by learned relevance, producing context-dependent representations.
tags:
- deep-learning
- transformers
title: Attention Mechanism
updated: '2026-04-17'
validator_passed: true
---

## Summary
Attention is a mechanism that lets a model weight different parts of its input by learned relevance, producing context-dependent representations.

## Key Ideas
- Scaled dot-product: softmax(QK^T / sqrt(d_k)) V
- Query, Key, Value projections are learned linear maps
- Softmax over keys gives a probability distribution used to weight values
- Self-attention = Q, K, V all come from the same sequence

## Details
Attention replaced recurrence in sequence models by allowing each position to access all other positions in O(1) path length, enabling long-range dependency modeling.

## Related

## Sources
- Bahdanau et al., 2014 - Neural Machine Translation by Jointly Learning to Align and Translate
- [[KV Cache]]