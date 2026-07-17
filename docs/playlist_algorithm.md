# MoodyDj — Playlist Generation Algorithm Design

Goal: evolve the current pipeline (LLM picks tracks → Spotify search → return first hits)
into a multi-stage **generate → verify → enrich → score → select → sequence** funnel that
produces more relevant, better-ordered playlists.

Core principle: **the LLM proposes from textual memory; everything downstream verifies
against ground truth.** The LLM's music knowledge is second-hand (text about music, not
audio), so its output must always be treated as a candidate list, never a final answer.

---

## Version roadmap

| Version  | Candidate source                                         | What it adds                                      | Trigger / status                                                          |
| -------- | -------------------------------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------- |
| **v0**   | Single LLM call → first Spotify search hit               | — (the current pipeline)                          | Live today. **Ship this first** — deploy blockers only, no algorithm work |
| **v1**   | LLM over-generates; funnel verifies, scores, sequences   | Stages 0–5 below, built via Phases 1–5            | First post-ship improvement pass                                          |
| **v1.5** | v1 + feature-space neighbors of the LLM's verified picks | Content-based candidate expansion (section below) | Cheap add-on once the Phase 4 SQLite exists                               |
| **v2**   | Embedding corpus proposes; LLM curates                   | Retrieval-first / RAG (section below)             | Only if observed failures are "the LLM doesn't know the right tracks"     |
| **v3**   | v2 + user behavior                                       | Feedback / personalization loop (Stage 6)         | After real usage data exists                                              |

Who knows what: the **LLM** understands the _user_ (mood, intent, cultural context) but
its track knowledge is limited to what's famous in text. The **dataset** knows the
_tracks_ (real IDs, real features, long tail included) but understands nothing.
Each version up the ladder shifts more of the candidate-sourcing burden from LLM memory
onto real data, while the LLM keeps the judgment role. Decision of July 2026: ship v0,
then let real bad playlists — not speculation — decide how far up the ladder to climb.

---

## Current pipeline and its weaknesses

```
user_input ──► LLM (15-20 tracks) ──► Spotify /search (first hit) ──► response
```

| #   | Weakness                                                                                  | Where                                             |
| --- | ----------------------------------------------------------------------------------------- | ------------------------------------------------- |
| 1   | First search hit accepted blindly — covers, karaoke, live and 8-bit versions slip through | `request_generated_list` in `spotify_api_comm.py` |
| 2   | Every LLM pick ships — no scoring, filtering, or selection                                | whole pipeline                                    |
| 3   | Playlist order is arbitrary (LLM output order)                                            | whole pipeline                                    |
| 4   | User taste never enters the prompt (`build_taste_context` is commented out)               | `openai_api_comm.py`                              |
| 5   | Searches run sequentially — slow, and no headroom to over-generate                        | `request_generated_list`                          |
| 6   | No quantitative features → no way to honor "danceable", "high energy" etc.                | everywhere                                        |

---

## Target pipeline

```
                    ┌──────────────────────────────────────────────┐
user_input ───────► │ Stage 0  Intent parsing (LLM, structured)    │
/me/top (taste) ──► └──────────────────┬───────────────────────────┘
                                       ▼
                    ┌──────────────────────────────────────────────┐
                    │ Stage 1  Candidate generation (LLM, 40-50    │
                    │          tracks + per-track feature estimates│
                    └──────────────────┬───────────────────────────┘
                                       ▼
                    ┌──────────────────────────────────────────────┐
                    │ Stage 2  Grounding: parallel Spotify search, │
                    │          fuzzy match validation, junk filter │
                    └──────────────────┬───────────────────────────┘
                                       ▼
                    ┌──────────────────────────────────────────────┐
                    │ Stage 3  Feature enrichment:                 │
                    │          SQLite dataset → (optional external │
                    │          API) → LLM estimate fallback        │
                    └──────────────────┬───────────────────────────┘
                                       ▼
                    ┌──────────────────────────────────────────────┐
                    │ Stage 4  Scoring & selection (top K with     │
                    │          diversity constraints)              │
                    └──────────────────┬───────────────────────────┘
                                       ▼
                    ┌──────────────────────────────────────────────┐
                    │ Stage 5  Sequencing (energy arc, BPM         │
                    │          smoothing)                          │
                    └──────────────────┴──────────► response       │
                    └──────────────────────────────────────────────┘
```

---

## Stage 0 — Intent parsing

One structured-output LLM call (can be merged into Stage 1) that converts free text into
a machine-usable intent object driving every later stage:

