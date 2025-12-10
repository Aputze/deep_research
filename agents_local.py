import asyncio
import ast
import contextlib
import inspect
import json
import logging
import operator
import os
import uuid
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Callable, Iterable, List, Optional

# Framework for running AI agents using OpenAI API

logger = logging.getLogger(__name__)


@dataclass
class ModelSettings:
    tool_choice: Optional[str] = None


class WebSearchTool:
    def __init__(self, search_context_size: str = "low"):
        self.search_context_size = search_context_size


class Agent:
    def __init__(
        self,
        name: str,
        instructions: str,
        model: str | None = None,
        tools: Optional[List[Callable]] = None,
        output_type: Any | None = None,
        model_settings: ModelSettings | None = None,
    ):
        self.name = name
        self.instructions = instructions
        self.model = model
        self.tools = tools or []
        self.output_type = output_type
        self.model_settings = model_settings


def function_tool(func: Callable) -> Callable:
    """Decorator placeholder used for tool registration."""
    return func


# Thread-local storage for trace context
import threading
_trace_context = threading.local()

@contextlib.contextmanager
def trace(name: str, trace_id: str | None = None):
    """Context manager for tracing operations. Creates an Assistant run to establish a trace in Traces tab."""
    if trace_id is None:
        trace_id = gen_trace_id()
    
    # Create an Assistant run to establish a trace in OpenAI's Traces tab
    # Chat completions show in Completions tab, but Assistants API creates Traces
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    assistant_id = None
    thread_id = None
    run_id = None
    
    if openai_api_key:
        try:
            from openai import OpenAI
            # Create client with trace_id in headers for Assistant API calls
            extra_headers = {}
            if trace_id:
                extra_headers["OpenAI-Trace-Id"] = trace_id
            client = OpenAI(api_key=openai_api_key, default_headers=extra_headers if extra_headers else None)
            
            # Create or get a reusable assistant for tracing
            try:
                # Try to find existing assistant first
                assistants = client.beta.assistants.list(limit=20)
                existing = None
                for asst in assistants.data:
                    if asst.name == name:
                        existing = asst
                        break
                
                if existing:
                    assistant_id = existing.id
                else:
                    # Create a new assistant for this trace type - this will appear as a workflow trace
                    # Name it clearly as a workflow so it appears in workflow traces
                    assistant = client.beta.assistants.create(
                        name=name,
                        instructions=f"You are a workflow orchestrator tracking a research process.\n\nYour role is to acknowledge workflow steps and track progress:\n1. Planning searches\n2. Performing web searches\n3. Writing research reports\n4. Sending email reports\n\nAlways respond briefly to confirm you received each message.",
                        model="gpt-4o-mini",
                        tools=[],  # Tools will be added via function calling in actual agent runs
                        metadata={"workflow_type": "research", "trace_name": name}
                    )
                    assistant_id = assistant.id
                    logger.info(f"Created workflow assistant for trace: {assistant_id}")
            except Exception as e:
                logger.warning(f"Could not create/get assistant for trace: {e}")
            
            if assistant_id:
                try:
                    # Create a thread and initial run to establish the workflow trace
                    thread = client.beta.threads.create(
                        metadata={
                            "trace_id": trace_id,
                            "trace_name": name,
                            "workflow": "true",
                            "workflow_name": name
                        }
                    )
                    thread_id = thread.id
                    
                    # Create an initial message to start the workflow trace
                    try:
                        client.beta.threads.messages.create(
                            thread_id=thread_id,
                            role="user",
                            content=f"Orchestrate the research workflow: {name}\n\nTrace ID: {trace_id}\n\nThis workflow will execute these steps:\n1. Planning searches\n2. Performing web searches\n3. Writing research report\n4. Sending email report\n\nPlease confirm you will track these steps.",
                            metadata={
                                "trace_id": str(trace_id),
                                "workflow": "true",
                                "workflow_name": str(name),
                                "event": "workflow_start"
                            }
                        )
                    except Exception as e:
                        status = getattr(getattr(e, 'response', None), 'status_code', None)
                        body = None
                        try:
                            body = e.response.text  # type: ignore[attr-defined]
                        except Exception:
                            body = None
                        logger.warning(f"Could not post workflow start message to thread (status={status}): {e} body={body}")
                    
                    # Create a run with metadata - this creates the workflow trace.
                    # Use create_and_poll so the run is completed before we start adding messages,
                    # otherwise adding user messages while a run is active yields 400 errors.
                    run = client.beta.threads.runs.create_and_poll(
                        thread_id=thread_id,
                        assistant_id=assistant_id,
                        metadata={
                            "trace_id": trace_id,
                            "trace_name": name,
                            "workflow": "true",
                            "workflow_name": name,
                            "workflow_type": "research"
                        }
                    )
                    run_id = run.id
                    logger.info(f"Created assistant run for trace: {trace_id} (run_id: {run_id})")
                except Exception as e:
                    logger.warning(f"Could not create assistant run for trace: {e}")
        except Exception as e:
            logger.warning(f"Could not initialize trace with Assistant API: {e}")
    
    # Store trace context in thread-local storage
    _trace_context.trace_id = trace_id
    _trace_context.trace_name = name
    _trace_context.assistant_id = assistant_id
    _trace_context.thread_id = thread_id
    _trace_context.run_id = run_id
    
    try:
        yield
    finally:
        # Clean up thread-local storage
        if hasattr(_trace_context, 'trace_id'):
            delattr(_trace_context, 'trace_id')
        if hasattr(_trace_context, 'trace_name'):
            delattr(_trace_context, 'trace_name')
        if hasattr(_trace_context, 'assistant_id'):
            delattr(_trace_context, 'assistant_id')
        if hasattr(_trace_context, 'thread_id'):
            delattr(_trace_context, 'thread_id')
        if hasattr(_trace_context, 'run_id'):
            delattr(_trace_context, 'run_id')


