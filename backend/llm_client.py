"""
Tiny Ollama/Mistral client.
Swap the prompt strings below with your thesis-best prompts anytime.
"""

import os
import requests
from typing import List, Tuple

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "mistral")

# --- PROMPTS (replace later with your Jupyter winners) ---

# --- Thesis-based Few-Shot Prompt for FR Classification ---
FEW_SHOT_EXAMPLES_FR = [
    {"review": "the current fb app is not good at all for tabs with big screen", "classification": "Bug Report"},
    {"review": "the problem is with the way items displaypics are smalllarge empty space etc the display generally not attractive", "classification": "Bug Report"},
    {"review": "not to mention it force closes often", "classification": "Bug Report"},
    {"review": "it should have multi tabs", "classification": "Feature Request"},
    {"review": "i use my phone almost exclusivly to log into fb and not being able to delete or edit comments is unacceptable", "classification": "Feature Request"},
    {"review": "cant turn off location tracking", "classification": "Feature Request"},
    {"review": "my biggest pet peeve is that i cant like", "classification": "Feature Request"},
    {"review": "But why does it take up 27 MB of RAM on my Galaxy Nexus", "classification": "Other"},
    {"review": "I often find myself accidentally deleting words", "classification": "Other"}
]

formatted_few_shot_text_fr = ""
for ex in FEW_SHOT_EXAMPLES_FR:
    formatted_few_shot_text_fr += f"App Review Segment: {ex['review']}\nClassification: {ex['classification']}\n\n"

CLASSIFY_PROMPT = f"""
You are an expert in software requirements analysis, specializing in user feedback. Your task is to precisely classify the provided app review segment into one of the following functional requirement categories: 'Feature Request', 'Bug Report', or 'Other'.

**DEFINITIONS:**
* **Feature Request**: This category is for user feedback that clearly suggests a NEW functionality, an enhancement, or an improvement to existing features that are NOT currently broken or causing an error.
* **Bug Report**: This category is for user feedback that describes an ERROR, FAULT, FLAW, or UNINTENDED BEHAVIOR in the app. It highlights something that is BROKEN or not working as designed.
* **Other**: This category is for general feedback, compliments, complaints that are not specific enough to be a bug or feature, questions, or irrelevant comments.

**EXAMPLES:**
{formatted_few_shot_text_fr}

**INSTRUCTIONS:**
1.  Read the "App Review Segment" carefully.
2.  Based on the definitions and examples, determine which of the three categories it most accurately fits.
3.  Your final output MUST be only the category name (e.g., 'Feature Request'), without any additional text, explanation, or punctuation.

**App Review Segment:** '''{{text}}'''

**Classification:**
"""

# --- Thesis-based Chain-of-Thought Prompt for NFR Classification ---
NFR_COT_PROMPT = """
You are a highly skilled software requirements expert, specializing in non-functional requirements (NFRs). Your task is to accurately classify a given user review into one of the following NFR types.

**NFR Categories:**
- Usability (US): How easy the system is to use, learn, and its user interface.
- Reliability (RL): The system's ability to perform consistently without failure, its uptime, and data recovery.
- Performance (PE): The system's speed, responsiveness, efficiency, throughput, and resource consumption.
- Portability (PO): How easily the system can be adapted or moved to different operating environments, platforms, or devices.
- Security (SE): Protection of data from unauthorized access, attacks, ensuring privacy and data integrity.
- Other (OT): Any review that does not fit clearly into the above specific NFR categories.

**Instructions:**
1. Read the 'User Review' carefully.
2. In a brief, step-by-step reasoning, analyze the review. What core concern is the user expressing? Does it relate to ease of use, stability, speed, compatibility, or data protection? Explain your reasoning process.
3. Based on your reasoning, determine the single best NFR category from the 'NFR Categories' list.
4. State your final classification clearly, preceded by "FINAL CLASSIFICATION:".
5. Your final output for classification MUST be only the two-letter abbreviation for the category, followed by a colon and the full category name (e.g., 'US: Usability', 'RL: Reliability', 'OT: Other'). Do NOT include any other text, explanation, or punctuation after "FINAL CLASSIFICATION:".

**User Review:** '''{review_text}'''

**Thinking Process:**
"""

# --- Thesis-based Constraint-Based Prompt for SRS Generation ---
SRS_PROMPT = """
Based on the following classified user feedback, generate a comprehensive Software Requirements Specification (SRS) document.

Classified Feedback:
{bullet_list}

Generate a well-structured SRS document that includes the following sections, using clear and concise language:
1. Introduction and Purpose
2. System Overview
3. Functional Requirements
4. Non-Functional Requirements
5. System Features
6. External Interfaces
7. Performance Requirements
8. Design Constraints

Crucially, ensure the generated SRS is coherent, logically organized, and directly addresses the classified feedback provided. **STRICTLY avoid including any implementation details, specific design solutions, or technical jargon that is not directly inferable from the user feedback. Each requirement must be unique and non-redundant. Ensure all requirements are stated in a clear, testable, and unambiguous manner.**
"""

