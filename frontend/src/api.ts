export type Classification = { 
  review: string; 
  classification: "Bug"|"Feature"|"Other"; 
  reasoning: string 
};

export type Result = {
  total_reviews: number;
  classification_summary: { Bug: number; Feature: number; Other: number };
  classifications: Classification[];
  srs_document: string;
};

export async function processFile(file: File): Promise<Result> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch("http://localhost:8001/process", { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function sendToJira(items: Classification[]){
  const r = await fetch("http://localhost:8001/jira/create",{
    method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({ items })
  });
  if(!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function sendOneToJira(item: Classification) {
  const res = await fetch("http://localhost:8001/jira/create", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ items: [item] })
  });

  const text = await res.text();               // capture raw text for debugging
  try {
    const data = JSON.parse(text);
    if (!res.ok) throw new Error(data.error || JSON.stringify(data));
    return data;                               // {created:[], failed:[]}
  } catch {
    throw new Error(`HTTP ${res.status}: ${text}`); // bubble exact server error
  }
}

export async function sendSelectedClassificationsToJira(items: Classification[]) {
  const res = await fetch("http://localhost:8001/jira/send-selected-classifications", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ items })
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
