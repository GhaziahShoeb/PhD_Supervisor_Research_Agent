import os
from dotenv import load_dotenv
import logging

# Load environment variables first
load_dotenv()

# Defensive patch for a LangChain bug where _fetch_last_ai_and_tool_messages can raise
# UnboundLocalError when no AI message is present (e.g., if a model/tool fails early).
try:
    import langchain.agents.factory as lc_factory
    from langchain_core.messages import AIMessage

    _original_model_to_tools = lc_factory.model_to_tools

    def _safe_model_to_tools(state, *args, **kwargs):
        messages = state.get("messages") or []
        # If there is no AI message yet, bail out gracefully instead of crashing.
        if not any(isinstance(m, AIMessage) for m in messages):
            return {"messages": []}
        return _original_model_to_tools(state, *args, **kwargs)

    lc_factory.model_to_tools = _safe_model_to_tools
    # Log that the defensive patch was applied
    logging.getLogger("professor_research.agent").info("Applied LangChain defensive patch: safe_model_to_tools")
except Exception:
    # If the module isn't available in the current runtime, skip the patch silently.
    logging.getLogger("professor_research.agent").debug("LangChain factory patch not applied (module missing or error)")

from deepagents import create_deep_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from utils.tools import internet_search, read_file, write_file
from utils.backends import production_backend_factory
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")
# configure module logger
logger = logging.getLogger("professor_research.agent")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)
# 1. Define Models
model_gemini = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0, max_retries=5, timeout=600)

# 2. Define the Specialized Subagent Team
subagents = [
    {
        "name": "university-shortlister",
        "description": "Shortlists top-tier universities based on IT and AI and QS rankings.",
        "system_prompt": "Search for universities within the preferred country with strong research in AI and IT. Identify specific labs for Applied AI and Quantum Computing. Save your findings to /results/shortlist.md. When using the internet_search tool, include keywords and do not use 'site:' alone.",
        "tools": [internet_search, write_file],
        "model": model_gemini
    },
    {
        "name": "professor-discovery",
        "description": "Finds specific PIs in each shortlisted university working on stateful agents or QML.",
        "system_prompt": "Scan faculty directories to find professors. Filter for keywords: 'stateful agents', 'LLM memory', 'Quantum ML'. Save profiles to /results/profs_raw.json. When using the internet_search tool, include keywords and do not use 'site:' alone.",
        "tools": [internet_search, write_file, read_file],
        "model": model_gemini
    },
    {
        "name": "professor-validator",
        "description": "Deep-dives into publications and grant databases to check funding and PhD openings.",
        "system_prompt": "Check for active grants (SFI/ERC) and recent publications (2024-2026). Verify if they are currently accepting PhD students. Highlight those matching a B.Tech IT background. When using the internet_search tool, include keywords and do not use 'site:' alone.",
        "tools": [internet_search, read_file],
        "model": model_gemini
    },
    {
        "name" : "Master's Program Search Agent",
        "description": "Searches for suitable Master's programs based on user's research interests and academic background based on the universities shortlisted by the university-shortlister subagent. Only used when the user requests for Master's program options.",
        "tools": [internet_search, write_file, read_file],
        "model": model_gemini ,
        "system_prompt": (
            "You are a Master's Program Search Agent. Your task is to find suitable Master's programs for the user based on their research interests and academic background.\n"
            "1. Review the list of shortlisted universities provided by the university-shortlister subagent.\n"
            "2. For each university, search for Master's programs that align with the user's research interests and academic background.\n"
            "3. Compile a list of suitable Master's programs, including program name, university name, duration, and key research areas, tuition fees, and intake dates.  \n"
            "4. Save the compiled list to `/results/masters_programs.json`."
        ),
    }
]

# 3. Create the Main Orchestrator Agent
try:
    logger.info("Initializing subagents...")
    for sub in subagents:
        logger.info(f" - Subagent: {sub['name']} ({sub['description']})")
    
    logger.info("Creating deep agent 'academic-research-lead' with %d subagents", len(subagents))
    agent = create_deep_agent(
    model=model_gemini,
    name="academic-research-lead",
    system_prompt="""
You are the Lead Academic Coordinator. 

Your goal is to coordinate your subagents to find professors and compile a final report.

REPORT INSTRUCTIONS:
As the research progresses, compile the findings into a file named `/results/academic_report.md`.
You MUST use the following table format for the output:

| University Name | Professor Name | Designation | Email | Research Area | Active Grants | Recent Publication | PhD Openings |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |

For each findings of the Master's Program Search Agent if the user's requested about master's program , compile the findings into the file named '/results/Master's_Programs_Report.md'. You MUST use the following table format for the output:
| University Name | Program Name | Duration | Key Research Areas | Tuition Fees | Intake Dates |
| :--- | :--- | :--- | :--- | :--- | :--- |


Use the `write_file` tool to save this report to your persistent GCS storage (mapped to /results/).
When using the internet_search tool, include keywords and do not use 'site:' alone. 
""",
    subagents=subagents,
    tools=[write_file, read_file], # Orchestrator needs to write the final report and read subagent outputs
    backend=production_backend_factory
    )
    logger.info("Agent created: %s", getattr(agent, 'name', 'academic-research-lead'))
except Exception as e:
    logger.exception("Failed to create agent: %s", e)
    raise

