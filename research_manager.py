from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from critic_agent import critic_agent, CriticalAudit
from email_agent import email_agent
import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class ResearchManager:

    async def run(self, query: str, num_searches: int = 3, send_email: bool = True):
        """Run the deep research process, yielding status updates and streaming the report.
        
        Args:
            query: The research query
            num_searches: Number of parallel search queries to perform (1-5, default: 5)
            send_email: Whether to send the report via email at the end (default: True)
        """
        # Ensure num_searches is within valid range
        num_searches = max(1, min(5, int(num_searches)))
        try:
            trace_id = gen_trace_id()
            safe_topic = query.strip()[:60] if query else "Research"
            workflow_name = f"Research: {safe_topic}"
            logger.info(f"Starting research run with trace_id: {trace_id}, num_searches: {num_searches}, send_email: {send_email}")
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
                    search_plan = await self.plan_searches(query, num_searches)
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
                    yield "**Starting critical audit phase...**\n\n"
                except Exception as e:
                    logger.error(f"Error in write_report: {str(e)}", exc_info=True)
                    yield f"**Error writing report:** {str(e)}"
                    raise

                try:
                    yield "- **Agent: Critic Agent** - Auditing and validating research report...\n\n"
                    # Add timeout to prevent hanging
                    import asyncio
                    try:
                        audit = await asyncio.wait_for(
                            self.audit_report(final_report),
                            timeout=60.0  # 60 second timeout
                        )
                        logger.info("Report audit completed successfully")
                        
                        # Append audit to report
                        audit_section = self._format_audit(audit)
                        final_report_with_audit = final_report + "\n\n" + audit_section
                        # Add signature after audit
                        final_report_with_audit = self._add_report_signature(final_report_with_audit, query)
                        
                        display_report_with_audit = display_report + "\n\n" + audit_section
                        # Add signature to display report (extract just the signature part)
                        signature_only = self._add_report_signature("", query).lstrip()
                        display_report_with_audit = display_report_with_audit + "\n\n" + signature_only
                        
                        yield f"- **Critic Agent** completed - Critical audit generated\n\n"
                    except asyncio.TimeoutError:
                        logger.warning("Critic agent timed out after 60 seconds, skipping audit")
                        yield "- **Critic Agent** timed out - Skipping audit and continuing with report\n\n"
                        final_report_with_audit = final_report
                        display_report_with_audit = display_report
                        # Add signature
                        final_report_with_audit = self._add_report_signature(final_report_with_audit, query)
                        signature_only = self._add_report_signature("", query).lstrip()
                        display_report_with_audit = display_report_with_audit + "\n\n" + signature_only
                    
                    if send_email:
                        yield "**Report ready - streaming to you now (email will send next)...**\n\n"
                    else:
                        yield "**Report ready - streaming to you now...**\n\n"
                    yield display_report_with_audit
                    
                    # Update report object with audit and signature
                    report.markdown_report = final_report_with_audit
                    
                    if send_email:
                        yield "**Starting email phase...**\n\n"
                except Exception as e:
                    logger.error(f"Error in audit_report: {str(e)}", exc_info=True)
                    yield f"- **Critic Agent** error: {str(e)}. Continuing with original report.\n\n"
                    # Continue with original report if audit fails
                    final_report_with_audit = final_report
                    display_report_with_audit = display_report
                    # Add signature
                    final_report_with_audit = self._add_report_signature(final_report_with_audit, query)
                    signature_only = self._add_report_signature("", query).lstrip()
                    display_report_with_audit = display_report_with_audit + "\n\n" + signature_only
                    
                    if send_email:
                        yield "**Report ready - streaming to you now (email will send next)...**\n\n"
                    else:
                        yield "**Report ready - streaming to you now...**\n\n"
                    yield display_report_with_audit
                    
                    # Update report object with signature
                    report.markdown_report = final_report_with_audit
                    
                    if send_email:
                        yield "**Starting email phase...**\n\n"
                except Exception as e:
                    logger.error(f"Error in write_report: {str(e)}", exc_info=True)
                    yield f"**Error writing report:** {str(e)}"
                    raise

                if send_email:
                    try:
                        yield "- **Agent: Email Agent** - Formatting and sending report via email...\n\n"
                        await self.send_email(report)
                        logger.info("Email sent successfully")
                        yield "- **Email Agent** completed - Report sent successfully\n\n"
                        yield "**Research process complete!**\n\n"
                    except Exception as e:
                        logger.warning(f"Email sending failed: {str(e)}", exc_info=True)
                        yield f"Email sending failed: {str(e)}. Research complete."
                else:
                    yield "**Research process complete!** (Email sending was disabled)\n\n"

        except Exception as e:
            logger.error(f"Fatal error in research run: {str(e)}", exc_info=True)
            yield f"**Fatal Error:** {str(e)}\n\nPlease check the logs for more details."


    async def plan_searches(self, query: str, num_searches: int = 3) -> WebSearchPlan:
        """Plan the searches to perform for the query.
        
        Args:
            query: The research query
            num_searches: Number of search queries to generate (1-5)
        """
        # Ensure num_searches is within valid range
        num_searches = max(1, min(5, int(num_searches)))
        logger.info(f"Planning {num_searches} searches for query: {query}")
        print(f"Planning {num_searches} searches...")
        try:
            # Create dynamic instructions for the planner agent
            from planner_agent import planner_agent
            instructions = f"""You are a research planning assistant that creates web search queries.

CRITICAL RULES:
1. Generate EXACTLY {num_searches} search queries that will gather the MOST RECENT information
2. Add recency constraints to queries using RELATIVE TIME REFERENCES ONLY:
   - Use terms like "latest", "current", "recent", "newest", "most recent", "up-to-date"
   - Prefer phrases like "latest version", "current status", "recent updates", "newest developments"
   - NEVER include hardcoded years like "2024", "2025", or any specific year - use relative time terms instead
3. Prioritize queries that will find:
   - Official documentation and vendor sites
   - Recent news and announcements
   - Current specifications and features
4. Avoid generic queries - be specific and include temporal indicators using relative time language

Your searches should ensure the research is based on up-to-date information, not outdated sources. Always use relative time references, never hardcoded years.
IMPORTANT: You must generate EXACTLY {num_searches} search queries."""
            
            # Temporarily update planner agent instructions
            original_instructions = planner_agent.instructions
            planner_agent.instructions = instructions
            
            try:
                result = await Runner.run(
                    planner_agent,
                    f"Query: {query}\n\nGenerate EXACTLY {num_searches} search queries.",
                )
                plan = result.final_output_as(WebSearchPlan)
                
                # Ensure we have the correct number of searches
                if len(plan.searches) != num_searches:
                    logger.warning(f"Planner generated {len(plan.searches)} searches, expected {num_searches}. Adjusting...")
                    if len(plan.searches) > num_searches:
                        plan.searches = plan.searches[:num_searches]
                    # If fewer, we'll use what we have (planner might have had a good reason)
                
                logger.info(f"Will perform {len(plan.searches)} searches")
                print(f"Will perform {len(plan.searches)} searches")
                return plan
            finally:
                # Restore original instructions
                planner_agent.instructions = original_instructions
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

    def _format_audit(self, audit: CriticalAudit) -> str:
        """Format the critical audit into markdown."""
        audit_md = f"""

---

## Critical Audit Report

### Overall Assessment
{audit.critical_summary}

### Confidence Score: {audit.confidence_score.score}/100

{chr(10).join(f"- {point}" for point in audit.confidence_score.explanation)}

### Unproven Assumptions

"""
        for i, assumption in enumerate(audit.unproven_assumptions, 1):
            audit_md += f"""
**Assumption {i}:**
- **Claim:** {assumption.claim}
- **Weakness:** {assumption.weakness}
- **Required Evidence:** {assumption.required_evidence}

"""

        audit_md += "\n### Marketing Claims vs Technical Reality\n\n"
        for i, classification in enumerate(audit.capability_classifications, 1):
            audit_md += f"""
**Capability {i}: {classification.capability}**
- **Classification:** {classification.classification}
- **Reasoning:** {classification.reasoning}

"""

        audit_md += "\n### Missing Critical Questions\n\n"
        for i, question in enumerate(audit.missing_questions, 1):
            audit_md += f"""
**Question {i}: {question.question}**
- **Importance:** {question.importance}

"""

        audit_md += f"""
### Agentic & MCP Readiness Assessment

**Autonomous Agents Support:**
{audit.agentic_readiness.autonomous_agents}

**Secure Execution:**
{audit.agentic_readiness.secure_execution}

**Context Governance:**
{audit.agentic_readiness.context_governance}

**Missing Components:**
{audit.agentic_readiness.missing_components}

---
"""
        return audit_md

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
- Critic Agent (critical audit and validation)
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
            
            # Don't add signature here - it will be added after audit
            
            logger.info("Report written successfully")
            print("Finished writing report")
            return report
        except Exception as e:
            logger.error(f"Error in write_report: {str(e)}", exc_info=True)
            raise

    async def audit_report(self, report_markdown: str) -> CriticalAudit:
        """Audit the research report for weaknesses, assumptions, and gaps."""
        logger.info("Auditing report...")
        print("Auditing report...")
        try:
            result = await Runner.run(
                critic_agent,
                f"Research Report to Audit:\n\n{report_markdown}",
            )
            audit = result.final_output_as(CriticalAudit)
            logger.info("Report audit completed successfully")
            print("Report audit completed")
            return audit
        except Exception as e:
            logger.error(f"Error in audit_report: {str(e)}", exc_info=True)
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
