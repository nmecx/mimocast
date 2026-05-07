# Xiaomi MiMo 100T Grant — `mimocast` submission

Form: <https://100t.xiaomimimo.com/>
Project: `mimocast`
Repo: `https://github.com/<you>/mimocast`

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

Paste-ready (≈1 700 chars, fits the 2 000-char limit):

```
Project: mimocast — turn any document into a narrated MP4 video deck
         using all three model classes in the MiMo V2.5 family.
Repo:    https://github.com/<you>/mimocast
Stack:   Python 3.11, openai-py (against MiMo's OpenAI-compatible API),
         pydantic v2, typer, rich, pypdf, Pillow, tenacity, ffmpeg.

Core problem
  Producing a narrated explainer video from a paper, blog post or PDF
  used to require stitching three vendors (LLM + image-gen + TTS)
  together with three auth flows, three rate-limit pools, and three
  billing dashboards. MiMo V2.5 ships reasoner, multimodal vision, and
  TTS behind one OpenAI-compatible endpoint. mimocast is a four-agent
  Python orchestrator that turns that single integration into an
  end-to-end content workflow.

Crew / agent flow
  1. Reader      — ingests PDF / URL / Markdown, extracts plain text,
                   auto-detects language (zh/ja/ko/ar fallback en).
  2. Summarizer  — calls MiMo reasoner with a strict JSON schema to
                   produce a 3–8 section outline. Malformed JSON
                   triggers a temperature-0 repair pass instead of
                   failing the run.
  3. Designer    — asks MiMo multimodal for an editorial image prompt
                   per slide, then renders the actual slide PNG with
                   PIL (deterministic, testable, swappable for a real
                   image-gen endpoint later).
  4. Narrator    — sends each section's speaker_notes to MiMo TTS,
                   writes per-slide MP3s; mock mode emits length-correct
                   silent WAVs so Composer timing stays accurate.
  5. Composer    — ffmpeg builds one segment per slide and concatenates
                   them into deck.mp4.

Recoverability
  After every phase the Orchestrator persists RunState to
  ~/.mimocast/<run_id>.json. `mimocast recover <run_id>` resumes from
  the saved phase, so a network blip or an OOM kill never re-pays for
  tokens already spent. tenacity guards every API call with exponential
  backoff (≤3 tries).

Why MiMo V2.5 specifically
  - One OpenAI-compatible base URL covers reasoner + vision + TTS.
  - Strict JSON-schema decoding eliminates the fragile parse layer.
  - Multilingual reasoning means the Indonesian / Chinese / Arabic
    sources we tested produce in-language speaker notes without drift.
  - Token Plan pricing makes long-form deck production economic.
```

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
https://github.com/<you>/mimocast
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
