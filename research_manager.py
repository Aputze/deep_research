from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class ResearchManager:

    async def run(self, query: str):
        """Run the deep research process, yielding status updates and streaming the report."""
        try:
            trace_id = gen_trace_id()
            safe_topic = query.strip()[:60] if query else "Research"
            workflow_name = f"Research: {safe_topic}"
            logger.info(f"Starting research run with trace_id: {trace_id}")
            with trace(workflow_name, trace_id=trace_id):
                trace_link = f"https://platform.openai.com/logs/trace?trace_id={trace_id}"
                print("View workflow trace in OpenAI:")
                print(f"  Trace ID: {trace_id}")
                print(f"  URL: {trace_link}")
                yield f"**View Workflow Trace:** [OpenAI Platform - Traces Tab]({trace_link})\n\n"
                yield f"*Trace ID: `{trace_id}`*\n\n"

                print("Starting research...")
                logger.info("Starting research phase")
                yield "**Starting research process...**\n\n"

                try:
                    yield f"- **Agent: Planner Agent** - Planning search strategy for: *{query}*\n\n"
                    search_plan = await self.plan_searches(query)
                    logger.info(f"Search plan created with {len(search_plan.searches)} searches")
                    yield f"- **Planner Agent** completed - Generated {len(search_plan.searches)} search queries\n\n"
                    yield "**Starting search phase...**\n\n"
                except Exception as e:
                    logger.error(f"Error in plan_searches: {str(e)}", exc_info=True)
                    yield f"**Error planning searches:** {str(e)}"
                    raise

                try:
                    yield f"- **Agent: Search Agent** - Performing {len(search_plan.searches)} parallel searches...\n\n"

                    for i, item in enumerate(search_plan.searches, 1):
                        yield f"  - Search {i}/{len(search_plan.searches)}: *{item.query}*\n"

                    search_results = await self.perform_searches(search_plan)

                    logger.info(f"Completed searches, got {len(search_results)} results")
                    yield f"- **Search Agent** completed - Collected {len(search_results)} search results\n\n"
                    yield "**Starting report writing phase...**\n\n"
                except Exception as e:
                    logger.error(f"Error in perform_searches: {str(e)}", exc_info=True)
                    yield f"**Error performing searches:** {str(e)}"
                    raise

                try:
                    yield "- **Agent: Writer Agent** - Synthesizing research findings into comprehensive report...\n\n"
                    report = await self.write_report(query, search_results)
                    logger.info("Report written successfully")
                    final_report = report.markdown_report
                    display_report = final_report
                    if display_report and not display_report.strip().startswith("# Report"):
                        display_report = f"# Report\n\n{display_report}"
                    yield f"- **Writer Agent** completed - Report generated ({len(final_report)} characters)\n\n"
                    yield "**Report ready - streaming to you now (email will send next)...**\n\n"
                    yield display_report
                    yield "**Starting email phase...**\n\n"
                except Exception as e:
                    logger.error(f"Error in write_report: {str(e)}", exc_info=True)
                    yield f"**Error writing report:** {str(e)}"
                    raise

                try:
                    yield "- **Agent: Email Agent** - Formatting and sending report via email...\n\n"
                    await self.send_email(report)
                    logger.info("Email sent successfully")
                    yield "- **Email Agent** completed - Report sent successfully\n\n"
                    yield "**Research process complete!**\n\n"
                except Exception as e:
                    logger.warning(f"Email sending failed: {str(e)}", exc_info=True)
                    yield f"Email sending failed: {str(e)}. Research complete."

        except Exception as e:
            logger.error(f"Fatal error in research run: {str(e)}", exc_info=True)
            yield f"**Fatal Error:** {str(e)}\n\nPlease check the logs for more details."


    async def plan_searches(self, query: str) -> WebSearchPlan:
        """Plan the searches to perform for the query."""
        logger.info(f"Planning searches for query: {query}")
        print("Planning searches...")
        try:
            result = await Runner.run(
                planner_agent,
                f"Query: {query}",
            )
            plan = result.final_output_as(WebSearchPlan)
            logger.info(f"Will perform {len(plan.searches)} searches")
            print(f"Will perform {len(plan.searches)} searches")
            return plan
        except Exception as e:
            logger.error(f"Error in plan_searches: {str(e)}", exc_info=True)
            raise

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """Perform the searches to perform for the query."""
        logger.info(f"Performing {len(search_plan.searches)} searches")
        print("Searching...")

        num_completed = 0
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                if result is not None:
                    results.append(result)
                    logger.debug("Search completed successfully")
                else:
                    logger.warning("Search returned None result")
            except Exception as e:
                logger.error(f"Error waiting for search task: {str(e)}", exc_info=True)
            num_completed += 1
            print(f"Searching... {num_completed}/{len(tasks)} completed")
        logger.info(f"Finished searching, collected {len(results)} results")
        print("Finished searching")
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        """Perform a search for the query with progressive date filtering.
        
        Tries progressively wider date ranges: 3 months -> 12 months -> no limit.
        Returns the first successful result or None if all attempts fail.
        """
        base_query = item.query
        
        # Progressive date filtering: try 3 months, then 12 months, then no limit
        date_ranges = [
            ("3 months", "last 3 months"),
            ("12 months", "last 12 months"),
            ("no limit", None)
        ]
        
        for range_name, date_constraint in date_ranges:
            if date_constraint:
                # Add date constraint to query
                search_query = f"{base_query} {date_constraint}"
                input_text = f"Search term: {search_query}\nReason for searching: {item.reason}\n\nIMPORTANT: Focus on finding sources from the {range_name}. If you find sufficient relevant results (2+ sources), provide your summary. If results are insufficient, indicate this clearly in your response."
            else:
                # No date constraint for final attempt
                search_query = base_query
                input_text = f"Search term: {search_query}\nReason for searching: {item.reason}\n\nIMPORTANT: Search without date restrictions. Use any relevant sources found, even if older. Explicitly note in your summary that recent information was limited."
            
            logger.debug(f"Searching: {search_query} (reason: {item.reason}, date range: {range_name})")
            try:
                result = await Runner.run(
                    search_agent,
                    input_text,
                )
                output = str(result.final_output)
                
                # Check if we got meaningful results
                if output and len(output.strip()) > 50:
                    # Check if output explicitly indicates insufficient results
                    insufficient_indicators = [
                        "no recent information found",
                        "no information found",
                        "insufficient results",
                        "no relevant sources",
                        "could not find"
                    ]
                    has_sufficient_results = not any(
                        indicator.lower() in output.lower() 
                        for indicator in insufficient_indicators
                    )
                    
                    # If we have sufficient results, or this is our final attempt, use it
                    if has_sufficient_results or range_name == "no limit":
                        logger.debug(f"Search completed for: {base_query} (used {range_name} range)")
                        return output
                    else:
                        # Results were insufficient, try next date range
                        logger.debug(f"Insufficient results for {base_query} with {range_name} range, trying next range")
                        continue
                else:
                    # Very short output, try next range
                    logger.debug(f"Short output for {base_query} with {range_name} range, trying next range")
                    continue
                    
            except Exception as e:
                logger.error(f"Error in search for '{search_query}' with {range_name} range: {str(e)}", exc_info=True)
                # If this is the last attempt, return None; otherwise continue to next range
                if range_name == "no limit":
                    return None
                continue
        
        # If we exhausted all ranges without success, return None
        logger.warning(f"All date ranges exhausted for query: {base_query}")
        return None

    def _add_report_signature(self, markdown_report: str, query: str) -> str:
        """Add a signature section to the report with metadata."""
        signature = f"""

---

## Report Signature

**Date:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}

**Research Request:** {query}

**Agents Used:**
- Planner Agent (search strategy planning)
- Search Agent (web research with progressive date filtering)
- Writer Agent (report synthesis)
- Email Agent (report delivery)

**Tools Used:**
- SERPER Web Search API (progressive date filtering: 3 months → 12 months → no limit)
- Mailjet Email API

**Models Used:**
- gpt-4o-mini (all agents)

---

*Report generated by Deep Researcher*
"""
        return markdown_report + signature

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """Write the report for the query."""
        logger.info(f"Writing report for query: {query} with {len(search_results)} search results")
        print("Thinking about report...")
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        try:
            result = await Runner.run(
                writer_agent,
                input,
            )
            report = result.final_output_as(ReportData)
            
            # Add signature to the report
            report.markdown_report = self._add_report_signature(report.markdown_report, query)
            
            logger.info("Report written successfully")
            print("Finished writing report")
            return report
        except Exception as e:
            logger.error(f"Error in write_report: {str(e)}", exc_info=True)
            raise

    async def send_email(self, report: ReportData) -> None:
        logger.info("Sending email...")
        print("Writing email...")
        try:
            result = await Runner.run(
                email_agent,
                report.markdown_report,
            )
            logger.info("Email sent successfully")
            print("Email sent")
            return report
        except Exception as e:
            logger.error(f"Error in send_email: {str(e)}", exc_info=True)
            raise
