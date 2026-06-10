"""
The Unofficial Guide — Minerva Student Spots
Gradio-powered query interface for the RAG system.

Run: python app.py
Open: http://localhost:7860
"""

import gradio as gr
from query import ask


def handle_query(question: str, city_filter: str) -> tuple[str, str, str]:
    """
    Process a user query and return the answer, sources, and retrieved chunks.
    """
    if not question.strip():
        return "Please enter a question.", "", ""

    # Map the dropdown value
    filter_val = None if city_filter == "All Cities" else city_filter

    try:
        result = ask(question, top_k=5, city_filter=filter_val)
    except Exception as e:
        return f"Error: {str(e)}", "", ""

    # Format the answer
    answer = result["answer"]

    # Format sources
    sources = "\n".join(f"• {s}" for s in result["sources"])

    # Format retrieved chunks for transparency
    chunks_text = ""
    for i, chunk in enumerate(result["retrieved_chunks"], 1):
        dist = chunk["distance"]
        chunks_text += f"[{i}] (score: {dist:.3f}) {chunk['source']}\n"
        chunks_text += f"    {chunk['text'][:150]}...\n\n"

    return answer, sources, chunks_text


# Build the Gradio interface
with gr.Blocks(
    title="The Unofficial Guide — Minerva Student Spots",
    theme=gr.themes.Soft(),
    css="""
    .main-title { text-align: center; margin-bottom: 0; }
    .subtitle { text-align: center; color: #666; margin-top: 0; }
    """
) as demo:

    gr.Markdown(
        "# 🗺️ The Unofficial Guide",
        elem_classes="main-title"
    )
    gr.Markdown(
        "*Minerva student-reviewed cafes, restaurants & study spots across 6 cities*",
        elem_classes="subtitle"
    )

    with gr.Row():
        with gr.Column(scale=4):
            question_input = gr.Textbox(
                label="Ask a question",
                placeholder="e.g., Which cafes in Berlin have good wifi for studying?",
                lines=2,
                elem_id="question-input",
            )
        with gr.Column(scale=1):
            city_dropdown = gr.Dropdown(
                label="Filter by city",
                choices=[
                    "All Cities",
                    "San Francisco",
                    "Seoul",
                    "Berlin",
                    "Taipei",
                    "Hyderabad",
                    "Buenos Aires",
                ],
                value="All Cities",
                elem_id="city-filter",
            )

    ask_btn = gr.Button("🔍 Ask", variant="primary", elem_id="ask-button")

    answer_output = gr.Textbox(
        label="Answer",
        lines=10,
        elem_id="answer-output",
    )

    with gr.Row():
        sources_output = gr.Textbox(
            label="📎 Sources",
            lines=4,
            elem_id="sources-output",
        )
        chunks_output = gr.Textbox(
            label="🔍 Retrieved Chunks (debug)",
            lines=4,
            elem_id="chunks-output",
        )

    # Example questions
    gr.Examples(
        examples=[
            ["Which cafes in Berlin have the best wifi for long study sessions?", "All Cities"],
            ["What is the cheapest filling meal in Hyderabad?", "Hyderabad"],
            ["Which San Francisco restaurants are affordable and filling?", "San Francisco"],
            ["Are there any 24-hour study spots in Seoul?", "Seoul"],
            ["Which places should students avoid in Buenos Aires?", "Buenos Aires"],
            ["What are the best night market foods in Taipei?", "Taipei"],
        ],
        inputs=[question_input, city_dropdown],
    )

    # Wire up events
    ask_btn.click(
        handle_query,
        inputs=[question_input, city_dropdown],
        outputs=[answer_output, sources_output, chunks_output],
    )
    question_input.submit(
        handle_query,
        inputs=[question_input, city_dropdown],
        outputs=[answer_output, sources_output, chunks_output],
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
