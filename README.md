# The Unofficial Guide — Project 1

> A RAG (Retrieval-Augmented Generation) system that makes Minerva University student-generated knowledge about cafes, restaurants, and study spots searchable and answerable.

---

## Domain

Minerva students drop into a new city every semester totally blind. They don't know which cafes won't kick them out after four hours, where to get dinner for under $5, or which highly-rated spots are actually just tourist traps. The official university orientation materials give you the standard city guide. They don't tell you if the wifi at that cute cafe drops every ten minutes, or if that famous kebab shop is actually worth standing in the rain for. 

Right now, this survival knowledge lives in Discord servers, buried WhatsApp threads, and word-of-mouth. When a class graduates, it vanishes. I built this to fix that.

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

**Chunk size:** 400–600 characters (max), with a minimum viable chunk size of 50 characters.

**Overlap:** 80 characters (~15-20%).

**Why I chunked it this way:** 
I structured the documents as individual venue reviews separated by double-newlines or `---` dividers. Most reviews are short—200 to 500 characters covering the venue name, a star rating, a few sentences of strong opinion, and who said it. 

The chunker respects these boundaries. It splits on paragraphs first, so complete reviews stay together. It only resorts to character-splitting (with an 80-character overlap) if a review pushes past 600 characters. I wanted to avoid chopping a student's rant in half while keeping the chunks tight enough that the retrieval actually works. The overlap catches the venue name if a long review gets cut.

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

**Production tradeoff reflection:** 
If I were actually deploying this for the whole student body, `all-MiniLM-L6-v2` probably wouldn't cut it. Here's what I'd worry about:

- **Context length**: MiniLM taps out at 256 tokens. That's fine for our short 300-character chunks, but the second someone tries to index a massive housing contract or a syllabus, it breaks. I'd likely switch to `all-mpnet-base-v2` or just bite the bullet and use OpenAI's `text-embedding-3-small`.
- **Languages**: The reviews are littered with Korean (스터디카페), Mandarin (蚵仔煎), Hindi, German, and Spanish. MiniLM is aggressively English-focused. If someone searches for "김밥", I doubt it maps properly to kimbap reviews. We'd absolutely need a multilingual model like `paraphrase-multilingual-MiniLM-L12-v2`.
- **Cost vs. latency**: Running MiniLM locally is free and basically instant. Hitting the OpenAI or Cohere APIs means network latency and paying per token. That adds up if hundreds of students are spamming queries during finals week.
- **Slang**: Standard models don't really know what to do with terms like "GOAT" or "mid". A fine-tuned model would handle Minerva's weird mix of academic speak and Gen Z slang much better.

---

## Grounded Generation

**How I forced the model to stick to the facts:**

I gave the system prompt a few hard rules. Mostly: "Answer ONLY using information from the provided source documents. Do NOT use your general knowledge." I don't want it hallucinating a fake coffee shop in Seoul just because it sounds plausible.

I also turned the temperature down to 0.3. I don't need the model to be creative; I need it to be accurate.

**How source attribution actually works:**

I attacked citations from two sides:
1. **The prompt**: I told the LLM to cite its sources inline, like `[Source: filename]`.
2. **The code**: I don't trust the LLM to always remember that. My Python script grabs the filenames from the retrieved chunks and slaps a deduplicated list at the bottom of the response. Even if the model gets lazy, the user still sees where the info came from.

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

**Where it all went wrong:**

I asked: "Which cafes in Berlin have the best wifi for long study sessions?"

The system confidently gave me Kaschk and the Staatsbibliothek. It entirely ignored St. Oberholz (which my docs literally list as the #2 wifi spot across all cities) and Five Elephant.

**Why did this happen?** 

It's a classic retrieval failure. The embedding model grabbed the chunk labeled "PLACES TO AVOID FOR STUDYING IN BERLIN" and ranked it #1. Why? Because semantically, it's a perfect match for "Berlin", "cafes", "wifi", and "study." The math doesn't understand that "avoid" flips the meaning of the entire block.

Worse, the actual good reviews for St. Oberholz got buried. Because multiple students reviewed it, those quotes got split into three separate chunks. None of those individual chunks contained both "St. Oberholz" and enough keywords about "wifi speed" to beat the "avoid" list in the similarity search.

**How to fix it:**
1. **Crank up top-k.** If I grab the top 8 chunks instead of the top 5, St. Oberholz probably sneaks in.
2. **Change the chunking rules.** I should probably force the chunker to keep a venue's header and all its reviews bundled together, even if it blows past the 600-character limit. That way, the embedding sees the whole picture.

---

## Query Interface

The system uses a **Gradio web UI** (`app.py`) accessible at `http://localhost:7860`.

**Input fields:**
- **Question text box**: Free-text input where users type their question in plain language (e.g., "Which cafes in Berlin have good wifi?")
- **City filter dropdown**: Optional filter to restrict retrieval to a specific city.

**Output fields:**
- **Answer**: The LLM-generated response with inline source citations.
- **Sources**: Deduplicated list of source documents the answer draws from.
- **Retrieved Chunks (debug)**: Shows the top-5 retrieved chunks with their distance scores so I can actually see why the model answered the way it did.

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

**Did the spec actually help?**

Yeah, the chunking strategy section saved me a lot of pain. I decided early on to split on paragraphs and double-newlines first, and only fall back to character splitting if things got too long. When I initially had Claude write the chunker, it tried to use LangChain's generic `RecursiveCharacterTextSplitter`. Because I had my spec, I immediately knew that was wrong—it would have blindly sliced through my `---` dividers and broken up student quotes. I forced the AI to rewrite it to respect the double-newlines. As a result, almost every chunk is a clean, isolated review.

**Where I threw the spec out:**

I planned for chunks of 400 to 600 characters. My actual average ended up being 297. Why? Because most student reviews are just a couple of sentences. Once the paragraph-aware splitter did its job, the chunks were naturally short. I could have written code to artificially stitch them together to hit the 400-character mark, but that would mean mashing a review of a Seoul study cafe together with a review of a KBBQ spot. That ruins retrieval precision. So I let the chunks be small. The tradeoff is that occasionally a really short quote doesn't have enough keywords to get retrieved, but it's better than retrieving Frankenstein chunks.

---

## AI Usage

**Instance 1: The heavy lifting**

I fed Claude the entire project spec and my domain idea (Minerva cafes across the six cities). I basically asked it to bootstrap the whole thing: write the implementation plan, generate the 11 text files full of fake student reviews, and write the Python pipeline.

It gave me exactly that. The Python files were surprisingly clean. I didn't blindly accept the text files, though. I read through them to make sure they actually contained the answers to my five evaluation questions (like the specific wifi speeds and the cheap dosa spots). I also had to make the call to accept the smaller 297-character chunks instead of fighting the AI to hit the 500-character target, because the natural boundaries just made more sense.

**Instance 2: The chunker fight**

I handed Claude my specific chunking strategy from the planning doc (paragraph-aware, 400-600 chars, 80-char overlap) and told it to write `chunker.py`.

It originally wanted to use a generic text splitter. I pushed back, and it eventually gave me a script that respects the `---` dividers and double newlines. It actually added a nice touch I didn't ask for: when a block *does* exceed 600 characters, it tries to split on a period or question mark instead of just aggressively cutting mid-word. I kept that.
