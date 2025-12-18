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
/* Light mode variables */
:root {
    --win-bg: #ffffff;
    --win-panel: #f8f9fa;
    --win-stroke: #dee2e6;
    --win-text: #212529;
    --win-muted: #6c757d;
    --win-accent: #3b82f6;
    --win-accent-2: #60a5fa;
}

/* Dark mode variables - only apply when dark mode is detected */
@media (prefers-color-scheme: dark) {
    :root {
        --win-bg: #0b1017;
        --win-panel: #121824;
        --win-stroke: #1f2937;
        --win-text: #e7ecf3;
        --win-muted: #a7b3c2;
        --win-accent: #3b82f6;
        --win-accent-2: #60a5fa;
    }
}

/* Force dark mode if .dark class is present */
.dark,
.dark :root {
    --win-bg: #0b1017 !important;
    --win-panel: #121824 !important;
    --win-stroke: #1f2937 !important;
    --win-text: #e7ecf3 !important;
    --win-muted: #a7b3c2 !important;
}

body, .gradio-container {
    background: var(--win-bg);
    color: var(--win-text);
}

.app-shell {
    max-width: 1100px;
    margin: 0 auto;
    gap: 12px;
    padding: 4px 0 18px;
}
.app-shell .gr-block, .app-shell .gr-box, .app-shell .gr-panel, .app-shell .gr-group {
    background: var(--win-panel);
    border: 1px solid var(--win-stroke);
    border-radius: 12px;
}
.app-shell .gr-button {
    border-radius: 8px;
}
.app-shell input, 
.app-shell textarea,
.app-shell .gr-textbox,
.app-shell .gr-textbox input,
.app-shell .gr-textbox textarea,
.app-shell .gr-textbox textarea,
.gradio-container .gr-textbox input,
.gradio-container .gr-textbox textarea,
.gradio-container input[type="text"],
.gradio-container textarea {
    border-radius: 8px;
    background: var(--win-panel) !important;
    color: var(--win-text) !important;
    border-color: var(--win-stroke) !important;
    caret-color: var(--win-accent) !important;
    overflow: hidden !important;
    resize: none !important;
}
.app-shell .gr-textbox textarea,
.gradio-container .gr-textbox textarea,
.gradio-container textarea {
    scrollbar-width: none !important; /* Firefox */
    -ms-overflow-style: none !important; /* IE and Edge */
}
.app-shell .gr-textbox textarea::-webkit-scrollbar,
.gradio-container .gr-textbox textarea::-webkit-scrollbar,
.gradio-container textarea::-webkit-scrollbar {
    display: none !important; /* Chrome, Safari, Opera */
}
.app-shell input:focus,
.app-shell textarea:focus,
.app-shell .gr-textbox input:focus,
.app-shell .gr-textbox textarea:focus,
.gradio-container .gr-textbox input:focus,
.gradio-container .gr-textbox textarea:focus {
    border-color: var(--win-accent);
}
.app-shell h1, .app-shell h2, .app-shell h3, .app-shell h4 {
    color: var(--win-text);
}
.app-shell p, .app-shell li, .app-shell span, .app-shell label {
    color: var(--win-text);
}
.app-shell .gr-markdown {
    background: transparent;
    color: var(--win-text);
}
.app-shell .gr-markdown p,
.app-shell .gr-markdown h1,
.app-shell .gr-markdown h2,
.app-shell .gr-markdown h3,
.app-shell .gr-markdown h4,
.app-shell .gr-markdown li,
.app-shell .gr-markdown ul,
.app-shell .gr-markdown ol {
    color: var(--win-text);
}
/* Fix markdown display areas (report, status) */
.app-shell .gr-box .gr-markdown,
.gradio-container .gr-box .gr-markdown,
.gradio-container .markdown-body,
.app-shell .markdown-body {
    background: var(--win-panel);
    color: var(--win-text);
}
.app-shell .gr-box,
.gradio-container .gr-box {
    background: var(--win-panel);
    color: var(--win-text);
}
.gradio-container ::placeholder {
    color: var(--win-muted);
    opacity: 0.7;
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
.run-btn button,
.run-btn button.primary,
.run-btn .gr-button,
.run-btn .gr-button.primary,
button.run-btn,
button.run-btn.primary {
    background: linear-gradient(135deg, #16a34a, #15803d) !important;
    background-color: #16a34a !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 8px 18px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    box-shadow: 0 8px 18px rgba(21, 128, 61, 0.18) !important;
    transition: transform 120ms ease, box-shadow 120ms ease, opacity 120ms ease;
}
.run-btn button:hover,
.run-btn button.primary:hover,
.run-btn .gr-button:hover,
.run-btn .gr-button.primary:hover,
button.run-btn:hover,
button.run-btn.primary:hover {
    background: linear-gradient(135deg, #15803d, #16a34a) !important;
    background-color: #15803d !important;
    transform: translateY(-1px);
    box-shadow: 0 10px 22px rgba(21, 128, 61, 0.22) !important;
    opacity: 0.97;
}
.run-btn button:active,
.run-btn button.primary:active,
.run-btn .gr-button:active,
.run-btn .gr-button.primary:active,
button.run-btn:active,
button.run-btn.primary:active {
    background: linear-gradient(135deg, #15803d, #16a34a) !important;
    background-color: #15803d !important;
    transform: translateY(0);
    box-shadow: 0 6px 14px rgba(21, 128, 61, 0.16) !important;
}
/* Override any Gradio primary button styles with maximum specificity */
.gradio-container .run-btn button,
.gradio-container .run-btn .gr-button,
.gradio-container .run-btn button.primary,
.gradio-container .run-btn .gr-button.primary,
.gradio-container .run-btn button[class*="primary"],
.gradio-container .run-btn .gr-button[class*="primary"],
div.run-btn button,
div.run-btn .gr-button {
    background: linear-gradient(135deg, #16a34a, #15803d) !important;
    background-color: #16a34a !important;
    background-image: linear-gradient(135deg, #16a34a, #15803d) !important;
}
/* Ensure hover states are also green */
.gradio-container .run-btn button:hover,
.gradio-container .run-btn .gr-button:hover,
.gradio-container .run-btn button.primary:hover,
.gradio-container .run-btn .gr-button.primary:hover {
    background: linear-gradient(135deg, #15803d, #16a34a) !important;
    background-color: #15803d !important;
    background-image: linear-gradient(135deg, #15803d, #16a34a) !important;
}

.download-card {
    background: transparent !important;
    border: 1px dashed var(--win-stroke) !important;
    border-radius: 10px !important;
    padding: 6px 10px !important;
    box-shadow: none !important;
    min-height: auto !important;
    max-width: 320px !important;
    width: 100% !important;
}
.download-card .container,
.download-card .wrap,
.download-card .file-preview {
    min-height: auto !important;
    height: auto !important;
    padding: 0 !important;
}
.download-card .upload-text {
    color: var(--win-muted) !important;
    font-size: 12px;
}
.download-card .file-preview {
    border: none !important;
    height: auto !important;
    min-height: 32px !important;
}
.download-card * {
    color: var(--win-muted) !important;
}

/* Fix for file components */
.gradio-container .gr-file {
    background: var(--win-panel) !important;
    border-color: var(--win-stroke) !important;
}
.gradio-container .gr-file * {
    color: var(--win-text) !important;
}

.description-text {
    font-size: 14px !important;
    color: var(--win-muted) !important;
    margin-top: 4px !important;
    margin-bottom: 20px !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    padding: 0 !important;
    line-height: 1.6 !important;
    display: block !important;
    width: 100% !important;
    overflow: visible !important;
    min-height: auto !important;
    max-height: none !important;
}
.description-text p,
.description-text .markdown,
.description-text .markdown p {
    margin: 0 !important;
    padding: 0 !important;
    font-size: 14px !important;
    color: var(--win-muted) !important;
    line-height: 1.6 !important;
    overflow: visible !important;
    white-space: normal !important;
}

.header-row {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    gap: 12px !important;
    margin-bottom: 8px !important;
    width: 100% !important;
}
.header-image {
    width: auto !important;
    min-width: 48px !important;
    height: 48px !important;
    flex: 0 0 auto !important;
    display: flex !important;
    align-items: center !important;
    visibility: visible !important;
    opacity: 1 !important;
    margin-left: auto !important;
}
.header-image img,
.header-image .gr-image,
.header-image .gr-image img,
.header-image .gr-image-wrapper img,
.header-image [class*="image"] img {
    height: 48px !important;
    width: auto !important;
    min-width: 48px !important;
    object-fit: contain !important;
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    max-width: 100% !important;
}
/* Hide image controls and options but keep image visible */
.header-image .gr-image-controls,
.header-image button:not([class*="image"]),
.header-image .download-button,
.header-image .share-button,
.header-image [class*="button"]:not([class*="image"]) {
    display: none !important;
}
.header-image .gr-image-wrapper,
.header-image .gr-image {
    pointer-events: none !important;
    cursor: default !important;
    display: block !important;
    visibility: visible !important;
}
/* Ensure the entire image component is visible */
.header-image,
.header-image * {
    max-height: 48px !important;
}
.header-image > * {
    display: block !important;
    visibility: visible !important;
}
/* Make sure Gradio doesn't hide it */
.gradio-container .header-image,
.gradio-container .header-image * {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
}
.header-title {
    flex: 1 1 auto !important;
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
}
.header-title h1,
.header-title .markdown h1,
.header-title .markdown {
    color: var(--win-text) !important;
    margin: 0 !important;
    padding: 0 !important;
    display: inline !important;
}

/* Gradio components - respect theme */
.gradio-container {
    background: var(--win-bg);
}
.gradio-container .panel,
.gradio-container .panel-heading,
.gradio-container .panel-body,
.gradio-container .form,
.gradio-container .form-group {
    background: var(--win-panel);
    color: var(--win-text);
}
.gradio-container .input-group input,
.gradio-container .input-group textarea {
    background: var(--win-panel);
    color: var(--win-text);
    border-color: var(--win-stroke);
}
.gradio-container .gr-box {
    background: var(--win-panel);
    border-color: var(--win-stroke);
    color: var(--win-text);
}
.gradio-container .gr-form {
    background: transparent;
}
.gradio-container button.secondary {
    background: var(--win-panel);
    color: var(--win-text);
    border-color: var(--win-stroke);
}
.gradio-container button.secondary:hover {
    background: var(--win-stroke);
}
/* Text inputs - respect theme */
.gradio-container input,
.gradio-container textarea,
.gradio-container .gr-textbox input,
.gradio-container .gr-textbox textarea {
    background: var(--win-panel);
    color: var(--win-text);
    border-color: var(--win-stroke);
}
/* Markdown/content areas - respect theme */
.gradio-container .gr-box,
.gradio-container .gr-markdown,
.gradio-container .markdown-body {
    background: var(--win-panel);
    color: var(--win-text);
}
.gradio-container ::placeholder {
    color: var(--win-muted);
    opacity: 0.7;
}

/* Checkbox styling - standard checkbox */
.app-shell .gr-checkbox,
.gradio-container .gr-checkbox {
    background: var(--win-panel) !important;
    border: 1px solid var(--win-stroke) !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
}

.app-shell .gr-checkbox label,
.gradio-container .gr-checkbox label {
    color: var(--win-text) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    cursor: pointer !important;
}

.app-shell .gr-checkbox .info,
.gradio-container .gr-checkbox .info {
    color: var(--win-muted) !important;
    font-size: 11px !important;
    margin-top: 4px !important;
}

/* Standard checkbox styling */
.app-shell .gr-checkbox input[type="checkbox"],
.gradio-container .gr-checkbox input[type="checkbox"] {
    appearance: auto !important;
    -webkit-appearance: checkbox !important;
    width: 18px !important;
    height: 18px !important;
    cursor: pointer !important;
    margin-right: 8px !important;
    accent-color: var(--win-accent) !important;
    flex-shrink: 0 !important;
}

/* Ensure the checkbox is clickable */
.app-shell .gr-checkbox input[type="checkbox"],
.gradio-container .gr-checkbox input[type="checkbox"],
.app-shell .gr-checkbox label,
.gradio-container .gr-checkbox label {
    pointer-events: auto !important;
    cursor: pointer !important;
}

/* Number input styling */
.app-shell .gr-number,
.gradio-container .gr-number {
    background: var(--win-panel) !important;
    border: 1px solid var(--win-stroke) !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
}

.app-shell .gr-number label,
.gradio-container .gr-number label {
    color: var(--win-text);
    font-size: 13px;
    font-weight: 500;
}

.app-shell .gr-number .info,
.gradio-container .gr-number .info {
    color: var(--win-muted);
    font-size: 11px;
    margin-top: 4px;
}

.app-shell .gr-number input[type="number"],
.gradio-container .gr-number input[type="number"] {
    background: var(--win-panel);
    color: var(--win-text);
    border: 1px solid var(--win-stroke);
    border-radius: 6px;
    padding: 6px 10px;
    width: 100%;
    accent-color: var(--win-accent);
}

.app-shell .gr-number input[type="number"]:focus,
.gradio-container .gr-number input[type="number"]:focus {
    border-color: var(--win-accent);
    outline: none;
}

.app-shell .gr-slider input[type="range"]::-webkit-slider-thumb,
.gradio-container .gr-slider input[type="range"]::-webkit-slider-thumb {
    appearance: none !important;
    -webkit-appearance: none !important;
    width: 18px !important;
    height: 18px !important;
    background: var(--win-accent) !important;
    border-radius: 50% !important;
    cursor: pointer !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
    margin-top: -5px !important;
}

.app-shell .gr-slider input[type="range"]::-moz-range-thumb,
.gradio-container .gr-slider input[type="range"]::-moz-range-thumb {
    width: 18px !important;
    height: 18px !important;
    background: var(--win-accent) !important;
    border-radius: 50% !important;
    cursor: pointer !important;
    border: none !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
}
"""


async def run(query: str, num_searches: float):
    # Ensure num_searches is within valid range (1-5)
    if num_searches is None:
        num_searches = 3
    num_searches = max(1, min(5, int(num_searches)))
    # Email sending is disabled - always set to False
    send_email = False
    logger.info(f"Starting research for query: {query}, num_searches: {num_searches}, send_email: {send_email}")
    status_text = ""
    report_text = "*Report will appear here once research begins...*"
    report_store = ""
    
    # Initialize with empty status
    yield status_text, report_text, report_store
    
    try:
        async for chunk in ResearchManager().run(query, num_searches=num_searches, send_email=send_email):
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


with gr.Blocks() as ui:
    with gr.Column(elem_classes=["app-shell"]):
        with gr.Row(elem_classes=["header-row"]):
            gr.Markdown("# Deep Research", elem_classes=["header-title"])
        gr.Markdown(
            "An AI-powered research automation system that performs comprehensive web research on any topic and generates detailed reports. The system uses multiple specialized AI agents to plan searches, gather information, synthesize findings, and deliver results via email.",
            elem_classes=["description-text"]
        )
        with gr.Row():
            query_textbox = gr.Textbox(label="What topic would you like to research?", scale=3)
            num_searches_input = gr.Number(
                label="Number of searches",
                value=3,
                minimum=1,
                maximum=5,
                scale=1,
                info="Number of parallel search queries (1-5)"
            )
        run_button = gr.Button("Run", elem_classes=["run-btn"])
        report_state = gr.State("")
        
        with gr.Row():
            with gr.Column(scale=1):
                status = gr.Markdown(label="Status", value="**Ready to research**\n\nEnter a query and click Run to begin.")
            with gr.Column(scale=2):
                report = gr.Markdown(label="Report", value="*Report will appear here once research begins...*")
        
        with gr.Row(elem_classes=["save-row"]):
            save_button = gr.Button("Save report", variant="secondary", elem_classes=["save-btn"], scale=0, min_width=0)
            saved_file = gr.File(label="Download report", interactive=False, file_count="single", scale=2, elem_classes=["download-card"])
    
    run_button.click(fn=run, inputs=[query_textbox, num_searches_input], outputs=[status, report, report_state])
    query_textbox.submit(fn=run, inputs=[query_textbox, num_searches_input], outputs=[status, report, report_state])
    save_button.click(fn=save_report, inputs=report_state, outputs=saved_file)

ui.launch(
    server_name="0.0.0.0",
    server_port=int(os.getenv("PORT", 7860)),
    share=False,
    inbrowser=False,
    css=CUSTOM_CSS,
)
