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
            # 2. OR it's very long (>1000 chars) AND contains report-like content
            is_report = False
            chunk_stripped = chunk.strip()
            if chunk_stripped.startswith("# Report"):
                is_report = True
            elif len(chunk) > 1000 and ("# Report" in chunk or ("**Query:**" in chunk and "## Findings" in chunk)):
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
    gr.Markdown("# Deep Research")
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    run_button = gr.Button("Run", variant="primary")
    report_state = gr.State("")
    
    with gr.Row():
        with gr.Column(scale=1):
            status = gr.Markdown(label="Status", value="**Ready to research**\n\nEnter a query and click Run to begin.")
        with gr.Column(scale=2):
            report = gr.Markdown(label="Report", value="*Report will appear here once research begins...*")
    
    with gr.Row():
        save_button = gr.Button("Save Report", variant="secondary")
        saved_file = gr.File(label="Download report", interactive=False, file_count="single")
    
    run_button.click(fn=run, inputs=query_textbox, outputs=[status, report, report_state])
    query_textbox.submit(fn=run, inputs=query_textbox, outputs=[status, report, report_state])
    save_button.click(fn=save_report, inputs=report_state, outputs=saved_file)

ui.launch(inbrowser=True)