```python
class PlaylistIntent(BaseModel):
    mood_keywords: list[str]          # "melancholic", "warm", "nocturnal"
    target_energy: float              # 0-1
    target_danceability: float        # 0-1
    target_valence: float             # 0-1
    tempo_range: tuple[int, int]      # BPM window
    energy_arc: Literal['flat', 'ramp_up', 'peak_and_cool', 'wind_down']
    language_or_market: Optional[str] # "greek", "GR"
    era: Optional[str]                # "90s", "modern"
    familiarity: float                # 0 = deep cuts, 1 = hits
```

Why: "rainy Sunday coding" and "Greek summer party" need different _arcs_, _markets_,
and _familiarity_, not just different track picks. Making this explicit lets Stages 4-5
work with numbers instead of vibes.

Key prompt principle: the LLM's knowledge lives in **text-space**. Express targets as
descriptive language in the generation prompt ("strong steady groove, made for dancing"),
not raw floats — the intent object's numbers are for _our_ scoring code, the words are
for the LLM.

## Stage 1 — Candidate generation (over-generate)

- Ask for **40-50 candidates** for a final playlist of ~20. The funnel below discards
  liberally; headroom is what makes discarding possible.
- Extend `TrackRecommendation` with estimated features and a justification:

```python
class TrackRecommendation(BaseModel):
    track_name: str
    artist_name: str
    danceability: float
    energy: float
    valence: float
    tempo_bpm: int
    justification: str    # one line: why this track fits the request
```

The justification forces the model to ground each pick (measurably reduces
hallucinated tracks) and is useful for debugging bad picks.

- **Taste injection:** re-enable `build_taste_context` using `GET /me/top/artists` /
  `/me/top/tracks` (still-available endpoints; `user-top-read` scope already granted).
  Reference artists are the highest-value anchors in text-space.
- Optional second pass with a "adjacent artists / deeper cuts" bias when
  `familiarity` is low, to widen the candidate pool beyond the obvious.

## Stage 2 — Grounding and verification

Replace "take the first hit" in `request_generated_list`:

1. **Parallelize** the searches (`ThreadPoolExecutor`, ~8 workers). Required for 40-50
   candidates to stay fast; also fixes weakness #5.
2. Request `limit=3` (max 10 post-Feb-2026) instead of 1, then pick the best hit by
   **fuzzy match**: normalized string similarity (`difflib.SequenceMatcher` or
   `rapidfuzz`) between requested and returned `track_name`/`artist_name`.
   Reject below ~0.8 similarity — better to lose a candidate than ship a wrong track.
3. **Junk filter** on returned names: drop hits containing "karaoke", "tribute",
   "made famous by", "8-bit", "lullaby version", "sped up" (unless requested).
4. Pass `market` from the intent object (field already exists unused in `SearchQuery`)
   — critical for non-Anglophone requests like Greek music.
5. Keep Spotify's ground-truth metadata for scoring: `popularity`, `explicit`,
   `duration_ms`, release date.

## Stage 3 — Feature enrichment

Layered lookup, first hit wins:

1. **Local SQLite** — slimmed Kaggle "Spotify 1.2M+ Songs" dataset (real
   pre-deprecation Spotify audio features, keyed by Spotify track ID). Free, offline,
   instant. Blind spot: releases after ~2023.
2. **(Optional) external API for cache misses** — see "External APIs" below.
3. **LLM estimates from Stage 1** — always present, so enrichment can never fail;
   just fuzzier numbers.

Record the provenance (`dataset | external | llm_estimate`) per track — useful for
tuning scoring weights later.

## Stage 4 — Scoring and selection

Score every verified candidate against the intent object:

```
score(track) =
    w1 · feature_fit        # 1 - distance(track features, intent targets)
  + w2 · familiarity_fit    # how well Spotify popularity matches intent.familiarity
  + w3 · taste_affinity     # artist/genre overlap with user's /me/top data
  + w4 · era_market_fit     # release date vs intent.era, market match
  - w5 · artist_repeat_penalty   # discourage >2 tracks per artist
```

Start with hand-tuned weights (e.g. 0.4 / 0.2 / 0.2 / 0.1 / 0.1); refine from feedback
later. Select top K greedily with the repeat penalty applied incrementally
(maximal-marginal-relevance style) so the playlist stays diverse.

## Stage 5 — Sequencing

Order the selected K tracks per `intent.energy_arc`:

- Build a target energy curve over positions 1..K (flat / ramp / peak-and-cool / etc.).
- Assign tracks to positions minimizing (energy deviation from curve) +
  (BPM jump between neighbors). A greedy nearest-fit pass is enough at K≈20;
  no need for exact optimization.
