# The Unofficial Guide — Project 1

> A RAG (Retrieval-Augmented Generation) system that makes Minerva University student-generated knowledge about favorite cafes, restaurants, and study spots across 6 rotation cities searchable and answerable.

---

## Domain

Student-reviewed cafes, restaurants, and study spots across Minerva University's six rotation cities: San Francisco, Seoul, Hyderabad, Berlin, Buenos Aires, and Taipei. This knowledge is valuable because Minerva students arrive in a new city every semester with zero local context — they don't know which cafes have reliable wifi for 6-hour coding sessions, which restaurants serve filling meals for under $5, or which tourist-trap spots to avoid. Official university orientation materials provide generic city guides but never cover the hyper-specific, opinion-based details that actually matter: wifi speed at a specific cafe, whether a kebab shop is worth a 30-minute line, or which night market stalls are student-budget friendly. This information lives in ephemeral Discord messages, WhatsApp groups, and word-of-mouth conversations that disappear when students graduate.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | SF cafe & study spot reviews | Student reviews (.txt) | documents/sf_cafes_study_spots.txt |
| 2 | SF affordable restaurant reviews | Student reviews (.txt) | documents/sf_affordable_restaurants.txt |
| 3 | Berlin cafe & study spot reviews | Student reviews (.txt) | documents/berlin_cafes_study_spots.txt |
| 4 | Berlin affordable restaurant reviews | Student reviews (.txt) | documents/berlin_affordable_restaurants.txt |
| 5 | Seoul cafe & study spot reviews | Student reviews (.txt) | documents/seoul_cafes_study_spots.txt |
| 6 | Seoul restaurant & street food reviews | Student reviews (.txt) | documents/seoul_affordable_restaurants.txt |
| 7 | Taipei cafe & night market reviews | Student reviews (.txt) | documents/taipei_cafes_and_food.txt |
| 8 | Hyderabad cafe & food reviews | Student reviews (.txt) | documents/hyderabad_cafes_and_food.txt |
| 9 | Buenos Aires cafe & food reviews | Student reviews (.txt) | documents/buenos_aires_cafes_and_food.txt |
| 10 | Cross-city wifi & food value comparison | Student survey data (.txt) | documents/cross_city_comparison.txt |
| 11 | New student survival guide (all cities) | Collaborative guide (.txt) | documents/new_student_survival_guide.txt |

---

## Chunking Strategy

**Chunk size:** 400–600 characters (max), with a minimum viable chunk size of 50 characters

**Overlap:** 80 characters (~15-20%)

**Why these choices fit your documents:** The documents are structured as individual venue reviews separated by double-newlines and `---` dividers. Each review block is typically 200-500 characters — a venue name, star rating, 3-6 sentences of opinion, and a student attribution. The chunker splits on these natural boundaries first (paragraph-aware splitting), preserving complete reviews as single chunks. Only when a review exceeds 600 characters does the chunker fall back to character-splitting with 80-character overlap and sentence-boundary preference. This prevents reviews from being split mid-thought while keeping chunks small enough for precise semantic matching. The 80-character overlap ensures venue names carry into subsequent chunks if a long review is split.

**Final chunk count:** 168 chunks across 11 documents (average chunk size: 297 characters)

### Sample Chunks

**Chunk 1** — from `hyderabad_cafes_and_food.txt` (Hyderabad):
> "The Indian Coffee House is a Hyderabad essential. Don't go for wifi or outlets. Go for the ₹30 filter coffee, the dosa for ₹50, and the feeling of sitting in a place with decades of history. Then go to Roastery for your actual study session." — Class of 2026

**Chunk 2** — from `cross_city_comparison.txt` (All Cities):
> "Going from Hyderabad where a full meal is $1 to San Francisco where a sandwich is $15 was the biggest culture shock of my Minerva experience." — M26

**Chunk 3** — from `taipei_cafes_and_food.txt` (Taipei):
> Louisa Coffee (路易莎咖啡, multiple locations — try Zhongxiao or near NTU) Rating: ★★★★★ "Taiwan's answer to Starbucks but actually GOOD for studying. An Americano is NT$65 (~$2 USD), wifi is fast and reliable, outlets at most seats, and they're open until 10-11pm..."

