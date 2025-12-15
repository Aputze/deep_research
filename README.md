---
title: Deep Research
emoji: "🔍"
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 6.1.0
app_file: deep_research.py
pinned: false
---

# Deep Research 🔍

**An AI-powered research automation system that performs comprehensive web research on any topic and generates detailed reports using live web searches.**

Deep Research uses multiple specialized AI agents to plan searches, gather current information, synthesize findings, and deliver results. Built with a focus on **accuracy through real-time data**, the system prioritizes up-to-date information over potentially outdated training data.

---

## 🌟 Key Features

### Research Capabilities
- ✅ **Live Web Research** - Uses SERPER API for real-time web searches, ensuring current information
- ✅ **Intelligent Planning** - Automatically generates 5 targeted search queries with recency constraints
- ✅ **Parallel Execution** - Performs multiple searches simultaneously for faster results
- ✅ **Source Verification** - Cross-checks facts across 2+ independent sources when possible
- ✅ **Recency Prioritization** - Prefers sources from the last 12 months, official documentation, and reputable sites

### User Experience
- ✅ **Modern Web Interface** - Clean, dark-mode Gradio UI with responsive design
- ✅ **Real-time Streaming** - Watch status updates and report generation in real-time
- ✅ **Report Export** - Download comprehensive reports as markdown files
- ✅ **Email Delivery** - Automatically sends formatted research reports via Mailjet
- ✅ **OpenAI Tracing** - Full workflow visibility in OpenAI Platform's Traces tab

### Output Quality
- ✅ **Comprehensive Reports** - 5-10 page detailed analyses (1000+ words)
- ✅ **Structured Format** - Markdown formatting with sections, summaries, and follow-up questions
- ✅ **Evidence-Based** - All content based solely on current web research, not training data

---

## 🏗️ System Architecture

The system consists of specialized AI agents working in orchestration:

### Agent Overview

| Agent | Role | Key Responsibilities |
|-------|------|---------------------|
| **Planner Agent** | Search Strategy | Analyzes queries and creates search plans with recency constraints (e.g., "latest 2024 developments", "current status") |
| **Search Agent** | Web Research | Performs live SERPER searches, prioritizes recent sources (last 12 months), verifies across multiple sources |
| **Writer Agent** | Content Synthesis | Combines research into comprehensive reports (1000+ words) based solely on web results |
| **Email Agent** | Delivery | Formats and sends reports via Mailjet email service |
| **Research Manager** | Orchestration | Coordinates workflow, manages async operations, provides real-time status updates |

### Research Philosophy

**Core Principle**: The system assumes internal knowledge may be outdated (cutoff ~2023). Therefore:

1. **Every research task** MUST perform live web searches using SERPER
2. **Sources are prioritized** by recency (last 12 months) and authority (official docs → vendor sites → reputable blogs)
3. **Important facts** are cross-verified across 2+ independent sources when possible
4. **Answers are based** ONLY on current web results, never pre-existing knowledge
5. **Gaps are transparent** - explicitly states when no recent information is available

---

## 📋 Prerequisites

Before you begin, ensure you have:

- **Python** 3.8 or higher
- **OpenAI API Key** - For AI agent execution
- **Mailjet API Credentials** - API key and secret for email delivery
- **SERPER API Key** - For web search functionality

### Getting API Keys

