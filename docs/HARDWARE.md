# Local model sizing

The delivery machine reports Windows x64, an Intel Core i7-1355U, 12 logical processors and approximately 14 GiB of visible memory. GPU capacity was not verified. Docker and Ollama were not available through the inspected local installations/commands.

The full-stack configuration proposes `qwen2.5:1.5b` for conservative excerpt selection and `nomic-embed-text` for 768-dimensional embeddings. These were selected to keep a CPU-only laptop review plausible; no measured latency or quality result is claimed on this machine. Budget several gigabytes for the model runtime and additional memory for Supabase containers, Node/Metro, Python and the browser. Leave headroom for Windows; stop unrelated applications and monitor actual memory before increasing model size.

Start with:

```text
ollama pull nomic-embed-text
ollama pull qwen2.5:1.5b
```

If responses are slow, reduce concurrent requests or use the configured HTTPS compatible chat endpoint. Model credentials remain backend-only. The current compatible adapter changes only chat generation; swapping embeddings requires an `EmbeddingProvider` implementation, matching dimensions and complete re-indexing. Native Azure/Gemini/Anthropic adapters are extension points, not installed integrations.

The portable demo uses deterministic lexical embeddings and exact excerpts, explicitly labeled in the app. It is not a benchmark for Ollama or a semantic-retrieval acceptance result.
