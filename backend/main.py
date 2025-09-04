from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from llm_client import classify_feedback, generate_srs
from jira_client import create_issue
from fastapi import Body
from llm_client import srs_to_user_stories

app = FastAPI(title="ReqTool MVP", version="0.1")

# Dev-friendly CORS; lock down later if needed
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

def labels_for_item(kind: str, subtype: str | None) -> list[str]:
    labs = []
    k = (kind or "").lower()
    if k == "bug":
        labs += ["bug"]
    elif k in ("feature", "fr", "functional requirement"):
        labs += ["feature"]
    elif k in ("nfr", "non-functional requirement"):
        labs += ["nfr"]
        if subtype:
            labs += [f"nfr-{subtype.lower().replace(' ', '-') }"]
    else:
        labs += ["other"]
    return labs

@app.get("/")
def health():
    import os
    jira_vars = {
        "JIRA_URL": os.getenv("JIRA_URL"),
        "JIRA_EMAIL": os.getenv("JIRA_EMAIL"), 
        "JIRA_API_TOKEN": "***" if os.getenv("JIRA_API_TOKEN") else None,
        "JIRA_PROJECT_KEY": os.getenv("JIRA_PROJECT_KEY")
    }
    return {"ok": True, "service": "ReqTool MVP", "jira_config": jira_vars}

@app.post("/process")
async def process_txt(file: UploadFile = File(...)):
    if not file.filename.endswith(".txt"):
        raise HTTPException(400, "Please upload a .txt file")

    raw = await file.read()
    
    # Try UTF-8 first; if nulls/BOM suggest UTF-16, decode accordingly
    try:
        content = raw.decode("utf-8")
        if "\x00" in content:  # likely UTF-16 uploaded as .txt
            content = raw.decode("utf-16", errors="ignore")
    except UnicodeDecodeError:
        # Fallbacks: UTF-16 LE/BE or Latin-1
        try:
            content = raw.decode("utf-16", errors="ignore")
        except Exception:
            content = raw.decode("latin-1", errors="ignore")

    # Final cleanup
    content = content.replace("\x00", "").strip()
    lines = [l.strip() for l in content.splitlines() if len(l.strip()) >= 3]
    if not lines:
        raise HTTPException(400, "No reviews found in file")

    classifications = []
    summary = {"Bug": 0, "Feature": 0, "Other": 0}

    for ln in lines:
        label, reason = classify_feedback(ln)
        summary[label] += 1
        classifications.append({
            "review": ln,
            "classification": label,
            "reasoning": reason
        })

    srs_text = generate_srs([(c["review"], c["classification"], c["reasoning"])
                             for c in classifications])

    return {
        "total_reviews": len(lines),
        "classification_summary": summary,
        "classifications": classifications,
        "srs_document": srs_text
    }

class JiraItem(BaseModel):
    review: str
    classification: str        # "Bug" | "Feature" | "Other"
    reasoning: Optional[str]=None

class JiraRequest(BaseModel):
    items: List[JiraItem]

@app.post("/jira/create")
def jira_create(req: JiraRequest):
    created, failed = [], []
    for it in req.items:
        itype = "Bug" if it.classification=="Bug" else ("Story" if it.classification=="Feature" else "Task")
        try:
            key = create_issue(summary=it.review, description=(it.reasoning or ""), issuetype=itype)
            created.append({"key":key, "summary":it.review})
        except Exception as e:
            failed.append({"summary":it.review, "error":str(e)})
    return {"created":created, "failed":failed}

@app.post("/jira/send-first")
def jira_send_first(payload: dict = Body(...)):
    items = payload.get("classifications", [])
    if not items:
        return {"error": "No classifications to send"}
    first = items[0]
    summary = first.get("review", "")
    desc = first.get("reasoning", "")
    classification = first.get("classification") or first.get("fr_nfr") or "Task"
    return create_issue(summary, desc, classification)

# Note: Keeping the old debug endpoint for compatibility, but it may not work with the new jira_client
# You can remove it if you don't need it anymore

@app.post("/stories/generate")
def generate_stories(payload: dict = Body(...)):
    """
    Input: { "srs_document": "<text>" }
    Output: { "stories": [ "...", "..." ] }
    """
    srs = payload.get("srs_document", "")
    if not srs:
        return {"error": "Missing srs_document"}
    stories = srs_to_user_stories(srs)
    return {"stories": stories}

@app.post("/jira/send-selected")
def jira_send_selected(payload: dict = Body(...)):
    """
    Input: { "stories": [ { "user_story": "...", "classification": "Feature|Bug|NFR|..." } ] }
    Output: { "created": [{key,summary}], "failed":[{title,error}] }
    """
    items = payload.get("stories", [])
    if not items:
        return {"error": "No stories provided"}
    if len(items) > 10:
        return {"error": "Cannot send more than 10 stories at once"}

    created, failed = [], []
    for it in items:
        story = (it.get("user_story") or "").strip()
        classification = it.get("classification") or "Feature"
        if not story:
            failed.append({"title": "", "error": "Empty story"})
            continue
        res = create_issue(summary=story, description=story, classification=classification)
        if "key" in res:
            created.append(res)
        else:
            failed.append({"title": story, "error": res.get("error","Unknown error")})
    return {"created": created, "failed": failed}

# Run with: uvicorn main:app --reload --port 8001

@app.post("/jira/send-selected-classifications")
def jira_send_selected_classifications(payload: dict = Body(...)):
    """
    Input: { "items": [ { "review": "...", "classification":"Bug|Feature|Other|FR|NFR",
                          "subtype": "Performance|Usability|..." (optional),
                          "reasoning": "..." } ] }
    Output: { "created":[{key,summary}], "failed":[{title,error}] }
    """
    items = payload.get("items", [])
    if not items:
        return {"error": "No items provided"}
    if len(items) > 10:
        return {"error": "Cannot send more than 10 items at once"}

    created, failed = [], []
    for it in items:
        summary = (it.get("review") or "").strip()
        if not summary:
            failed.append({"title": "", "error": "Empty review"})
            continue
        kind = it.get("classification") or it.get("fr_nfr") or "Feature"
        subtype = it.get("subtype")
        labels = labels_for_item(kind, subtype)

        # Optional: summary prefix to make intent obvious in Jira list views
        prefix = "[BUG]" if "bug" in labels else ("[NFR]" if "nfr" in labels else "[FEATURE]")
        res = create_issue(
            summary=f"{prefix} {summary}",
            description=it.get("reasoning") or summary,
            labels=labels
        )
        (created if "key" in res else failed).append(res if "key" in res else {"title": summary, "error": res["error"]})
    return {"created": created, "failed": failed}