- **Fallback when features are mostly LLM-estimated:** one cheap LLM call —
  "order these N confirmed tracks as a DJ set for <mood>, warm-up → peak → cooldown."
  The model is genuinely good at this and it needs no numbers.

## Stage 6 (later) — Feedback loop

The step that makes the system _learn_: record per-user signals (skips and completions
via the Player API the app already has scopes for; explicit 👍/👎 in the UI). Store a
lightweight per-user profile (liked artists/genres, feature centroids of kept vs.
skipped tracks) and inject it into Stage 1's taste context and Stage 4's
`taste_affinity`. This compounds: every playlist improves the next one.

---

## Can external APIs help? Honest assessment

Only **Stage 3** (feature enrichment) benefits from an external API, and only for the
Kaggle dataset's blind spot: **tracks released after ~2023**. For a DJ app users will
ask for current music, so the gap is real but bounded.

| Option                                           | What it gives                                                                                                                | Risk                                                                                                                   |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **ReccoBeats** (`GET /track/:id/audio-features`) | Same feature set, accepts Spotify IDs directly                                                                               | Free community service: undocumented methodology, rate limits, reliability complaints (as recent as Apr 2026). No SLA. |
| **FreqBlog Music API**                           | Spotify-shaped `/v1/audio-features/{id}` drop-in                                                                             | Newer, less community track record                                                                                     |
| **Last.fm API**                                  | Crowd tags ("danceable", "chill"), similar-artist graph — a _different_ signal (human consensus, like the LLM but per-track) | Stable & established, but tags ≠ numeric features; extra mapping work                                                  |

**Recommendation:** the algorithm above works fully without any of them — LLM estimates
cover dataset misses acceptably. If new-release feature accuracy proves to be a real
quality problem, add ReccoBeats strictly as a **cache-filling gap-filler**: called only
on dataset miss, 2-3 s timeout, result cached in SQLite, LLM estimate as fallback.
Hide it behind a single `get_audio_features(track_id)` function so it is one file to
remove or swap. Never put it on the critical path.

The honest ranking of impact: Stage 2 verification and Stage 4 scoring will improve
perceived quality far more than any external features source. Wrong-version tracks and
unordered playlists are what users notice; a 0.7-vs-0.75 danceability error is not.

---

## Implementation phases

| Phase | Scope                                                                       | Files touched                               | Effort       |
| ----- | --------------------------------------------------------------------------- | ------------------------------------------- | ------------ |
| 1     | Parallel search + fuzzy verification + junk filter + `market` param         | `spotify_api_comm.py`                       | small        |
| 2     | Extended schema (features + justification), over-generation, intent parsing | `searchQueryModel.py`, `openai_api_comm.py` | small-medium |
| 3     | Scoring & selection + LLM-sequencer ordering                                | new `ranking.py`                            | medium       |
| 4     | SQLite features dataset + enrichment layer with provenance                  | new `features_db.py`, build script          | medium       |
| 5     | Taste context from `/me/top` wired into Stage 1 and Stage 4                 | `openai_api_comm.py`, `app.py`              | small        |
| 6     | Feedback loop (player signals, per-user profile)                            | new module + frontend work                  | large, later |

---

## v1.5 — Content-based candidate expansion (feature-space nearest neighbors)

A middle rung between v1 and v2: use the Phase-4 SQLite dataset not just to _enrich_
candidates but to _propose_ new ones. It attacks v1's core weakness — the LLM mostly
knows famous tracks — at **zero embedding cost**, because it reuses the numeric audio
features already bundled for Stage 3.

```
Stage 2 output (verified LLM picks, real Spotify IDs)
        │  each pick becomes a seed
        ▼
k-NN query over normalized feature vectors in SQLite  ──►  ~5 neighbors per seed
        │  neighbors are dataset rows: guaranteed real, hallucination impossible
        ▼
merged candidate pool (LLM picks + neighbors, provenance-tagged)
        ▼
Stage 4 scoring + LLM curation as usual   ◄── neighbors NEVER ship unjudged
```

**Build steps, in order:**

1. **Offline, in the dataset build script:** min-max/z-score normalize the ~10 feature
   columns (danceability, energy, valence, tempo, acousticness, instrumentalness,
   speechiness, liveness, loudness) and store the normalized vector per track.
2. **Similarity query:** cosine or euclidean distance over those vectors. At 1.2M rows
   a brute-force scan in SQLite is seconds; pre-filtering (step 4) or an
   `sqlite-vec` index brings it to milliseconds.
