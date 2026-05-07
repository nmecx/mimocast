# Architecture

`mimocast` is a five-phase pipeline driven by a single recoverable
orchestrator. Every phase has exactly one input artifact and one output
artifact; everything that crosses a phase boundary is persisted to disk
so a crash never costs more than the work *inside* the failing phase.

## Phases

| # | Phase     | Agent       | MiMo capability used     | Input            | Output           |
|---|-----------|-------------|--------------------------|------------------|------------------|
| 1 | read      | `Reader`    | —                        | URL / file path  | `Document`       |
| 2 | summarize | `Summarizer`| reasoner (JSON-schema)   | `Document`       | `Outline`        |
| 3 | design    | `Designer`  | multimodal vision        | `Outline`        | `list[Slide]`    |
| 4 | narrate   | `Narrator`  | TTS                      | `Outline`        | `list[AudioClip]`|
| 5 | compose   | `Composer`  | — (ffmpeg)               | slides + audio   | `Deck` (MP4)     |

## State machine

```
   ┌─────────┐   ┌────────────┐   ┌────────┐   ┌─────────┐   ┌─────────┐   ┌──────┐
   │  READ   │──►│ SUMMARIZE  │──►│ DESIGN │──►│ NARRATE │──►│ COMPOSE │──►│ DONE │
   └─────────┘   └────────────┘   └────────┘   └─────────┘   └─────────┘   └──────┘
        ▲              ▲              ▲             ▲             ▲
        │              │              │             │             │
        └──────────────┴──────────────┴─────────────┴─────────────┘
                       resume entry point on `recover`
```

After **every** transition the `Orchestrator` writes the current
`RunState` (with the freshly produced artifact attached) to
`~/.mimocast/<run_id>.json`. `mimocast recover <run_id>` deserialises
that file and re-enters the loop at the saved phase.

## Why three model classes

The MiMo V2.5 family is unusually well-aligned for this kind of
end-to-end content workflow:

* The **reasoner** produces structured JSON outlines reliably under
  strict schema decoding — no fragile regex parsing.
* The **multimodal vision** model handles figure captioning and image
  prompt generation; it lets us substitute real image-gen later without
  changing the agent contract.
* The **TTS** model handles long-form narration with consistent voice
  identity across slides.

A single API key, base URL and rate limit pool simplifies operations
considerably compared to stitching three vendors together.

## Mock mode

When `MIMOCAST_API_KEY` is unset (or `--mock` is passed), `MimoClient`
short-circuits each method:

* `reason()` returns a deterministic three-section outline derived from
  the user prompt header.
* `describe_image()` returns a templated caption.
* `synthesize()` returns a silent WAV whose duration matches what the
  real model would speak (so the Composer step still produces correctly
  timed video segments).

The rest of the pipeline is unchanged. This is what powers the test
suite and the offline demo, and what reviewers can run locally without
spending tokens.

## Failure modes & recovery

| Failure                       | Behaviour                                              |
|------------------------------|--------------------------------------------------------|
| Network blip mid-call        | `tenacity` retries with exponential backoff, ≤3 tries. |
| Malformed JSON from reasoner | `Summarizer` triggers a single repair-pass with `temperature=0`. |
| ffmpeg missing               | Composer logs a warning, returns a `Deck` without `video_path`; slides + audio remain on disk. |
| Crash anywhere               | Last good `RunState` persists; `recover RUN_ID` re-enters at the right phase. |
| Bad source URL               | Reader fails fast before any tokens are spent.         |

## Extension points

The agents are intentionally small and stateless. To swap any of them:

* **Designer**: replace PIL rendering with a real image-gen endpoint
  (DALL·E / Stable Diffusion / MiMo image-gen when available) — keep
  the `image_prompt` field as the contract.
* **Narrator**: switch to a different TTS voice or back-end by changing
  `MIMOCAST_TTS_VOICE` / `MIMOCAST_TTS_MODEL`.
* **Reader**: add `.docx` or `.epub` by extending `_read_path`.
* **Composer**: emit a `.webm` / `.mov` by editing `_make_segment`.