1. **OpenAI**: [Get your API key](https://platform.openai.com/api-keys)
2. **Mailjet**: [Sign up and get credentials](https://www.mailjet.com/)
3. **SERPER**: [Register and get API key](https://serper.dev/)

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Deep-research
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
MAILJET_API_KEY=your_mailjet_api_key_here
MAILJET_API_SECRET=your_mailjet_api_secret_here
SERPER_API_KEY=your_serper_api_key_here
```

### 4. Configure Email Settings

Edit `email_agent.py` to set your sender and recipient email addresses:

```python
"From": {
    "Email": "your-sender@example.com",  # Must be verified in Mailjet
    "Name": "Deep Research"
},
"To": [
    {
        "Email": "your-recipient@example.com",
    }
]
```

**Important**: Email addresses must be verified in your Mailjet account before sending.

---

## 💻 Usage

### Starting the Application

1. **Run the application:**
   ```bash
   python deep_research.py
   ```

2. **Access the web interface:**
   - The app will start on `http://localhost:7860` (or the port specified in `PORT` environment variable)
   - The URL will be displayed in the console

### Performing Research

1. **Enter your research query** in the text input box
2. **Click "Run"** or press Enter to start
3. **Monitor progress** in the Status panel:
   - View which agent is currently active
   - See search queries being executed
   - Track completion status
   - Access the OpenAI trace link
4. **Watch the report** stream in real-time in the Report panel
5. **Download the report** using the "Save report" button when complete
6. **Check your email** for the formatted report delivery

### Example Research Queries

- "What are the latest developments in quantum computing in 2024?"
- "How is artificial intelligence being used in healthcare currently?"
- "Recent advances in renewable energy storage technologies"
- "Current status and trends in cryptocurrency regulation"
- "Latest research on climate change mitigation strategies"
- "What are the newest features in Python 3.12 and 3.13?"

---

## 🔄 How It Works

### Research Workflow

```
┌─────────────────┐
│  User Query     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Planner Agent   │ → Generates 5 search queries with recency constraints
└────────┬────────┘   (e.g., "latest 2024 developments", "current status")
         │
         ▼
┌─────────────────┐
│ Search Agent    │ → Performs parallel SERPER web searches
│ (x5 parallel)   │   - Prioritizes last 12 months
│                 │   - Cross-verifies sources
└────────┬────────┘   - Produces concise summaries
         │
         ▼
┌─────────────────┐
│ Writer Agent    │ → Synthesizes into comprehensive report
└────────┬────────┘   - 1000+ words, structured markdown
         │
         ▼
┌─────────────────┐
│ Email Agent     │ → Formats and sends via Mailjet
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Final Output    │ → Report + Email + Downloadable file
└─────────────────┘
```

### Detailed Process

1. **Query Analysis & Planning**
   - Planner agent analyzes your research question
   - Creates 5 targeted search queries
   - Adds recency constraints (2024, 2025, "latest", "current")
   - Prioritizes queries for official docs and recent content

2. **Live Web Search**
   - Multiple search agents execute queries simultaneously using SERPER
   - Source prioritization:
     - Last 12 months (strongly preferred)
     - Official documentation and vendor websites
     - Reputable tech blogs and news sites
     - Outdated sources ignored unless no alternative exists
   - Cross-verification of important facts across sources
   - Production of concise summaries (2-3 paragraphs, <300 words)

3. **Content Synthesis**
   - Writer agent combines all findings
   - Creates structured report with:
     - Short summary (2-3 sentences)
     - Detailed markdown report (5-10 pages, 1000+ words)
     - Follow-up questions (2-3 suggestions)
   - Based solely on web research results, not training data

4. **Email Delivery**
   - Email agent formats report as HTML
   - Sends via Mailjet to configured recipient
   - Includes full report content

5. **Progress Tracking**
   - Real-time streaming updates throughout process
   - OpenAI trace link for detailed execution logs
   - Status updates for each agent phase

---

## 📤 Output Format

The system generates comprehensive research outputs:

### Report Structure

- **Short Summary**: 2-3 sentence overview of key findings
- **Detailed Report**: Comprehensive analysis in markdown format:
  - 5-10 pages of content
  - 1000+ words
  - Structured sections and subsections
  - Evidence-based content from web sources
- **Follow-up Questions**: 2-3 suggested topics for further research

### Delivery Methods

1. **Web Interface**: Streaming display with real-time updates
2. **Email**: Formatted HTML email with complete report
3. **Downloadable File**: Markdown file for local storage and editing

---

## ⚙️ Configuration

### Search Parameters

| Parameter | Value | Location |
|-----------|-------|----------|
| Number of searches | 5 | `planner_agent.py` (`HOW_MANY_SEARCHES`) |
| Search context size | Low | `search_agent.py` (WebSearchTool) |
| Report length | 1000+ words | `writer_agent.py` (instructions) |
| Recency priority | Last 12 months | `search_agent.py` (instructions) |

### Model Settings

| Setting | Value | Purpose |
|---------|-------|---------|
| Primary model | GPT-4o-mini | Cost-effective for research tasks |
| Tool choice | Required | Ensures proper SERPER tool usage |
| Temperature | 0.7 | Balanced creativity and accuracy |

### UI Configuration

- **Dark mode**: Always enabled (custom CSS)
- **Streaming**: Enabled for status and report updates
- **Port**: 7860 (configurable via `PORT` environment variable)
- **Server**: 0.0.0.0 (accessible from network)

---

## 🔍 OpenAI Tracing

The system provides comprehensive workflow visibility through OpenAI Platform:

### Features

- **Trace ID**: Unique identifier generated for each research run
- **Workflow View**: All agent executions appear as steps in the workflow trace
- **Detailed Logs**: View complete execution details, API calls, and responses
- **Link Access**: Direct link provided in UI status panel

### Accessing Traces

1. Click the trace link in the Status panel during/after research
2. Or visit: `https://platform.openai.com/logs/trace?trace_id={trace_id}`
3. View in OpenAI Platform's "Traces" tab for detailed execution logs

### What You'll See

- Main workflow trace for the entire research process
- Individual agent execution steps
- API calls and responses
- Timing and performance metrics
- Error details (if any)

---

## 🛠️ Dependencies

### Core Dependencies

```
gradio>=6.1.0          # Web interface framework
python-dotenv>=1.0.0   # Environment variable management
mailjet-rest>=1.3.0    # Email delivery service
pydantic>=2.0.0        # Data validation and settings
openai>=1.102.0        # OpenAI API client
openai-agents>=0.2.10  # Agent framework utilities
```

### Installation

All dependencies are listed in `requirements.txt`. Install with:

```bash
pip install -r requirements.txt
```

---

## 📁 Project Structure

```
Deep-research/
├── deep_research.py          # Main application with Gradio UI
├── research_manager.py       # Orchestrates the research workflow
├── planner_agent.py          # Search planning agent
├── search_agent.py           # Web search agent with SERPER
├── writer_agent.py           # Report synthesis agent
├── email_agent.py            # Email delivery agent
├── agents.py                 # Agent framework and runner
├── requirements.txt          # Python dependencies
├── README.md                 # This file
└── .env                      # Environment variables (create this)
```

### Key Files

- **`deep_research.py`**: Main entry point, Gradio UI, CSS styling
- **`research_manager.py`**: Workflow orchestration, async coordination
- **`planner_agent.py`**: Search query generation with recency constraints
- **`search_agent.py`**: SERPER integration, web search execution
- **`writer_agent.py`**: Report generation and formatting
- **`email_agent.py`**: Mailjet email sending
- **`agents.py`**: Agent framework, OpenAI API integration, tracing

---

## 🐛 Troubleshooting

### Common Issues

#### API Key Errors

**Problem**: Authentication errors for OpenAI, Mailjet, or SERPER

**Solutions**:
- Verify all API keys are correctly set in `.env` file
- Check keys are valid and have sufficient quota/credits
- Ensure no extra spaces or quotes around keys in `.env`
- Restart the application after changing `.env`

#### Email Not Sending

**Problem**: Reports not received via email

**Solutions**:
- Verify sender email is verified in your Mailjet account
- Check recipient email is correct in `email_agent.py`
- Review Mailjet dashboard for delivery status and errors
- Ensure `MAILJET_API_KEY` and `MAILJET_API_SECRET` are set correctly
- Check Mailjet API logs for detailed error messages

#### Search Failures

**Problem**: Some searches fail or return no results

**Solutions**:
- Check SERPER API status and quota
- Verify `SERPER_API_KEY` is set correctly
- Some searches may fail due to rate limits or network issues
- System continues with successful searches
- Review console logs for specific error messages

#### No Recent Information Found

**Problem**: System reports no recent information available

**Solution**:
- This is by design - system prioritizes accuracy over completeness
- Try refining your query to be more specific
- Check if the topic has recent developments
- System explicitly states when no recent information is available rather than using outdated data

#### UI Not Loading or Displaying Incorrectly

**Problem**: Interface issues or styling problems

**Solutions**:
- Clear browser cache and refresh
- Check console for JavaScript errors
- Verify Gradio version matches requirements (`pip install --upgrade gradio`)
- Check port 7860 is not already in use
- Review browser console for CSS/styling errors

### Debugging

#### Enable Detailed Logging

The system uses Python logging. Check console output for:
- `INFO`: General workflow progress
- `DEBUG`: Detailed execution information
- `ERROR`: Error messages with stack traces

#### View OpenAI Traces

1. Get the trace ID from the Status panel
2. Visit the trace link in OpenAI Platform
3. Review execution logs, API calls, and responses
4. Check for error messages in the trace

#### Check Dependencies

```bash
pip list | grep -E "gradio|openai|pydantic|mailjet|dotenv"
```

Ensure all required packages are installed and up to date.

---

## 🔒 Security Best Practices

### API Key Management

- ✅ **Never commit** `.env` files or API keys to version control
- ✅ **Use environment variables** for all sensitive configuration
- ✅ **Rotate API keys** regularly
- ✅ **Keep keys secure** and limit access
- ✅ **Use `.gitignore`** to exclude `.env` files

### Email Security

- ✅ **Verify email addresses** in Mailjet before sending
- ✅ **Validate sender/recipient** emails in code
- ✅ **Use secure email services** (Mailjet provides TLS/SSL)
- ✅ **Review email content** before sending sensitive information

### General Security

- ✅ **Keep dependencies updated** (`pip install --upgrade`)
- ✅ **Review code changes** before deployment
- ✅ **Monitor API usage** for unusual activity
- ✅ **Use HTTPS** in production environments

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** with clear, well-documented code
4. **Test thoroughly**:
   - Test with various research queries
   - Verify all API integrations work correctly
   - Check UI functionality and styling
   - Ensure error handling is robust
5. **Commit your changes** with clear, descriptive messages
6. **Push to your branch** (`git push origin feature/amazing-feature`)
7. **Submit a pull request** with a detailed description of changes

### Development Guidelines

- Follow existing code style and structure
- Add logging for important operations
- Include error handling for API calls
- Update documentation for new features
- Test with real API keys (use test keys when possible)

---

## 📄 License

[Add your license information here]

---

## 💬 Support & Resources

### Getting Help

- **Check this README** first - many common issues are covered
- **Review console output** for detailed error messages
- **Check OpenAI traces** for workflow execution details
- **Verify API configurations** are correct

### Additional Resources

- **OpenAI Platform**: [platform.openai.com](https://platform.openai.com)
- **Mailjet Documentation**: [dev.mailjet.com](https://dev.mailjet.com)
- **SERPER API Docs**: [serper.dev](https://serper.dev)
- **Gradio Documentation**: [gradio.app/docs](https://gradio.app/docs)

---

## 📝 Notes

### Research Philosophy Reminder

This system is designed to provide **current, accurate information** based on live web searches. It:

- ✅ Prioritizes recency and accuracy over completeness
- ✅ Explicitly states when information is unavailable
- ✅ Never relies on potentially outdated knowledge
- ✅ Cross-verifies important facts when possible
- ✅ Transparently identifies information gaps

### API Requirements

**All three API keys are required** for full functionality:
- **OpenAI**: Core AI agent execution (required)
- **SERPER**: Web search functionality (required)
- **Mailjet**: Email delivery (optional, but recommended)

### Performance

- Typical research time: 2-5 minutes depending on query complexity
- Search execution: Parallel processing for faster results
- Report generation: Streaming for immediate feedback
- Email delivery: Usually completes within seconds of report generation

---

**Built with ❤️ for accurate, up-to-date research**

*Last updated: 2024*
