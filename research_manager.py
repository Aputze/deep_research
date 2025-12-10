from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
import asyncio
import logging

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
                    yield f"- **Writer Agent** completed - Report generated ({len(report.markdown_report)} characters)\n\n"
                    yield "**Starting email phase...**\n\n"

                    final_report = report.markdown_report
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

                yield final_report
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
        """Perform a search for the query."""
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        logger.debug(f"Searching: {item.query} (reason: {item.reason})")
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            output = str(result.final_output)
            logger.debug(f"Search completed for: {item.query}")
            return output
        except Exception as e:
            logger.error(f"Error in search for '{item.query}': {str(e)}", exc_info=True)
            return None

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