3. **Online, after Stage 2:** for each verified pick, fetch its k≈5 nearest neighbors,
   tag them `provenance='neighbor'`, and append to the candidate pool feeding Stage 4.
4. **Constrain the query to fight genre-blindness:** audio features describe how a
   track _sounds physically_, not what it _is culturally_ — a Greek laiko ballad and a
   Nashville country song can have near-identical valence/energy. Mitigate with a
   release-year window (±10y of the seed) and the intent's market/language when the
   dataset has it. The hard rule stays: neighbors go through Stage 4 scoring and the
   LLM curator, which knows "this doesn't belong in a Greek summer playlist" even when
   the numbers agree.
5. **Bonus uses of the same query, nearly free once built:** a "more like this" feature
   in the UI (seed = the clicked track), and neighbor-distance as the BPM/energy
   smoothing signal in Stage 5.

**Why not just build v2?** v1.5 needs no new infrastructure, no embedding run, and no
corpus documents — one afternoon on top of Phase 4. If neighbor expansion plus LLM
curation closes the relevance gap, v2 may never be needed. Its ceiling: seeds come from
the LLM, so if the LLM proposes _nothing_ relevant for a niche request, there is
nothing to expand — that failure mode is exactly the v2 trigger.

---

## v2 target architecture: retrieval-first (embeddings / RAG)

The long-term direction, to be built **after Phases 1–5 are live and real failure modes
are observable**. It inverts the pipeline: instead of the LLM inventing track names that
we then hunt for on Spotify, we retrieve real catalog tracks by semantic similarity and
let the LLM curate.

```
offline:  dataset row ──► text doc ("Uptown Funk — Bruno Mars. Funk, pop.
          Very danceable, high energy, euphoric, 115 BPM, 2014.")
          ──► OpenAI text-embedding-3-small ──► vector stored via sqlite-vec

online:   user_input ──► embed (full sentence, not keywords)
          ──► cosine top ~100 real tracks
          ──► LLM curates & orders the best ~20 (RAG)
          ──► fetch by Spotify ID directly (no name search, no fuzzy matching)
```

**What it structurally solves:**

- **Hallucination** — candidates provably exist; the LLM only selects, never invents.
- **Version matching** — retrieved tracks carry Spotify IDs from the dataset; the
  fuzzy-search path is only needed for the fallback (below).
- **Non-Anglophone / long-tail relevance** — retrieval doesn't depend on how much
  English text was written about a track, only on the corpus document.

**Constraints and costs:**

- Embedding quality = document quality. Feature-values-to-words + genre + era gets
  good mood matching; cultural nuance ("Tarantino soundtrack vibes") still needs the
  LLM curator. Terminology note: this is _embeddings/semantic search_, not "attention" —
  attention is the internal transformer mechanism that produces these representations.
- Embedding cost is trivial (~$1 for all 1.2M tracks at text-embedding-3-small rates).
  Memory is the real constraint on Render free tier (512 MB): truncate embeddings to
  256 dims (natively supported) and/or restrict the corpus to the most popular
  ~200-300k tracks; sqlite-vec queries from disk.
- **Dataset blind spot (post-~2023 releases) remains** — keep LLM free-generation +
  Spotify search + fuzzy verification (Phases 1-2) as the fallback candidate source.
  Nothing built in Phases 1-5 is throwaway: the intent object, features SQLite,
  scoring, and sequencing all carry over unchanged; retrieval only replaces the
  candidate-sourcing stage.

**Decision trigger:** build this when observed failures are "the LLM doesn't know the
right tracks" (thin candidate pools for niche/non-English requests, repeated picks,
hallucinations despite the buffer). If failures are mostly wrong versions or bad
ordering, the Phase 1-3 funnel is the fix and v2 can wait. Try v1.5 first — it is far
cheaper and covers the "LLM only knows the famous tracks" half of the problem; v2 is
for the harder half, where the LLM has no relevant seed to expand from.

---

## Order of work

1. **Ship v0** — deploy blockers only (env-var URLs, import fix, gunicorn +
   requirements, cross-domain cookies, CSRF state param, frontend build errors).
   No algorithm changes before launch.
2. **Post-ship, Phase 1 first**: it fixes the most user-visible failure (wrong track
   versions) with no schema or prompt changes, and the parallelism it adds is a
   prerequisite for over-generation in Phase 2.
3. Phases 2–5 in order, then v1.5 as a small extension of Phase 4.
4. Collect real failure examples throughout — they are the evidence that decides
   whether v2 (and later v3) is worth building.
