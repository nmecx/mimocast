# Xiaomi MiMo 100T Grant — `mimocast` submission

Form: <https://100t.xiaomimimo.com/>
Project: `mimocast`
Repo: `https://github.com/nmecx/mimocast`

---

## 01 · Your email

`<your-github-linked-email@example.com>`

> Use the email tied to your GitHub *and* your Xiaomi MiMo platform
> account. If they're not bound yet, do it at <https://id.mi.com> before
> submitting (FAQ 04 / 09).

---

## 02 · Which agent tool do you use most?

**Windsurf** *(Cascade is built into Windsurf)*

> Pick whichever agent tool actually drove development. Reviewers cross-
> reference this against your commit messages.

---

## 03 · Primary model series you use

**MiMo**

> Listed first because the project is *designed* around MiMo V2.5's
> three-model footprint (reasoner + multimodal + TTS). Fallback Claude /
> GPT only via litellm shims when the user has no MiMo key.

---

## 04 · Describe what you've built

Form constraint: **≤1 200 chars**, ≥100 words. Both drafts below pass.

### A. ASCII-safe (1 196 chars / 1 196 UTF-8 bytes — recommended; works whether the form counts chars or bytes)

```
Project: mimocast -- github.com/nmecx/mimocast (MIT)

Problem: Producing a narrated explainer video from a paper or PDF used to mean stitching three vendors (LLM + image-gen + TTS) with three auth flows, rate-limit pools, dashboards. MiMo V2.5 ships reasoner, multimodal vision, and TTS behind one OpenAI-compatible endpoint -- mimocast turns that into one recoverable agent workflow.

Logic flow -- 5-phase multi-agent crew under a single orchestrator:

1. Reader: PDF/URL/Markdown -> text; detects zh/ja/ko/ar.
2. Summarizer: MiMo reasoner + strict JSON-schema decoding produces a 3-8 section outline; malformed JSON triggers a temperature-0 repair pass instead of crashing.
3. Designer: MiMo multimodal generates editorial prompts; renders 1920x1080 slides.
4. Narrator: MiMo TTS voices each section's speaker_notes per slide.
5. Composer: ffmpeg stitches segments into deck.mp4.

After every phase RunState persists to ~/.mimocast/<run_id>.json; `mimocast recover <run_id>` resumes from the last good phase, so a crash never re-pays for tokens already spent. tenacity guards every call (<=3 retries, exp backoff). Pydantic v2 enforces typed cross-phase contracts. 14 pytest cases, ruff clean.
```

### B. Typographic (1 199 chars / 1 212 UTF-8 bytes — only safe if the form counts chars/codepoints, not bytes)

```
Project: mimocast — github.com/nmecx/mimocast (MIT)

Problem: Producing a narrated explainer video from a paper or PDF used to mean stitching three vendors (LLM + image-gen + TTS) with three auth flows, rate-limit pools, billing dashboards. MiMo V2.5 ships reasoner, multimodal vision, and TTS behind one OpenAI-compatible endpoint — mimocast turns that into one recoverable agent workflow.

Logic flow — 5-phase multi-agent crew under a single orchestrator:

1. Reader: PDF/URL/Markdown → text; detects zh/ja/ko/ar.
2. Summarizer: MiMo reasoner + strict JSON-schema decoding produces a 3–8 section outline; malformed JSON triggers a temperature-0 repair pass instead of crashing.
3. Designer: MiMo multimodal generates editorial prompts; renders 1920×1080 slides.
4. Narrator: MiMo TTS voices each section's speaker_notes per slide.
5. Composer: ffmpeg stitches segments into deck.mp4.

After every phase RunState persists to ~/.mimocast/<run_id>.json; `mimocast recover <run_id>` resumes from the last good phase, so a crash never re-pays for tokens already spent. tenacity guards every call (≤3 retries, exp backoff). Pydantic v2 enforces typed cross-phase contracts. 14 pytest cases, ruff clean.
```

> **Why both?** Most web forms count `string.length` (UTF-16 code units),
> in which case both drafts fit. A few forms count UTF-8 bytes — in
> which case **only Draft A** fits. Paste A first; only switch to B if
> the form's counter shows ≥1 200 with A (it shouldn't).

---

## 05 · Proof of usage & impact

Upload **all** of these (the form takes up to 5 files, ≤ 20 MB each):

### A. AI-platform billing screenshot (last 30 days)

* MiMo platform dashboard at
  <https://platform.xiaomimimo.com/> showing token spend tagged to this
  project.

### B. Terminal recording — end-to-end run

```bash
asciinema rec mimocast-demo.cast \
  -c "mimocast run examples/sample_doc.md --mock --dry-run --max-sections 4"
```

Convert + upload:

```bash
agg mimocast-demo.cast mimocast-demo.gif
ffmpeg -i mimocast-demo.gif mimocast-demo.mp4
```

### C. Sample deck artefact

The `out/<run_id>/` directory after a real run contains:

```
out/<run_id>/
├── slides/        slide_01.png … slide_NN.png       (1920×1080)
├── audio/         narration_01.mp3 … narration_NN.mp3
└── video/         deck.mp4                          (≤ 20 MB, ≈ 60–90 s)
```

Attach `deck.mp4` directly — reviewers love seeing the *output* of the
pipeline, not just the source code.

> ⚠️ **Be honest about provenance.** If you generated the demo MP4 with
> `--demo-tts` (gTTS substitute) instead of a real `MIMOCAST_API_KEY`,
> say so in the file name and caption: e.g. `deck-demo-gtts.mp4`. The
> grant evaluates real MiMo usage; mislabeling demo-mode artefacts as
> MiMo output undermines the submission.

### D. State-recovery proof

Screenshot a `~/.mimocast/<run_id>.json` before-and-after a kill,
showing `phase` advancing across resumed runs. This demonstrates the
"never lose tokens to wrapper crashes" claim concretely.

### E. Cost / impact one-pager

A small spreadsheet:

| Run | Source                    | Sections | Tokens (reasoner) | TTS chars | Wall-clock |
|-----|---------------------------|---------:|------------------:|----------:|-----------:|
| 001 | Attention paper PDF       | 6        | ~3 800            | ~2 200    | 41 s       |
| 002 | Indonesian blog post (ID) | 5        | ~3 100            | ~1 900    | 38 s       |
| 003 | Chinese tech doc (ZH)     | 6        | ~4 200            | ~2 400    | 44 s       |

---

## 06 · GitHub project link or live demo URL

```
https://github.com/nmecx/mimocast
```

* Pin the repo on your profile.
* Top-of-README demo GIF (15 s, autoplay).
* Add a tagged `v0.1.0` release with the demo `deck.mp4` attached as a
  release asset — reviewers can download it without leaving GitHub.

---

## Pre-submit checklist

- [ ] Email is bound to the Xiaomi ID at <https://id.mi.com>
- [ ] Repo is **public** and ships `LICENSE` (MIT)
- [ ] `pytest -q` passes locally with no API key (mock mode)
- [ ] At least one **live** run logged with real MiMo V2.5 spend
- [ ] `mimocast-demo.cast` (or .mp4) recorded with end-to-end output
- [ ] Spend screenshot from the last 30 days included
- [ ] `deck.mp4` sample attached (≤ 20 MB)
- [ ] Submitted before the 2026-05-28 00:00 Beijing-time deadline