**Chunk 4** — from `seoul_cafes_study_spots.txt` (Seoul):
> "Tom N Toms is my go-to when I don't want to pay for a study cafe. The atmosphere varies by location — Sinchon one is great, Gangnam one is too crowded. Pro tip: the ones near universities (Sinchon, Ewha) are most study-friendly." — Class of 2026

**Chunk 5** — from `berlin_affordable_restaurants.txt` (Berlin):
> Mustafa's Gemüse Kebap (Mehringdamm 32, Kreuzberg) Rating: ★★★★★ "Yes, the line is insane (30-60 minutes on weekends). Yes, it's worth it. The döner kebap here is €6 and it's genuinely the best thing I've ever eaten for under €10..."

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`, running locally (384-dimensional embeddings)

**Production tradeoff reflection:** If deploying this system for real Minerva students at scale, I would weigh several factors in choosing a different embedding model:

- **Context length**: `all-MiniLM-L6-v2` has a 256-token limit, which works for our short review chunks (avg 297 chars ≈ 60-75 tokens) but would struggle with longer documents like full housing guides or syllabi. A model like `all-mpnet-base-v2` (768 tokens) or OpenAI's `text-embedding-3-small` (8191 tokens) would handle more context per chunk.
- **Multilingual support**: Our documents include Korean (삼겹살, 스터디카페), Mandarin (路易莎咖啡, 蚵仔煎), Hindi terms, and German/Spanish venue names. `all-MiniLM-L6-v2` is English-focused and may not embed these terms meaningfully. A multilingual model like `paraphrase-multilingual-MiniLM-L12-v2` would handle cross-language queries better (e.g., searching for "김밥" should find kimbap reviews).
- **Cost vs. latency**: Local models like MiniLM are free and fast (~10ms inference) vs. API-hosted models (OpenAI, Cohere) that offer higher accuracy but add per-request cost ($0.02-0.13 per million tokens) and network latency (~100-500ms).
- **Domain-specific accuracy**: General-purpose models may not handle student slang ("GOAT," "mid," "goated") or niche food terms as well as a fine-tuned model would.

---

## Grounded Generation

**System prompt grounding instruction:**

The system prompt explicitly enforces grounding with these rules:
1. "Answer ONLY using information from the provided source documents below. Do NOT use your general knowledge about these cities, restaurants, or cafes."
2. "If the source documents don't contain enough information to answer the question, say: 'I don't have enough information in my sources to answer that question.'"
3. "When you reference specific information, mention the source document it comes from using the format [Source: filename]."
4. "Do NOT make up restaurant names, prices, ratings, or any details that aren't in the provided sources."

Temperature is set to 0.3 (low) to minimize creative generation and favor factual responses.

**How source attribution is surfaced in the response:**

Source attribution is enforced at two levels:
1. **LLM-level**: The system prompt instructs the model to cite `[Source: filename]` inline whenever it references specific information.
2. **Programmatic**: After generation, the system programmatically extracts and appends a deduplicated list of all source filenames from the retrieved chunks, guaranteeing attribution even if the LLM fails to cite inline.

### Example Response 1 — Grounded with citations

**Query:** "What is the cheapest filling meal a student can get in Hyderabad?"

**Response:** "The cheapest filling meal a student can get in Hyderabad is the street dosa, which costs ₹30-80 ($0.36-0.96) [Source: cross_city_comparison.txt]. Alternatively, students can also get a full meal at local tiffin centers for ₹100 (~$1.20) [Source: hyderabad_cafes_and_food.txt, new_student_survival_guide.txt], which includes unlimited breakfast items such as idli, dosa, vada, and coffee [Source: new_student_survival_guide.txt]."

**Sources:** cross_city_comparison.txt, new_student_survival_guide.txt, hyderabad_cafes_and_food.txt

### Example Response 2 — Grounded with citations

**Query:** "Are there any 24-hour study spots in Seoul?"

**Response:** "Yes, there are 24-hour study spots in Seoul. According to M25, 'The study cafe near our Minerva residence in Mapo-gu was open 24/7 and became my second home.' [Source: seoul_cafes_study_spots.txt]. Additionally, M26 mentions that Café Comma, a Korean study cafe chain, is 'Open 24 hours' [Source: seoul_cafes_study_spots.txt]. These study cafes offer a productive environment with amenities such as free drinks, outlets, and fast wifi."

**Sources:** seoul_cafes_study_spots.txt, cross_city_comparison.txt

### Out-of-scope Query — Refusal Response

**Query:** "What is the best pizza restaurant in New York City?"

**Response:** "I don't have enough information in my sources to answer that question. The provided documents only cover Minerva University student spots in San Francisco, Seoul, Berlin, Taipei, Hyderabad, and Buenos Aires — New York City is not included in these reviews."

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Which cafes in Berlin have the best wifi for long study sessions? | St. Oberholz (100+ Mbps), Five Elephant, Bonanza Coffee. Avoid Einstein Kaffee. | Mentioned Kaschk and Staatsbibliothek as top wifi spots. Did not mention St. Oberholz or Five Elephant despite them being in the documents. | Partially relevant | Partially accurate |
| 2 | What is the cheapest filling meal a student can get in Hyderabad? | Street dosa ₹30-80, tiffin centers ₹100, Hyderabad is cheapest Minerva city. | Correctly identified street dosa (₹30-80), tiffin centers (₹100), and ranked Hyderabad as cheapest. Cited all relevant sources. | Relevant | Accurate |
| 3 | Which SF restaurants are affordable and filling for students? | Señor Sisig ($12), El Farolito ($13), Tu Lan ($10-12), Dumpling Home ($12-20). | Named El Farolito and Señor Sisig but said "no specific quotes" despite them existing. Missed Tu Lan and Dumpling Home entirely. One retrieved chunk lost the restaurant name. | Partially relevant | Partially accurate |
| 4 | Are there any 24-hour study spots in Seoul? | Café Comma (24hr, ₩2,000-3,000/hr), Korean study cafes (스터디카페) 24/7. | Correctly identified Café Comma as 24hr, mentioned study cafes in Mapo-gu, cited pricing and amenities. | Relevant | Accurate |
| 5 | Which places should students avoid eating at in Buenos Aires? | Puerto Madero, Calle Florida, Café Tortoni (overpriced). | Identified Puerto Madero but said "no specific mention of particular restaurants to avoid" — missed the Calle Florida and Café Tortoni warnings that exist in the documents. | Partially relevant | Partially accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:** "Which cafes in Berlin have the best wifi for long study sessions?"

**What the system returned:** The system recommended Kaschk and Staatsbibliothek as top wifi spots, while completely missing St. Oberholz (explicitly rated #2 in the cross-city wifi ranking at 100+ Mbps) and Five Elephant (described as having "strong wifi" with a ★★★★★ rating).

**Root cause (tied to a specific pipeline stage):**

This is a **retrieval failure caused by chunk content mismatch**. The top-ranked retrieved chunk (distance: 0.290) was the "PLACES TO AVOID FOR STUDYING IN BERLIN" list — which is semantically related to "Berlin study spots" but contains the *opposite* of what was asked. The embedding model matched the query's semantic space ("Berlin" + "cafes" + "wifi" + "study") to this chunk because it mentions all those concepts, even though the chunk is about places to *avoid*. Meanwhile, the St. Oberholz reviews (which directly answer the question) were in separate chunks that didn't rank in the top 5, likely because the reviews for St. Oberholz are split across 3 separate chunks (3 different student quotes) and no single chunk contains both "St. Oberholz" and "wifi speed."

The cross-city comparison doc *does* rank St. Oberholz as #2, but that chunk appeared as result #5 and was about Seoul's Café Comma, not Berlin. The Berlin-specific wifi ranking information was in a different chunk of the comparison document.

**What you would change to fix it:** Two approaches could help: (1) **Increase top-k from 5 to 7-8** to capture more chunks, increasing the chance that the St. Oberholz chunk appears in the retrieved set. (2) **Adjust chunking** to keep venue header + all reviews as a single chunk (even if it exceeds 600 chars), so the embedding carries the full semantic context of "St. Oberholz + wifi + fast + 100mbps."

---

## Query Interface

The system uses a **Gradio web UI** (`app.py`) accessible at `http://localhost:7860`.

