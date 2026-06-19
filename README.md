======================================================================
         STRATEGIC AI FACT-CHECK AGENT - PRODUCTION DOCUMENTATION

1. OVERVIEW
----------------------------------------------------------------------
The Fact-Check Agent is a high-performance verification engine designed 
to protect analytical ecosystems against corporate hallucinations, outdated 
marketing metrics, and structural "Trap Documents." The system accepts 
unstructured PDF materials, extracts high-value quantifiable figures, 
queries live web indices via search telemetry, and uses a dual-stage 
LLM evaluation judge to pass final verdicts.

2. CORE SYSTEM ARCHITECTURE
----------------------------------------------------------------------
[PDF Upload] ──> [PyPDF Core Extraction] ──> [Gemini: Structured Query Generation]
                                                        │
[JSON Verdict Dashboard] <── [Gemini LLM Judge] <── [Tavily Web Search Live API]


3. ENVIRONMENT & API CONFIGURATION
----------------------------------------------------------------------
The platform requires active tokens from two cloud networks. Securely 
inject these credentials as environment variables or inside your hosting 
provider's production secrets manager:

  * GEMINI_API_KEY : Acquired via Google AI Studio. Powering the native 
                     2.5 Flash semantic mapping and logical arbitration.
                     
  * TAVILY_API_KEY : Acquired via Tavily AI. Acts as the search engine 
                     API layer providing clean web data context.

For local runtime operations, create a directory path at `.streamlit/secrets.toml`
and format as follows:
GEMINI_API_KEY = "your_actual_gemini_key_here"
TAVILY_API_KEY = "your_actual_tavily_key_here"


4. STEP-BY-STEP PRODUCTION DEPLOYMENT GUIDE (STREAMLIT CLOUD)
----------------------------------------------------------------------
Step 1: Commit code files (`app.py`, `requirements.txt`) directly into a 
        public or private GitHub repository.
Step 2: Authenticate into the dashboard at https://share.streamlit.io/
Step 3: Click "Create App", link your repository branch, and specify 
        `app.py` as your main file path.
Step 4: BEFORE deploying, open the "Advanced Settings" drawer.
Step 5: Paste your secret keys into the TOML text field exactly as mapped 
        in section 3 above.
Step 6: Click "Deploy". The engine will automatically install required 
        dependencies and supply a live, public testing URL.


5. EVALUATION AND BEHAVIOR AGAINST "TRAP DOCUMENTS"
----------------------------------------------------------------------
When evaluating deceptive text surfaces containing fabricated metrics:
  - VERIFIED: Applied if the target number fully matches current live reality.
  - INACCURATE: Applied if data exists but uses outdated or twisted timelines.
  - FALSE: Applied if the stat is a complete hallucination or flatly denied online.

The dashboard instantly computes an aggregative summary score (Verified vs. 
Inaccurate vs. False counts) before presenting the granular deep dive.
======================================================================