def gen_trace_id() -> str:
    # Use plain UUIDs to match the working project's trace links.
    return str(uuid.uuid4())


def get_trace_context():
    """Get current trace context from thread-local storage."""
    trace_id = getattr(_trace_context, 'trace_id', None)
    trace_name = getattr(_trace_context, 'trace_name', None)
    assistant_id = getattr(_trace_context, 'assistant_id', None)
    thread_id = getattr(_trace_context, 'thread_id', None)
    run_id = getattr(_trace_context, 'run_id', None)
    return trace_id, trace_name, assistant_id, thread_id, run_id

def add_trace_message(message: str):
    """Add a message to the trace thread to build up the trace history."""
    trace_id, trace_name, assistant_id, thread_id, run_id = get_trace_context()
    if not thread_id:
        return
    
    try:
        from openai import OpenAI
        import os
        from dotenv import load_dotenv
        
        # Ensure environment is loaded
        load_dotenv(override=True)
        
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            logger.debug("No OpenAI API key found, skipping trace message")
            return
        
        # Create client with trace_id in headers
        trace_headers = {}
        if trace_id:
            trace_headers["OpenAI-Trace-Id"] = trace_id
        client = OpenAI(api_key=openai_api_key, default_headers=trace_headers if trace_headers else None)
        # Add message to thread to build up trace visibility
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=f"[{trace_name}] {message}" if trace_name else message,
            metadata={"trace_id": str(trace_id), "event": "agent_activity"} if trace_id else None
        )
    except Exception as e:
        status = getattr(getattr(e, 'response', None), 'status_code', None)
        body = None
        try:
            body = e.response.text  # type: ignore[attr-defined]
        except Exception:
            body = None
        logger.warning(f"Could not add message to trace (non-critical, status={status}): {e} body={body}", exc_info=True)


class RunnerResult:
    def __init__(self, final_output: Any):
        self.final_output = final_output

    def final_output_as(self, cls):
        if isinstance(self.final_output, cls):
            return self.final_output
        try:
            return cls(**self.final_output)  # type: ignore[arg-type]
        except Exception:
            return self.final_output


