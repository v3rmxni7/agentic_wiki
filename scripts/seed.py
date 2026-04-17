# Seeds the knowledge base with a few canonical notes. Run once from the project root.
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.tools import notes as notes_tool


SEEDS = [
    {
        "slug": "transformers",
        "title": "Transformers",
        "tags": ["deep-learning", "architecture"],
        "body": """## Summary
The Transformer is a neural network architecture built entirely around attention, replacing recurrence and convolution for sequence modeling.

## Key Ideas
- Encoder-decoder stack of self-attention + feed-forward layers
- Multi-head attention enables parallel attention subspaces
- Positional encodings inject order since attention is permutation-invariant
- Residual connections + LayerNorm stabilize deep stacks

## Details
Introduced in "Attention Is All You Need" (Vaswani et al., 2017), Transformers dominate modern NLP, vision, and multimodal models. The decoder-only variant underlies modern LLMs.

## Related

## Sources
- Vaswani et al., 2017 - Attention Is All You Need
""",
    },
    {
        "slug": "attention",
        "title": "Attention Mechanism",
        "tags": ["deep-learning", "transformers"],
        "body": """## Summary
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
""",
    },
    {
        "slug": "rlhf",
        "title": "RLHF",
        "tags": ["alignment", "training"],
        "body": """## Summary
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
""",
    },
    {
        "slug": "tokenization",
        "title": "Tokenization",
        "tags": ["nlp", "preprocessing"],
        "body": """## Summary
Tokenization splits raw text into discrete units (tokens) that a model consumes. Modern LLMs use subword tokenization to balance vocabulary size and sequence length.

## Key Ideas
- Word-level: large vocabulary, poor coverage on rare words
- Character-level: small vocabulary, very long sequences
- Subword (BPE, WordPiece, Unigram): learned merges on a training corpus
- Byte-level variants handle any UTF-8 input

## Details
Tokenization choices directly affect compression, context length efficiency, and downstream task performance. Pretraining corpus and target languages shape the learned vocabulary.

## Related

## Sources
- Sennrich et al., 2016 - Neural Machine Translation of Rare Words with Subword Units
""",
    },
]


def main() -> None:
    for s in SEEDS:
        notes_tool.write_note(
            slug=s["slug"],
            title=s["title"],
            body=s["body"],
            tags=s["tags"],
            summary=s["body"].split("## Summary\n", 1)[-1].split("\n\n", 1)[0].strip()[:240],
            validator_passed=True,
            bump_revision=False,
        )
        print(f"seeded: {s['slug']}.md")


if __name__ == "__main__":
    main()
