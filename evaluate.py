"""
Evaluation Script
Runs all 5 test questions from planning.md, records results,
and outputs an evaluation report.

Usage: python evaluate.py
"""

import json
from query import ask


EVAL_QUESTIONS = [
    {
        "id": 1,
        "question": "Which cafes in Berlin have the best wifi for long study sessions?",
        "expected": (
            "St. Oberholz (100+ Mbps, outlets everywhere, mentioned as 'unofficial Minerva campus') "
            "and Five Elephant in Kreuzberg (strong wifi, good outlets). "
            "Bonanza Coffee also good but slower wifi. Avoid Einstein Kaffee and Balzac."
        ),
    },
    {
        "id": 2,
        "question": "What is the cheapest filling meal a student can get in Hyderabad?",
        "expected": (
            "Street dosa at Ram Ki Bandi for ₹80 (~$0.96), idli/dosa/vada at tiffin centers "
            "for ₹30-50, or breakfast at local joints for ₹100 (~$1.20) unlimited. "
            "Hyderabad is the cheapest Minerva city for food."
        ),
    },
    {
        "id": 3,
        "question": "Which San Francisco restaurants are affordable and filling for students on a budget?",
        "expected": (
            "Señor Sisig (Filipino-Mexican burritos, ~$12, massive portions), "
            "El Farolito (super burrito $13, open until 3am), "
            "Tu Lan (Vietnamese plates $10-12, huge portions), "
            "and Dumpling Home (soup dumplings $12-20 for a full meal)."
        ),
    },
    {
        "id": 4,
        "question": "Are there any 24-hour study spots in Seoul?",
        "expected": (
            "Yes — Café Comma is open 24 hours with unlimited coffee included for "
            "₩2,000-3,000/hour (~$1.50-2.25). Korean study cafes (스터디카페) are also "
            "24/7 in many locations with private booths, outlets, and free drinks."
        ),
    },
    {
        "id": 5,
        "question": "Which places should students avoid eating at in Buenos Aires?",
        "expected": (
            "Avoid Puerto Madero (tourist trap, 3x normal prices) and restaurants on "
            "Calle Florida (designed for tourists, terrible value). "
            "Café Tortoni is overpriced for the food quality."
        ),
    },
]


def run_evaluation():
    """Run all evaluation questions and print results."""
    print("=" * 70)
    print("  📊 Evaluation Report — The Unofficial Guide")
    print("=" * 70)

    results = []

    for eq in EVAL_QUESTIONS:
        print(f"\n{'─' * 70}")
        print(f"  Question {eq['id']}: {eq['question']}")
        print(f"{'─' * 70}")

        # Run the query
        result = ask(eq["question"])

        print(f"\n  📝 Expected Answer:")
        print(f"     {eq['expected']}")

        print(f"\n  💬 System Response:")
        print(f"     {result['answer'][:500]}...")

        print(f"\n  📎 Sources: {', '.join(result['sources'])}")

        print(f"\n  🔍 Retrieved Chunks:")
        for i, chunk in enumerate(result["retrieved_chunks"], 1):
            print(f"     [{i}] dist={chunk['distance']:.4f} | {chunk['source']}")
            print(f"         {chunk['text'][:120]}...")

        # Store for report
        results.append({
            "id": eq["id"],
            "question": eq["question"],
            "expected": eq["expected"],
            "response": result["answer"],
            "sources": result["sources"],
            "chunks": [
                {
                    "source": c["source"],
                    "distance": c["distance"],
                    "preview": c["text"][:200],
                }
                for c in result["retrieved_chunks"]
            ],
        })

    # Save results to JSON for README reference
    with open("evaluation_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n\n✅ Results saved to evaluation_results.json")

    print("\n" + "=" * 70)
    print("  Evaluation complete. Review results above and add accuracy")
    print("  judgments (accurate/partially accurate/inaccurate) to README.md")
    print("=" * 70)


if __name__ == "__main__":
    run_evaluation()
