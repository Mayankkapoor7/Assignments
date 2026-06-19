import streamlit as st
import os
import json
import re
from pypdf import PdfReader
from google import genai
from google.genai import types
import requests

# --- Configuration & Styling ---
st.set_page_config(page_title="Fact-Check AI Engine", page_icon="🔍", layout="wide")

st.markdown("""
<style>
    .report-card { border-radius: 8px; padding: 20px; margin-bottom: 15px; border-left: 6px solid; }
    .verified { background-color: #f0fdf4; border-color: #22c55e; color: #166534; }
    .inaccurate { background-color: #fffbeb; border-color: #f59e0b; color: #92400e; }
    .false { background-color: #fef2f2; border-color: #ef4444; color: #991b1b; }
    .badge { padding: 4px 12px; border-radius: 12px; font-weight: bold; font-size: 0.85em; display: inline-block; }
</style>
""", unsafe_allow_html=True)

# --- Initializing API Clients ---
# Looks for streamlit secrets first, drops back to local environment variables
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
TAVILY_KEY = st.secrets.get("TAVILY_API_KEY", os.getenv("TAVILY_API_KEY"))

if not GEMINI_KEY:
    st.error("Missing `GEMINI_API_KEY`. Please configure it in your environment or Streamlit Secrets.")
if not TAVILY_KEY:
    st.warning("Missing `TAVILY_API_KEY`. Real-time web verification will fall back to simulation mode.")

# Instantiate Gemini Client
ai_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

# --- Core Logic Functions ---

def extract_text_from_pdf(uploaded_file):
    """Extracts raw text data dynamically from uploaded PDF."""
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_claims(document_text):
    """Uses LLM structured generation to isolate verifiable stats, figures, and dates."""
    if not ai_client:
        return []
    
    prompt = f"""
    Analyze the following marketing/corporate text. Isolate exactly 3-6 distinct high-priority objective claims 
    (such as market stats, timelines, financial figures, growth rates, or technical metrics) that require 
    external live-web verification to confirm validity. Ignore subjective statements.
    
    Format the response as a strict JSON array where each item has exactly these fields:
    - "claim": The specific fact/stat extracted from the text.
    - "search_query": An optimized search query designed to pull up objective verification or source articles.

    Text:
    \"\"\"{document_text}\"\"\"
    """
    
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Failed to isolate document claims: {e}")
        return []

def query_live_web(query):
    """Queries live internet web indices for data matchers using Tavily."""
    if not TAVILY_KEY:
        # Fallback mocking if API key isn't setup during manual deployment test
        return "No active live engine token provided to verify real context."
        
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_KEY,
        "query": query,
        "search_depth": "advanced",
        "include_answer": True,
        "max_results": 3
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            data = res.json()
            # Combine snippets and structured answer direct from search pipeline
            context = f"Direct Answer Summary: {data.get('answer', 'N/A')}\n\n"
            context += "\n".join([f"- {r['title']}: {r['content']} (Source: {r['url']})" for r in data.get('results', [])])
            return context
    except Exception as e:
        return f"Search execution failed due to an error: {e}"
    return "No credible online corroboration discovered."

def evaluate_claim(claim_obj):
    """Verifies an isolated claim against targeted live web search context."""
    claim = claim_obj["claim"]
    query = claim_obj["search_query"]
    
    # Step 1: Run real-time live retrieval
    web_context = query_live_web(query)
    
    # Step 2: Use LLM Judge to reconcile differences
    prompt = f"""
    You are an objective, elite Truth Verification system. Evaluate whether the claim matches current 2026 realities.
    
    Claim to Check: "{claim}"
    Live Web Context Retrieved:
    \"\"\"{web_context}\"\"\"
    
    Categorize the claim into exactly one of these labels:
    - VERIFIED: The statement matches current real-world metrics perfectly.
    - INACCURATE: The claim points to real data, but uses outdated figures, mismatched years, or distorted scaling.
    - FALSE: The metric or statement is completely contradicted by real data or has zero online verification footprint.
    
    Provide your response as a strict JSON dictionary with these exact keys:
    "status": "VERIFIED" or "INACCURATE" or "FALSE"
    "analysis": "A concise, 2-sentence breakdown explaining why the claim holds this status based purely on the context."
    "real_facts": "The corrected or updated factual metric with supporting numbers. If verified, simply reaffirm the metric state."
    """
    
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        verdict = json.loads(response.text)
        verdict["claim"] = claim
        return verdict
    except Exception:
        return {
            "claim": claim,
            "status": "FALSE",
            "analysis": "Internal evaluation framework failed to process validation criteria.",
            "real_facts": "Unknown"
        }

# --- User Interface ---

st.title("🔍 Strategic AI Fact-Check Agent")
st.subheader("Automate Truth-Layer Verification of PDF Reports & Marketing Content")
st.write("Upload any PDF document. Our system will extract analytical claims, crawl the live web, and expose inaccuracies and trap data instantly.")

uploaded_file = st.file_uploader("Drop PDF report here for real-time audit", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("Step 1 of 3: Parsing file and extracting structural text layout..."):
        raw_text = extract_text_from_pdf(uploaded_file)
        
    if not raw_text.strip():
        st.error("The uploaded file contains no machine-readable textual layers. Please try a different document.")
    else:
        st.info(f"Successfully loaded document ({len(raw_text)} characters text parsed).")
        
        if st.button("Initiate Deep Audit", type="primary"):
            with st.spinner("Step 2 of 3: Processing semantic claims via Gemini..."):
                claims = extract_claims(raw_text)
                
            if not claims:
                st.warning("No high-priority statistical or verifiable claims were pinpointed inside this document structure.")
            else:
                st.success(f"Isolated {len(claims)} key quantitative statements requiring evaluation.")
                
                results = []
                progress_bar = st.progress(0)
                
                # Iterate and execute live web analysis loops per claim
                for index, c_item in enumerate(claims):
                    with st.spinner(f"Step 3 of 3: Live-searching & cross-referencing Claim #{index+1}..."):
                        evaluation = evaluate_claim(c_item)
                        results.append(evaluation)
                    progress_bar.progress((index + 1) / len(claims))
                
                # --- Metrics Dashboard Summary ---
                st.write("---")
                st.subheader("⚡ Audit Dashboard Summary")
                
                statuses = [r["status"] for r in results]
                v_count = statuses.count("VERIFIED")
                i_count = statuses.count("INACCURATE")
                f_count = statuses.count("FALSE")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Verified Claims", v_count, delta_color="normal")
                col2.metric("Outdated/Inaccurate", i_count, delta_color="inverse")
                col3.metric("Blatant Falsehoods/Traps", f_count, delta_color="inverse")
                
                # --- Granular Report Output ---
                st.write("---")
                st.subheader("📄 Deep-Dive Audit Breakdown")
                
                for res in results:
                    status_lower = res["status"].lower()
                    css_class = f"report-card {status_lower}"
                    
                    st.markdown(f"""
                    <div class="{css_class}">
                        <span class="badge">{res['status']}</span>
                        <p style="margin-top: 10px; font-weight: bold; font-size: 1.1em;">Claim Checked: "{res['claim']}"</p>
                        <p style="margin-bottom: 5px;"><strong>Analysis:</strong> {res['analysis']}</p>
                        <p style="margin-bottom: 0;"><strong>Ground-Truth Reality (2026):</strong> {res['real_facts']}</p>
                    </div>
                    """, unsafe_allow_html=True)