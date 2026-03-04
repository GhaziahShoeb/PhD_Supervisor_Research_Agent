import os
from deepagents import create_deep_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from utils.tools import internet_search, read_file, write_file

# Defensive patch for a LangChain bug where _fetch_last_ai_and_tool_messages can raise
# UnboundLocalError when no AI message is present (e.g., if a model/tool fails early).
try:
    import langchain.agents.factory as lc_factory
    from langchain_core.messages import AIMessage

    _original_model_to_tools = lc_factory.model_to_tools

    def _safe_model_to_tools(state, *args, **kwargs):
        messages = state.get("messages") or []
        if not any(isinstance(m, AIMessage) for m in messages):
            return {"messages": []}
        return _original_model_to_tools(state, *args, **kwargs)

    lc_factory.model_to_tools = _safe_model_to_tools
except Exception:
    pass

# Ensure API keys are loaded
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

# 1. Define Models
model_gemini = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0, max_retries=5)

# 2. Define the Specialized Subagent Team
subagents = [
    {
        "name": "university-shortlister",
        "description": "Shortlists universities based on the user's preferred Country, City, and Research Domain.",
        "system_prompt": (
            "You are an expert University Scout. Your goal is to identify the best universities for the user based on their specific request.\n"
            "1. Analyze the user's query to extract the target **Country** and **City** (e.g., Australia, Melbourne).\n"
            "2. Identify the **Research Domain** (e.g., AI, Computer Vision) and **Department** from the user's profile or query.\n"
            "3. Search for universities in that specific location that are top-ranked or well-regarded in that domain.\n"
            "4. Save the list of shortlisted universities to `/results/shortlist.md`.\n"
            "When using the internet_search tool, include keywords and do not use 'site:' alone."
        ),
        "tools": [internet_search, write_file],
        "model": model_gemini
    },
    {
        "name": "professor-discovery",
        "description": "Finds specific Professors/PIs in the shortlisted universities matching the user's Research Domain.",
        "system_prompt": (
            "You are an Academic Talent Sourcer. Your task is to find potential supervisors in the universities shortlisted by the 'university-shortlister'.\n"
            "1. For each university, scan the faculty directories of the relevant **Department**.\n"
            "2. Filter for faculty with the **Designation** of Professor, Associate Professor, or Assistant Professor.\n"
            "3. **Strictly** match their research interests with the user's **Research Domain** (as defined in the user's query).\n"
            "4. Save the raw profiles (Name, Email, Profile Link) to `/results/profs_raw.json`.\n"
            "When using the internet_search tool, include keywords and do not use 'site:' alone."
        ),
        "tools": [internet_search, write_file, read_file],
        "model": model_gemini
    },
    {
        "name": "professor-validator",
        "description": "Validates professors based on Grants, Publications, and PhD Openings.",
        "system_prompt": (
            "You are a Research Validator. Your job is to vet the professors found by the 'professor-discovery' agent.\n"
            "For each professor, verify the following using Internet Search:\n"
            "1. **Active Grants:** specific to the region (e.g., ARC for Australia, NSF for US, ERC for Europe) or industry funding.\n"
            "2. **Recent Publications:** Check for papers published between 2024-2026.\n"
            "3. **PhD Openings:** Check their lab website or personal page for 'Open Positions', 'Prospective Students', or 'Vacancy' notices.\n"
            "4. **Fit:** If the user provided a resume or background (e.g., B.Tech IT), assess if the professor typically hires students with that background.\n"
            "Output the validated data for the final report.\n"
            "When using the internet_search tool, include keywords and do not use 'site:' alone."
        ),
        "tools": [internet_search, read_file],
        "model": model_gemini
    }
]

# 3. Create the Main Orchestrator Agent
agent = create_deep_agent(
    model=model_gemini,
    name="academic-research-lead",
    system_prompt="""
You are the Lead Academic Coordinator. 

Your goal is to coordinate your subagents to find professors and compile a final report based on the User's specific query (Country, City, Domain).

REPORT INSTRUCTIONS:
As the research progresses, compile the findings into a file named `/results/academic_report.md`.
You MUST use the following table format for the output, filling in all columns found:

| University Name | Professor Name | Designation | Email | Research Area | Active Grants | Recent Publication | PhD Openings |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |

Use the `write_file` tool to save this report to your persistent GCS storage backend.
When using the internet_search tool, include keywords and do not use 'site:' alone.
""",
    subagents=subagents
)