**Input fields:**
- **Question text box**: Free-text input where users type their question in plain language (e.g., "Which cafes in Berlin have good wifi?")
- **City filter dropdown**: Optional filter to restrict retrieval to a specific city (San Francisco, Seoul, Berlin, Taipei, Hyderabad, Buenos Aires, or "All Cities")

**Output fields:**
- **Answer**: The LLM-generated response with inline source citations
- **Sources**: Deduplicated list of source documents the answer draws from
- **Retrieved Chunks (debug)**: Shows the top-5 retrieved chunks with their distance scores for transparency

**Sample interaction transcript:**

> **User input:** "What are the best night market foods in Taipei?"
> **City filter:** Taipei
>
> **Answer:** "According to student reviews, Shilin Night Market has several must-try items: oyster omelette (蚵仔煎) for NT$60, stinky tofu (臭豆腐) for NT$50, giant fried chicken cutlet (雞排) for NT$70, and bubble tea for NT$40-60 [Source: taipei_cafes_and_food.txt]. Students recommend budgeting NT$200-300 (~$6-9) for a full meal of multiple items. Raohe Night Market is recommended for its legendary pepper buns (NT$60) at the entrance stall [Source: taipei_cafes_and_food.txt]."
>
> **Sources:**
> • taipei_cafes_and_food.txt (Taipei)
> • cross_city_comparison.txt (All Cities)