# ------------- Core LLM helpers -------------

def _ask(prompt: str, timeout: int = 60) -> str:
    resp = requests.post(
        f"{OLLAMA_URL.rstrip('/')}/api/generate",
        json={"model": MODEL, "prompt": prompt, "stream": False},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json().get("response", "").strip()

def classify_feedback(line: str) -> Tuple[str, str]:
    """Return (label, reason) with label in {'Bug','Feature','Other'}."""
    out = _ask(CLASSIFY_PROMPT.format(text=line))
    low = out.lower().strip()
    
    # Map the new thesis-level output format to the expected labels
    if low.startswith("bug report") or low.startswith("bug"):
        label = "Bug"
    elif low.startswith("feature request") or low.startswith("feature"):
        label = "Feature"
    else:
        label = "Other"
    
    # For the new format, the output is just the classification, so use the original text as reason
    reason = line
    return label, reason

def classify_nfr_feedback(line: str) -> Tuple[str, str]:
    """Return (nfr_type, reasoning) for non-functional requirement classification."""
    out = _ask(NFR_COT_PROMPT.format(review_text=line))
    
    # Extract the final classification from the chain-of-thought output
    lines = out.split('\n')
    nfr_type = "OT: Other"  # Default
    reasoning = line
    
    for line in lines:
        if line.startswith("FINAL CLASSIFICATION:"):
            nfr_type = line.replace("FINAL CLASSIFICATION:", "").strip()
            break
    
    return nfr_type, reasoning

def generate_srs(items: List[Tuple[str, str, str]]) -> str:
    """
    items: [(review, label, reason)]
    Returns plain-text SRS.
    """
    # Keep it compact; you can change the shape if your SRS prompt prefers.
    bullets = "\n".join([f"- [{lbl}] {rev}" for (rev, lbl, _reason) in items])
    return _ask(SRS_PROMPT.format(bullet_list=bullets))

# --- SRS → User Stories helpers ---
from typing import List
import re, unicodedata

def extract_requirement_lines(srs_text: str) -> List[str]:
    s = srs_text.replace("\x00", "")
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("**", "")

    lines = s.splitlines()

    # Track which numbered section we're in (e.g., "3. Functional Requirements")
    current_section = None
    reqs: List[str] = []

    section_re = re.compile(r"^\s*(\d+)\.\s*(.+?)\s*$")
    bullet_re  = re.compile(r"^\s*-\s+(.*\S)\s*$")
    strip_tag  = re.compile(r"\s*\[(?:Bug|Feature|Other)\]\s*$", re.I)

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        # Heading like "3. Functional Requirements"
        m = section_re.match(line)
        if m:
            current_section = m.group(2).strip().lower()
            continue

        # Only capture bullets while we're *inside* Functional Requirements
        if current_section and "functional requirements" in current_section:
            mb = bullet_re.match(line)
            if mb:
                item = strip_tag.sub("", mb.group(1)).strip()
                item = " ".join(item.split())
                if item:
                    reqs.append(item)

    # Fallback: also accept "1.1. Something..." anywhere
    if not reqs:
        numbered = []
        for raw in lines:
            line = raw.strip()
            m = re.match(r"^\s*\d+(?:\.\d+)+\.?\s+(.*\S)$", line)
            if m:
                numbered.append(" ".join(m.group(1).split()))
        if numbered:
            reqs = numbered

    # De-dup case-insensitively
    seen, out = set(), []
    for r in reqs:
        key = r.lower()
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out

def srs_to_user_stories(srs_text: str, max_stories: int = 50) -> List[str]:
    """
    Convert extracted SRS requirements into user stories:
    "As a <user>, I want <goal> so that <reason>."
    One story per requirement. No invented features.
    """
    req_lines = extract_requirement_lines(srs_text)
    if not req_lines:
        return []

    prompt = (
        "You are a requirements analyst.\n"
        "Convert the following software requirements into concise user stories.\n"
        'Each story must follow exactly: As a <type of user>, I want <goal> so that <reason>.\n'
        "Do not invent features; do not merge or split items; one story per requirement.\n"
        "Aim for 12–20 words per story.\n\n"
        "Requirements:\n"
        + "\n".join(f"- {req}" for req in req_lines) +
        "\n\nOutput as a numbered list:\n"
        "1. As a ...\n2. As a ...\n"
    )

    raw = _ask(prompt)

    # Parse numbered/bulleted outputs
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    stories = []
    for ln in lines:
        ln = re.sub(r"^[\d\.\-\)\(\s•*]+", "", ln)
        if ln.lower().startswith("as a ") and " i want " in ln.lower():
            stories.append(" ".join(ln.split())[:280])

    # de-dup and cap
    seen, out = set(), []
    for s in stories:
        k = s.lower()
        if k not in seen:
            seen.add(k)
            out.append(s)
        if len(out) >= max_stories:
            break
    return out
