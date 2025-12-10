import os
import gradio as gr
import logging
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from research_manager import ResearchManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deep_research.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv(override=True)

CUSTOM_CSS = """
:root {
    --win-bg: #f3f3f3;
    --win-panel: #ffffff;
    --win-stroke: #dfe3e8;
    --win-text: #0f172a;
    --win-muted: #4b5563;
    --win-accent: #2563eb;
    --win-accent-2: #1f3c88;
}
@media (prefers-color-scheme: dark) {
    :root {
        --win-bg: #0f1115;
        --win-panel: #15181e;
        --win-stroke: #1f2937;
        --win-text: #e5e7eb;
        --win-muted: #9ca3af;
        --win-accent: #3b82f6;
        --win-accent-2: #60a5fa;
    }
}

body, .gradio-container {
    background: var(--win-bg);
    color: var(--win-text);
}

.app-shell {
    max-width: 1100px;
    margin: 0 auto;
    gap: 12px;
}
.app-shell .gr-block, .app-shell .gr-box, .app-shell .gr-panel, .app-shell .gr-group {
    background: var(--win-panel);
    border: 1px solid var(--win-stroke);
    border-radius: 12px;
}
.app-shell .gr-button {
    border-radius: 8px;
}
.app-shell input, .app-shell textarea {
    border-radius: 8px;
}
.app-shell h1, .app-shell h2, .app-shell h3, .app-shell h4 {
    color: var(--win-text);
}
.app-shell p, .app-shell li {
    color: var(--win-text);
}

.save-row {
    justify-content: flex-start;
    gap: 8px;
}
.save-btn {
    flex: 0 0 auto !important;
    width: auto !important;
}
.save-btn button {
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 600;
    background: linear-gradient(135deg, var(--win-accent-2), var(--win-accent));
    color: #ffffff;
    box-shadow: 0 8px 20px rgba(31, 60, 136, 0.18);
    transition: transform 120ms ease, box-shadow 120ms ease, opacity 120ms ease;
}
.save-btn button:hover {
    transform: translateY(-1px);
    box-shadow: 0 10px 24px rgba(31, 60, 136, 0.22);
    opacity: 0.96;
}
.save-btn button:active {
    transform: translateY(0);
    box-shadow: 0 6px 16px rgba(31, 60, 136, 0.16);
}

.run-btn {
    width: fit-content !important;
    margin: 6px 0 14px;
}
.run-btn button {
    background: linear-gradient(135deg, #16a34a, #15803d);
    color: #ffffff;
    border-radius: 10px;
    padding: 8px 18px;
    font-weight: 700;
    font-size: 14px;
    box-shadow: 0 8px 18px rgba(21, 128, 61, 0.18);
    transition: transform 120ms ease, box-shadow 120ms ease, opacity 120ms ease;
}
.run-btn button:hover {
    transform: translateY(-1px);
    box-shadow: 0 10px 22px rgba(21, 128, 61, 0.22);
    opacity: 0.97;
}
.run-btn button:active {
    transform: translateY(0);
    box-shadow: 0 6px 14px rgba(21, 128, 61, 0.16);
}

.download-card {
    background: transparent !important;
    border: 1px dashed var(--win-stroke) !important;
    border-radius: 10px !important;
    padding: 6px 10px !important;
    box-shadow: none !important;
    min-height: auto !important;
}
.download-card .container,
.download-card .wrap,
.download-card .file-preview {
    min-height: auto !important;
    padding: 0 !important;
}
.download-card .upload-text {
    color: var(--win-muted);
    font-size: 12px;
}
.download-card .file-preview {
    border: none !important;
}
"""


async def run(query: str):
    logger.info(f"Starting research for query: {query}")
    status_text = ""
    report_text = "*Report will appear here once research begins...*"
    report_store = ""
    
    # Initialize with empty status
    yield status_text, report_text, report_store
    
    try:
        async for chunk in ResearchManager().run(query):
            if not chunk or not chunk.strip():
                continue
            
            # More precise report detection - only consider it a report if:
            # 1. It starts with "# Report" (exact match)
            # 2. OR it's long and has section-like markers
            is_report = False
            chunk_stripped = chunk.strip()
            has_report_heading = chunk_stripped.startswith("# Report") or "# Report" in chunk
            has_sections = chunk.count("## ") >= 2 or chunk.count("### ") >= 2
            is_long_form = len(chunk_stripped) > 1200 or chunk.count("\n") >= 15
            
            if has_report_heading:
                is_report = True
            elif is_long_form and (has_sections or "**Query:**" in chunk or "## Findings" in chunk):
                is_report = True
            
            if is_report:
                # This is the report - replace the report content
                report_text = chunk
                report_store = chunk
                yield status_text, report_text, report_store
            else:
                # This is a status update - append to status
                status_text += chunk
                # Always yield both status and report to update UI
                yield status_text, report_text, report_store
    except Exception as e:
        logger.error(f"Error in run function: {str(e)}", exc_info=True)
        error_msg = f"**Error:** {str(e)}\n\nPlease check the logs for more details."
        yield status_text + "\n\n" + error_msg, report_text, report_store


def save_report(report_markdown: str):
    """Save the current report markdown to a temporary .md file and return its path for download."""
    try:
        if not report_markdown or report_markdown.strip() == "*Report will appear here once research begins...*":
            return None
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".md", prefix="deep_research_report_")
        tmp_path = Path(tmp_file.name)
        tmp_file.close()
        tmp_path.write_text(report_markdown, encoding="utf-8")
        return str(tmp_path)
    except Exception as e:
        logger.error(f"Failed to save report: {e}", exc_info=True)
        return None


with gr.Blocks(css=CUSTOM_CSS) as ui:
    with gr.Column(elem_classes=["app-shell"]):
        gr.Markdown("# Deep Research")
        query_textbox = gr.Textbox(label="What topic would you like to research?")
        run_button = gr.Button("Run", variant="primary", elem_classes=["run-btn"])
        report_state = gr.State("")
        
        with gr.Row():
            with gr.Column(scale=1):
                status = gr.Markdown(label="Status", value="**Ready to research**\n\nEnter a query and click Run to begin.")
            with gr.Column(scale=2):
                report = gr.Markdown(label="Report", value="*Report will appear here once research begins...*")
        
        with gr.Row(elem_classes=["save-row"]):
            save_button = gr.Button("Save report", variant="secondary", elem_classes=["save-btn"], scale=0, min_width=0)
            saved_file = gr.File(label="Download report", interactive=False, file_count="single", scale=2, elem_classes=["download-card"])
    
    run_button.click(fn=run, inputs=query_textbox, outputs=[status, report, report_state])
    query_textbox.submit(fn=run, inputs=query_textbox, outputs=[status, report, report_state])
    save_button.click(fn=save_report, inputs=report_state, outputs=saved_file)

ui.launch(
    server_name="0.0.0.0",
    server_port=int(os.getenv("PORT", 7860)),
    share=False,
    inbrowser=False,
)