---

## Spec Reflection

**One way the spec helped you during implementation:**

The chunking strategy section of `planning.md` was critical for making good architectural decisions early. By specifying "paragraph-aware splitting on double-newlines first, then character-splitting oversized blocks" before writing any code, I had a clear target for the chunker implementation. When the AI tool generated a generic `RecursiveCharacterTextSplitter`-based approach, I could immediately identify that it didn't match my spec — my documents have explicit review boundaries (`---` dividers and double newlines) that a character-based splitter would ignore. The spec forced me to implement the double-newline split first, which preserved complete reviews as single chunks in the majority of cases (average 297 chars, well within the 400-600 target).

**One way your implementation diverged from the spec, and why:**

The spec planned for chunks of 400-600 characters, but the actual average chunk size came out to 297 characters — significantly smaller than planned. This happened because the paragraph-aware splitting naturally produced chunks at the review boundaries, and many individual reviews are 150-350 characters. Rather than artificially merging small reviews together (which would combine unrelated venues into one chunk and hurt retrieval precision), I kept the natural review boundaries. The 297-character average still produces meaningful embeddings — each chunk contains a complete venue review with name, rating, and opinion — and the 168 total chunks fall well within the healthy 50-2000 range. The tradeoff is that very short chunks (like a 149-character quote) may not carry enough semantic signal to rank highly in retrieval.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* I provided the full project specification (all 6 milestones from the course instructions), my domain choice (Minerva student spots across 6 cities), and asked it to create an implementation plan with concrete manual steps mapped to rubric points, then generate 11 realistic source documents with student voices, and build the full Python pipeline.
- *What it produced:* A comprehensive implementation plan, 11 text files with realistic student reviews across 6 cities, and 7 Python modules (ingest.py, chunker.py, embedder.py, retriever.py, generator.py, query.py, app.py) plus build.py and evaluate.py.
- *What I changed or overrode:* I reviewed the generated documents to ensure they covered the specific questions I wanted to evaluate (wifi quality, affordable meals, places to avoid). I ran the build pipeline myself and validated the chunk output — the 168 chunks at 297 avg chars were smaller than the spec's 400-600 target, but I accepted this because the natural review boundaries produced more semantically coherent chunks than forced merging would have.

**Instance 2**

- *What I gave the AI:* I shared the planning.md chunking strategy section (paragraph-aware splitting, 400-600 chars, 80 overlap) and the document structure (review blocks separated by `---` and double newlines) and asked it to implement the chunker.
- *What it produced:* A `chunker.py` module that splits on `---` dividers and double-newlines first, then character-splits oversized blocks with sentence-boundary preference and 80-character overlap. It included a `MIN_CHUNK_SIZE` filter of 50 characters and a `print_sample_chunks()` function for validation.
- *What I changed or overrode:* The initial implementation correctly followed my spec's paragraph-aware approach rather than defaulting to a generic fixed-size splitter. I kept the implementation as generated after verifying the sample chunks were self-contained reviews, not fragments. The sentence-boundary splitting for oversized blocks was a good addition I hadn't specified explicitly — it prevents mid-sentence splits when a review exceeds 600 characters.