class Runner:
    @staticmethod
    async def run(agent: Agent, input_text: str, trace_id: str | None = None):
        """Run agent using OpenAI API with proper tool calling and structured outputs."""
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required. Please set it in your .env file.")
        
        if not agent.model:
            raise ValueError(f"Agent {agent.name} does not have a model specified.")
        
        from openai import OpenAI
        
        # Use provided trace_id or get from trace context if available
        if trace_id is None:
            trace_id, trace_name, assistant_id, thread_id, run_id = get_trace_context()
        else:
            _, trace_name, assistant_id, thread_id, run_id = get_trace_context()
        
        # Create client with extra headers for tracing
        # Note: OpenAI Python SDK uses default_headers on the client, not extra_headers on individual calls
        extra_headers = {}
        if trace_id:
            # Use trace_id in headers for grouping in OpenAI platform
            extra_headers["OpenAI-Trace-Id"] = trace_id
        
        client = OpenAI(api_key=openai_api_key, default_headers=extra_headers if extra_headers else None)
        
        logger.info(f"Running agent '{agent.name}' with model {agent.model}" + (f" (trace: {trace_id})" if trace_id else ""))
        
        # Add agent execution to the main workflow thread as a step
        # This makes each agent appear as a step in the workflow trace
        if thread_id:
            try:
                # Create client with trace_id in headers
                trace_headers = {}
                if trace_id:
                    trace_headers["OpenAI-Trace-Id"] = trace_id
                trace_client = OpenAI(api_key=openai_api_key, default_headers=trace_headers if trace_headers else None)
                # Add a message for this agent execution to the workflow thread
                try:
                    trace_client.beta.threads.messages.create(
                        thread_id=thread_id,
                        role="user",
                        content=f"[Agent Execution: {agent.name}]\n\n{input_text[:500]}",
                        metadata={
                            "trace_id": str(trace_id),
                            "agent_name": str(agent.name),
                            "workflow": str(trace_name),
                            "event": "agent_execution"
                        } if trace_id else None
                    )
                except Exception as e:
                    status = getattr(getattr(e, 'response', None), 'status_code', None)
                    body = None
                    try:
                        body = e.response.text  # type: ignore[attr-defined]
                    except Exception:
                        body = None
                    logger.debug(f"Could not add agent message to workflow thread (status={status}): {e} body={body}", exc_info=True)
                # Kick off a lightweight run for this agent so it shows as a step in the workflow trace
                try:
                    trace_client.beta.threads.runs.create_and_poll(
                        thread_id=thread_id,
                        assistant_id=assistant_id,
                        model=agent.model or "gpt-4o-mini",
                        instructions=f"Trace step marker for {agent.name}. No tool calls needed.",
                        metadata={
                            "trace_id": trace_id,
                            "agent_name": agent.name,
                            "workflow": trace_name,
                            "event": "agent_run"
                        } if trace_id else None,
                    )
                except Exception as e:
                    logger.debug(f"Could not create trace run for agent {agent.name}: {e}")
            except Exception as e:
                logger.debug(f"Could not add agent message to workflow thread: {e}")
        
        # Prepare tools for function calling
        tools = []
        if agent.tools:
            for tool_func in agent.tools:
                # For function tools, convert them to OpenAI function format
                if callable(tool_func) and not isinstance(tool_func, WebSearchTool):
                    sig = inspect.signature(tool_func)
                    tool_schema = {
                        "type": "function",
                        "function": {
                            "name": tool_func.__name__,
                            "description": tool_func.__doc__ or f"Tool: {tool_func.__name__}",
                            "parameters": {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        }
                    }
                    # Extract parameters from function signature
                    for param_name, param in sig.parameters.items():
                        param_type = "string"
                        if param.annotation != inspect.Parameter.empty:
                            if param.annotation == int:
                                param_type = "integer"
                            elif param.annotation == float:
                                param_type = "number"
                            elif param.annotation == bool:
                                param_type = "boolean"
                        tool_schema["function"]["parameters"]["properties"][param_name] = {"type": param_type}
                        if param.default == inspect.Parameter.empty:
                            tool_schema["function"]["parameters"]["required"].append(param_name)
                    tools.append(tool_schema)
        
        # For WebSearchTool, add a web search function
        has_web_search = any(isinstance(t, WebSearchTool) for t in agent.tools) if agent.tools else False
        if has_web_search:
            tools.append({
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for information about a topic. Returns relevant search results that can be summarized.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to execute"
                            }
                        },
                        "required": ["query"]
                    }
                }
            })
        
        # Prepare messages with trace context
        system_content = agent.instructions
        if trace_name:
            system_content = f"[Trace: {trace_name}]\n{agent.instructions}"
        
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": input_text}
        ]
        
        # Use trace_id as user identifier for grouping in OpenAI platform
        extra_params = {}
        if trace_id:
            extra_params["user"] = f"trace_{trace_id}"
        
        # Determine tool choice
        tool_choice = None
        if agent.model_settings and agent.model_settings.tool_choice == "required":
            tool_choice = "required"
        elif agent.model_settings and agent.model_settings.tool_choice:
            tool_choice = agent.model_settings.tool_choice
        
        # Planner agent: Use structured output
        if agent.output_type and agent.output_type.__name__ == "WebSearchPlan":
            plan_cls = agent.output_type
            logger.info(f"Using OpenAI API for planner agent with model: {agent.model}")
            
            user_prompt = f"User query: {input_text}\n\nGenerate a JSON response with a 'searches' array containing objects with 'query' and 'reason' fields. Output exactly 5 searches."
            
            planner_messages = [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_prompt}
            ]
            
            response = client.chat.completions.create(
                model=agent.model or "gpt-4o-mini",
                messages=planner_messages,
                response_format={"type": "json_object"},
                temperature=0.7,
                **extra_params,
            )
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI API")
            
            parsed_json = json.loads(content)
            
            # Extract searches from response
            if "searches" in parsed_json and isinstance(parsed_json["searches"], list):
                searches_data = parsed_json["searches"]
            elif isinstance(parsed_json, list):
                searches_data = parsed_json
            else:
                raise ValueError(f"Could not parse searches from OpenAI response: {parsed_json}")
            
            parsed_output = plan_cls(searches=searches_data)
            logger.info(f"Generated {len(parsed_output.searches)} searches using OpenAI API")
            for i, search in enumerate(parsed_output.searches, 1):
                logger.debug(f"  Search {i}: {search.query} - {search.reason}")
            return RunnerResult(parsed_output)
        
        # Search agent: Use function calling with web search
        if agent.name.lower().startswith("search"):
            logger.info(f"Using OpenAI API for search agent with model: {agent.model}")
            
            # Extract search query from input
            search_query = input_text
            if "Search term:" in input_text:
                search_query = input_text.split("Search term:")[-1].split("\n")[0].strip()
            
            max_iterations = 5
            iteration = 0
            
            while iteration < max_iterations:
                response = client.chat.completions.create(
                    model=agent.model,
                    messages=messages,
                    tools=tools if tools else None,
                    tool_choice=tool_choice,
                    temperature=0.7,
                    **extra_params,
                )
                
                message = response.choices[0].message
                messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [tc.model_dump() for tc in (message.tool_calls or [])] if message.tool_calls else None
                })
                
                # If no tool calls, return the content as summary
                if not message.tool_calls:
                    summary = message.content or f"Summary for: {search_query}"
                    logger.info(f"Search agent completed: {len(summary)} characters")
                    return RunnerResult(summary)
                
                # Handle tool calls (simulate web search results)
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments or "{}")
                    
                    if function_name == "web_search":
                        query = function_args.get("query", search_query)
                        # Simulate web search result (in real implementation, this would call actual search API)
                        search_result = f"Web search results for '{query}': Found relevant information about {query}. This is a simulated search result that would contain actual web content in a real implementation."
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": search_result
                        })
                    else:
                        # For other tools, call them directly
                        for tool_func in agent.tools:
                            if callable(tool_func) and tool_func.__name__ == function_name:
                                result = tool_func(**function_args)
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "content": json.dumps(result) if isinstance(result, dict) else str(result)
                                })
                                break
                
                iteration += 1
            
            # Final response should be the summary
            final_response = messages[-1].get("content", f"Summary for: {search_query}")
            return RunnerResult(final_response)
        
        # Writer agent: Use structured output
        if agent.output_type and agent.output_type.__name__ == "ReportData":
            report_cls = agent.output_type
            logger.info(f"Using OpenAI API for writer agent with model: {agent.model}")
            
            # Extract query and search results
            query_text = input_text
            search_results: list[str] = []
            if "Original query:" in input_text:
                parts = input_text.split("Original query:", 1)
                if len(parts) > 1:
                    remaining = parts[1]
                    if "Summarized search results:" in remaining:
                        query_part, results_part = remaining.split("Summarized search results:", 1)
                        query_text = query_part.strip()
                        try:
                            parsed = ast.literal_eval(results_part.strip())
                            if isinstance(parsed, list):
                                search_results = [str(item) for item in parsed]
                        except Exception:
                            search_results = [results_part.strip()]
            
            prompt = f"Original query: {query_text}\n\nSummarized search results:\n" + "\n".join(f"- {result}" for result in search_results) + "\n\nGenerate a comprehensive report. Return a JSON object with ALL of these required fields:\n- 'short_summary': A short 2-3 sentence summary\n- 'markdown_report': The full detailed report in markdown format\n- 'follow_up_questions': An array of 2-3 suggested research questions (required, cannot be empty or null)"
            
            messages = [
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ]
            
            response = client.chat.completions.create(
                model=agent.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.7,
                **extra_params,
            )
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI API")
            
            parsed_json = json.loads(content)
            # Ensure required fields exist to avoid validation errors
            # Handle follow_up_questions - must be a list
            if "follow_up_questions" not in parsed_json:
                parsed_json["follow_up_questions"] = []
            elif parsed_json.get("follow_up_questions") is None:
                parsed_json["follow_up_questions"] = []
            elif not isinstance(parsed_json.get("follow_up_questions"), list):
                parsed_json["follow_up_questions"] = [str(parsed_json.get("follow_up_questions"))]
            
            # Handle markdown_report
            if "markdown_report" not in parsed_json or not parsed_json.get("markdown_report"):
                # Fallback to use the whole content as markdown if missing
                parsed_json["markdown_report"] = content or "# Report\n\nNo content generated."
            
            # Handle short_summary
            if "short_summary" not in parsed_json or not parsed_json.get("short_summary"):
                markdown = parsed_json.get("markdown_report", "")
                parsed_json["short_summary"] = markdown[:200] + "..." if len(markdown) > 200 else markdown or "Report summary"

            # Create the report with validation
            try:
                output = report_cls(**parsed_json)
            except Exception as e:
                logger.error(f"Failed to create ReportData: {e}, JSON: {parsed_json}")
                # Create a fallback report with all required fields
                output = report_cls(
                    short_summary=parsed_json.get("short_summary", "Report generated"),
                    markdown_report=parsed_json.get("markdown_report", content or "# Report\n\nError generating report."),
                    follow_up_questions=list(parsed_json.get("follow_up_questions", []))
                )
            logger.info(f"Writer agent completed: {len(output.markdown_report)} characters in report")
            return RunnerResult(output)
        
        # Email agent: Use function calling
        if agent.tools:
            logger.info(f"Using OpenAI API for email agent with model: {agent.model}")
            
            response = client.chat.completions.create(
                model=agent.model,
                messages=messages,
                tools=tools,
                tool_choice="required" if tool_choice == "required" else "auto",
                temperature=0.7,
                **extra_params,
            )
            
            message = response.choices[0].message
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments or "{}")
                    
                    # Call the actual tool function
                    for tool_func in agent.tools:
                        if callable(tool_func) and tool_func.__name__ == function_name:
                            result = tool_func(**function_args)
                            logger.info(f"Email agent called {function_name}: {result.get('status', 'unknown')}")
                            return RunnerResult(result)
            
            return RunnerResult({"status": "no_tool_called"})
        
        # Fallback for other agents
        logger.warning(f"No specific handler for agent {agent.name}, using generic OpenAI call")
        response = client.chat.completions.create(
            model=agent.model,
            messages=messages,
            temperature=0.7,
            **extra_params,
        )
        
        content = response.choices[0].message.content or ""
        return RunnerResult(content)
