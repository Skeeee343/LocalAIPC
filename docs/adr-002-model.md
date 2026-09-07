# ADR-002 — Local model under P2000 5GB, 4-core, no CPU offload

Status: approved. Date: 2026-09-06. Revised 2026-09-07 (context 4K → 8K, timeout 60s → 300s).

## Constraint (from user)

Fit fully in P2000 VRAM at 4K context with runtime overhead. No CPU-offload assumption (4-core host). Priority: (1) fits, (2) reliable tool calls / low hallucination on dates+recurrence, (3) doesn't blow context on short chore commands.

## Decision (approved)

Default: `qwen3:4b` (2.5GB Ollama tag), 4K context, thinking off, 1 inference at a time.
Runners-up: `qwen2.5:3b` (1.9GB) or `llama3.2:3b` (2.0GB) if tool JSON is flaky.

Duck.ai Gemma 4 claim falsified against Ollama registry 2026-09-06:
`gemma4:e2b` = 7.2GB, `gemma4:e4b` = 9.6GB default tags (262K vocab: E2B 5.1B /
E4B 8B total w/ embeddings). Weights-alone spill 5GB P2000 — disqualified as
default. E2B/E4B Q4 2.9/4.5GB figures were weights-only, not install size.
Custom GGUF + embedding-quant could be re-benched only with `nvidia-smi` proof.

## Verify-before-lock candidates (all fit fully, 4K ctx, no offload)

- Qwen3-4B (non-thinking) — best tool-accuracy-per-VRAM, top agent scores
- Qwen2.5-3B-Instruct (1.9GB) — strong JSON structured output, resilient prompts
- Llama-3.2-3B-Instruct (2.0GB) — Meta claims beats Gemma-2-2.6B + Phi-3.5-mini on tool use, max OpenClaw compat
- Phi-3.5-mini 3.8B (2.2GB) — good reasoning/param, English-only, weaker tool eco; 3rd place
- Gemma-3-4B (3.3GB) / Gemma-2-2B (1.6GB) — no tools badge, multimodal overhead; skip for tool workload
- Sub-2B (qwen2.5:1.5b, gemma3:1b, llama3.2:1b) — fallback only, date hallucination jumps
- Phi-4-mini 3.8B (~2.3GB GGUF) — bench-only, no official Ollama tag

## Acceptance test (30–50 commands)

Every-X-days create, completion-anchor reset ("cleaned oven today, +90d"), Tuesday-weekly vs interval confusion, duplicate prevention, today/overdue summary, malformed-date rejection. Adapter validates everything (ADR-004) so model only needs correct structured calls. Pick highest tool-accuracy-per-VRAM, not highest MMLU.

# ponytail: 4K context cap + adapter-side date math, raise context only if VRAM headroom measured, not assumed.

## Revision 2026-09-07 (live evidence, supersedes 4K cap)

Agent system prompt alone is ~5–10k tokens (`context-pressure-diagnostic:
estimatedPromptTokens=10704` vs `promptBudgetBeforeReserve=2048`), so 4K
starved the agent: `embedded run timeout` at 60s, Discord "typing..."
forever. Fix in `openclaw.json.j2`: `contextTokens`/`num_ctx` 4096 → 8192,
`agents.defaults.timeoutSeconds` 60 → 300. Baseline pre-change
(`free`/`nvidia-smi`/`ollama ps`): RAM 3.0/30Gi, GPU 99% mid-inference,
VRAM 3115/5120MiB, `qwen3:4b` 100% GPU ctx 4096 — 8K expected ~+1GB, fits.
Re-measure after converge; 16K only with `nvidia-smi` proof.
