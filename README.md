---
# Deep Research

An AI-powered research automation system that performs comprehensive web research on any topic and generates detailed reports. The system uses multiple specialized AI agents to plan searches, gather information, synthesize findings, and deliver results via email.

## Features

- **Intelligent Search Planning**: Automatically generates 5 targeted web searches based on your research query
- **Parallel Web Search**: Performs multiple searches simultaneously for faster results
- **AI-Powered Synthesis**: Combines search results into comprehensive, well-structured reports
- **Email Delivery**: Automatically sends formatted research reports via email
- **Web Interface**: Clean, user-friendly Gradio interface for easy interaction
- **Real-time Progress**: Live updates on research progress and status

## Architecture

The system consists of several specialized AI agents:

- **Planner Agent**: Analyzes your query and creates a strategic search plan
- **Search Agent**: Performs web searches and summarizes findings
- **Writer Agent**: Synthesizes all research into comprehensive reports
- **Email Agent**: Formats and sends reports via email
- **Research Manager**: Orchestrates the entire research workflow

## Prerequisites

- Python 3.8+
- OpenAI API key
- SendGrid API key (for email functionality)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd deep_research
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the project root with:
```
OPENAI_API_KEY=your_openai_api_key_here
SENDGRID_API_KEY=your_sendgrid_api_key_here
```

4. Configure email settings:
Edit `email_agent.py` to set your email addresses:
- Line 12: Set your verified sender email
- Line 13: Set your recipient email

## Usage

### Web Interface

1. Run the application:
```bash
python deep_research.py
```

2. Open your browser to the provided URL (usually `http://localhost:7860`)

3. Enter your research query in the text box

4. Click "Run" or press Enter to start the research process

5. Watch the real-time progress updates

6. Receive your comprehensive research report via email

### Example Queries

- "What are the latest developments in quantum computing?"
- "How is artificial intelligence being used in healthcare?"
- "What are the environmental impacts of cryptocurrency mining?"
- "Recent advances in renewable energy storage technologies"

## How It Works

1. **Query Analysis**: The planner agent analyzes your research question and creates 5 targeted search queries
2. **Parallel Search**: Multiple search agents simultaneously perform web searches
3. **Content Synthesis**: The writer agent combines all findings into a comprehensive report
4. **Email Delivery**: The email agent formats and sends the final report
5. **Progress Tracking**: Real-time updates keep you informed throughout the process

## Output

The system generates:
- **Short Summary**: 2-3 sentence overview of key findings
- **Detailed Report**: 5-10 page comprehensive analysis in markdown format
- **Follow-up Questions**: Suggested topics for further research
- **Email Notification**: Formatted HTML email with the complete report

## Configuration

### Search Parameters
- Number of searches: 5 (configurable in `planner_agent.py`)
- Search context size: Low (for focused results)
- Report length: 1000+ words, 5-10 pages

### Model Settings
- Primary model: GPT-4o-mini (cost-effective for most tasks)
- Tool choice: Required (ensures proper tool usage)

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure your OpenAI and SendGrid API keys are correctly set in the `.env` file
2. **Email Not Sending**: Verify your SendGrid sender email is verified and recipient email is correct
3. **Search Failures**: Some searches may fail due to rate limits or network issues - the system will continue with successful searches

### Debugging

- Check the console output for detailed error messages
- View OpenAI traces using the provided trace URL for detailed execution logs
- Ensure all dependencies are properly installed

## Dependencies

- `gradio`: Web interface framework
- `python-dotenv`: Environment variable management
- `sendgrid`: Email delivery service
- `pydantic`: Data validation and settings
- `agents`: Custom AI agent framework (assumed to be available)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions:
- Check the troubleshooting section above
- Review the console output and trace logs
- Ensure all API keys and configurations are correct

---

**Note**: This system requires valid API keys for OpenAI and SendGrid to function properly. Make sure to keep your API keys secure and never commit them to version control.
