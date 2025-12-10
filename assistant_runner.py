import asyncio
import json
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI

from planner_agent import plan_searches
from search_agent import summarize_search
from writer_agent import write_report
from email_agent import send_email


def _client() -> OpenAI:
    load_dotenv(override=True)
    return OpenAI()


def _tools() -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "planner_tool",
                "description": "Plan web searches for the given query",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_tool",
                "description": "Summarize web search results for a term",
                "parameters": {
                    "type": "object",
                    "properties": {"term": {"type": "string"}},
                    "required": ["term"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "writer_tool",
                "description": "Write a detailed report from query and search summaries",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "search_results": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["query", "search_results"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "email_tool",
                "description": "Send the report via email",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subject": {"type": "string"},
                        "html_body": {"type": "string"},
                    },
                    "required": ["subject", "html_body"],
                },
            },
        },
    ]


def _ensure_assistant(client: OpenAI) -> str:
    # Create a fresh assistant each run to keep things simple/deterministic.
    assistant = client.beta.assistants.create(
        name="Research trace assistant",
        instructions=(
            "You are an orchestrator. Steps: "
            "1) Call planner_tool to get searches. "
            "2) For each search, call search_tool. "
            "3) Call writer_tool with query and the collected search summaries. "
            "4) Call email_tool with the final report. "
            "After tools complete, respond with the markdown report."
        ),
        model="gpt-4o-mini",
        tools=_tools(),
    )
    return assistant.id


def run_assistant_flow(query: str) -> Tuple[str, List[str]]:
    """
    Run the research flow via OpenAI Assistants so traces appear in Logs -> Traces.
    Returns (markdown_report, log_messages).
    """
    logs: List[str] = []
    client = _client()
    assistant_id = _ensure_assistant(client)
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(thread_id=thread.id, role="user", content=query)

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
    )

    markdown_report: str = ""
    search_results: List[str] = []

    while True:
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        status = run.status
        if status in ("queued", "in_progress"):
            # Avoid un-awaited coroutine warnings; yield briefly.
            import time
            time.sleep(0.05)
            continue
        if status == "requires_action":
            tool_calls = run.required_action.submit_tool_outputs.tool_calls
            outputs = []
            for call in tool_calls:
                name = call.function.name
                args = json.loads(call.function.arguments or "{}")
                if name == "planner_tool":
                    plan = asyncio.run(plan_searches(args["query"]))
                    output = plan.model_dump_json()
                    logs.append("Planner: planned searches")
                elif name == "search_tool":
                    summary = asyncio.run(summarize_search(args["term"]))
                    search_results.append(summary)
                    output = summary
                    logs.append(f"Search: {args['term']}")
                elif name == "writer_tool":
                    report = asyncio.run(write_report(args["query"], args["search_results"]))
                    markdown_report = report.markdown_report
                    output = report.model_dump_json()
                    logs.append("Writer: report generated")
                elif name == "email_tool":
                    res = send_email(args["subject"], args["html_body"])
                    output = json.dumps(res)
                    logs.append("Email: sent")
                else:
                    output = "{}"
                outputs.append({"tool_call_id": call.id, "output": output})
            client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id, run_id=run.id, tool_outputs=outputs
            )
            continue
        if status in ("completed", "cancelled", "failed", "expired"):
            break

    if not markdown_report:
        msgs = client.beta.threads.messages.list(thread_id=thread.id, limit=1)
        if msgs.data:
            content = msgs.data[0].content[0].text.value if msgs.data[0].content else ""
            markdown_report = content
    return markdown_report, logs

