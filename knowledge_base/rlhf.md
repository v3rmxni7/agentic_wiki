---
created: '2026-04-17'
revision: 0
summary: Reinforcement Learning from Human Feedback (RLHF) is a three-stage training
  recipe that aligns language models with human preferences.
tags:
- alignment
- training
title: RLHF
updated: '2026-04-17'
validator_passed: true
---

## Summary
Reinforcement Learning from Human Feedback (RLHF) is a three-stage training recipe that aligns language models with human preferences.

## Key Ideas
- Stage 1: supervised fine-tuning on demonstrations
- Stage 2: train a reward model from pairwise preference data
- Stage 3: optimize policy against the reward model with an RL algorithm
- KL penalty to a reference policy prevents reward hacking

## Details
Popularized by InstructGPT (Ouyang et al., 2022), RLHF is the standard post-training step in most production LLMs. Common RL algorithms used in stage 3 include PPO and, more recently, DPO-style direct preference methods.

## Related

## Sources
- Ouyang et al., 2022 - Training language models to follow instructions with human feedback