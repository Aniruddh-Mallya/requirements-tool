import { useState } from "react";
import { processFile, sendSelectedClassificationsToJira } from "./api";
import type { Result } from "./api";

export default function App() {
  const [busy, setBusy] = useState(false);
  const [data, setData] = useState<Result | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [log, setLog] = useState<string>("");
  const [stories, setStories] = useState<string[]>([]);
  const [selectedStories, setSelectedStories] = useState<Set<number>>(new Set());
  const [selectedClassifications, setSelectedClassifications] = useState<Set<number>>(new Set());

  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const input = e.currentTarget;                 // capture before any await
    const file = input.files?.[0];
    if (!file) return;

    if (!file.name.endsWith(".txt")) {
      setError("Please upload a .txt file");
      input.value = "";                            // safe to clear here too
      return;
    }

    setError(null);
    setLog("");
    setStories([]);
    setSelectedStories(new Set());
    setSelectedClassifications(new Set());
    setBusy(true);

    try {
      const res = await processFile(file);         // after this, event is pooled
      setData(res);
    } catch (err: any) {
      setError(err?.message ?? "Upload failed");
    } finally {
      setBusy(false);
      input.value = "";                            // we stored 'input', so this is safe
    }
  }

  return (
    <div style={{maxWidth:900, margin:"2rem auto", fontFamily:"system-ui, sans-serif"}}>
      <h1>ReqTool MVP</h1>
      <input type="file" accept=".txt" onChange={onUpload} disabled={busy} />
      <button 
        onClick={async () => {
          setError(null);
          setLog("Testing Jira connection...");
          setBusy(true);
          try {
            const res = await fetch("http://localhost:8001/jira/debug");
            const data = await res.json();
            setLog(`Jira Debug:\n${JSON.stringify(data, null, 2)}`);
            if (data.error) setError(data.error);
          } catch (e: any) {
            setError(e.message);
            setLog("Debug failed.");
          } finally {
            setBusy(false);
          }
        }}
        style={{
          marginLeft: "8px",
          padding: "8px 16px",
          fontSize: "14px",
          backgroundColor: "#666",
          color: "white",
          border: "none",
          borderRadius: "4px",
          cursor: "pointer"
        }}
      >
        Test Jira
      </button>
      {busy && <p>Processing… this can take a moment.</p>}
      {log && <pre style={{marginTop:8, padding:8, border:"1px solid #ddd", borderRadius:8, whiteSpace:"pre-wrap"}}>{log}</pre>}
      {error && <p style={{color:"crimson"}}>{error}</p>}

      {data && (
        <>
          <section style={{display:"flex", gap:16, marginTop:16}}>
            <Badge label="Total" value={data.total_reviews} />
            <Badge label="Bugs" value={data.classification_summary.Bug} />
            <Badge label="Features" value={data.classification_summary.Feature} />
            <Badge label="Other" value={data.classification_summary.Other} />
          </section>

          <section style={{marginTop:24}}>
            <h2>Classifications</h2>
            <div style={{marginBottom:16}}>
              <button 
                onClick={() => setSelectedClassifications(new Set(data.classifications.map((_, i) => i)))}
                style={{
                  marginRight: "8px",
                  padding: "4px 8px",
                  fontSize: "12px",
                  backgroundColor: "#6c757d",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer"
                }}
              >
                Select All
              </button>
              <button 
                onClick={() => setSelectedClassifications(new Set())}
                style={{
                  padding: "4px 8px",
                  fontSize: "12px",
                  backgroundColor: "#6c757d",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer"
                }}
              >
                Clear All
              </button>
            </div>
            
            <ul style={{padding:0, listStyle:"none", display:"grid", gap:12}}>
              {data.classifications.map((c, i) => (
                <li key={i} style={{border:"1px solid #ddd", borderRadius:8, padding:12}}>
                  <div style={{display:"flex", alignItems:"flex-start", gap:8}}>
                    <input
                      type="checkbox"
                      checked={selectedClassifications.has(i)}
                      onChange={(e) => {
                        const newSelected = new Set(selectedClassifications);
                        if (e.target.checked) {
                          newSelected.add(i);
                        } else {
                          newSelected.delete(i);
                        }
                        setSelectedClassifications(newSelected);
                      }}
                      style={{marginTop: "4px"}}
                    />
                    <div style={{flex: 1}}>
                      <div style={{fontSize:12, opacity:.7}}>{c.classification}</div>
                      <div style={{marginTop:4}}>{c.review}</div>
                      <div style={{fontSize:12, opacity:.7, marginTop:6}}>Reason: {c.reasoning}</div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
            
            <div style={{marginTop:16}}>
              <button 
                onClick={async () => {
                  if (selectedClassifications.size === 0) {
                    setError("Please select at least one classification");
                    return;
                  }
                  if (selectedClassifications.size > 10) {
                    setError("Cannot send more than 10 classifications at once");
                    return;
                  }
                  
                  setError(null);
                  setLog(`Sending ${selectedClassifications.size} selected classifications to Jira...`);
                  setBusy(true);
                  
                  try {
                    const selectedClassificationsList = Array.from(selectedClassifications).map(index => data.classifications[index]);
                    
                    const res = await sendSelectedClassificationsToJira(selectedClassificationsList);
                    
                    if (res.created) {
                      const successCount = res.created.length;
                      const failedCount = res.failed?.length || 0;
                      setLog(`✅ Created ${successCount} Jira issues${failedCount > 0 ? `, ${failedCount} failed` : ''}`);
                      if (failedCount > 0) {
                        setError(`Failed: ${res.failed.map((f: any) => f.error).join(', ')}`);
                      }
                    } else {
                      setError(`Error: ${res.error}`);
                      setLog("Send failed.");
                    }
                  } catch (e: any) {
                    setError(e.message);
                    setLog("Send failed.");
                  } finally {
                    setBusy(false);
                  }
                }}
                disabled={selectedClassifications.size === 0 || selectedClassifications.size > 10}
                style={{
                  padding: "12px 24px",
                  fontSize: "16px",
                  backgroundColor: selectedClassifications.size > 0 ? "#28a745" : "#6c757d",
                  color: "white",
                  border: "none",
                  borderRadius: "6px",
                  cursor: selectedClassifications.size > 0 ? "pointer" : "not-allowed"
                }}
              >
                Send Selected to Jira ({selectedClassifications.size})
              </button>
            </div>
          </section>

          <section style={{marginTop:24}}>
            <h2>SRS</h2>
            <pre style={{whiteSpace:"pre-wrap", border:"1px solid #ddd", borderRadius:8, padding:12}}>
              {data.srs_document}
            </pre>
            
            <div style={{marginTop:16}}>
              <button 
                onClick={async () => {
                  setError(null);
                  setLog("Generating user stories...");
                  setBusy(true);
                  try {
                    const res = await fetch("http://localhost:8001/stories/generate", {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ srs_document: data.srs_document }),
                    });
                    const out = await res.json();
                    if (out.stories) {
                      setStories(out.stories);
                      setLog(`Generated ${out.stories.length} user stories`);
                      setError(null);
                    } else {
                      setError(`Error: ${out.error}`);
                      setLog("Story generation failed.");
                    }
                  } catch (e: any) {
                    setError(e.message);
                    setLog("Story generation failed.");
                  } finally {
                    setBusy(false);
                  }
                }}
                style={{
                  padding: "8px 16px",
                  fontSize: "14px",
                  backgroundColor: "#6f42c1",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer"
                }}
              >
                Generate User Stories
              </button>
            </div>
          </section>

          {stories.length > 0 && (
            <section style={{marginTop:24}}>
              <h2>User Stories</h2>
              <div style={{marginBottom:16}}>
                <button 
                  onClick={() => setSelectedStories(new Set(stories.map((_, i) => i)))}
                  style={{
                    marginRight: "8px",
                    padding: "4px 8px",
                    fontSize: "12px",
                    backgroundColor: "#6c757d",
                    color: "white",
                    border: "none",
                    borderRadius: "4px",
                    cursor: "pointer"
                  }}
                >
                  Select All
                </button>
                <button 
                  onClick={() => setSelectedStories(new Set())}
                  style={{
                    padding: "4px 8px",
                    fontSize: "12px",
                    backgroundColor: "#6c757d",
                    color: "white",
                    border: "none",
                    borderRadius: "4px",
                    cursor: "pointer"
                  }}
                >
                  Clear All
                </button>
              </div>
              
              <div style={{marginBottom:16}}>
                {stories.map((story, index) => (
                  <div key={index} style={{marginBottom:8, display:"flex", alignItems:"flex-start", gap:8}}>
                    <input
                      type="checkbox"
                      checked={selectedStories.has(index)}
                      onChange={(e) => {
                        const newSelected = new Set(selectedStories);
                        if (e.target.checked) {
                          newSelected.add(index);
                        } else {
                          newSelected.delete(index);
                        }
                        setSelectedStories(newSelected);
                      }}
                      style={{marginTop: "4px"}}
                    />
                    <div style={{flex: 1, fontSize: "14px"}}>{story}</div>
                  </div>
                ))}
              </div>
              
              <button 
                onClick={async () => {
                  if (selectedStories.size === 0) {
                    setError("Please select at least one story");
                    return;
                  }
                  if (selectedStories.size > 10) {
                    setError("Cannot send more than 10 stories at once");
                    return;
                  }
                  
                  setError(null);
                  setLog(`Sending ${selectedStories.size} selected stories to Jira...`);
                  setBusy(true);
                  
                  try {
                    const selectedStoriesList = Array.from(selectedStories).map(index => ({
                      review: stories[index],
                      classification: "Feature" as const, // Default classification for generated stories
                      reasoning: stories[index] // Use the story text as reasoning
                    }));
                    
                    const res = await sendSelectedClassificationsToJira(selectedStoriesList);
                    
                    if (res.created) {
                      const successCount = res.created.length;
                      const failedCount = res.failed?.length || 0;
                      setLog(`✅ Created ${successCount} Jira issues${failedCount > 0 ? `, ${failedCount} failed` : ''}`);
                      if (failedCount > 0) {
                        setError(`Failed: ${res.failed.map((f: any) => f.error).join(', ')}`);
                      }
                    } else {
                      setError(`Error: ${res.error}`);
                      setLog("Send failed.");
                    }
                  } catch (e: any) {
                    setError(e.message);
                    setLog("Send failed.");
                  } finally {
                    setBusy(false);
                  }
                }}
                disabled={selectedStories.size === 0 || selectedStories.size > 10}
                style={{
                  padding: "12px 24px",
                  fontSize: "16px",
                  backgroundColor: selectedStories.size > 0 ? "#28a745" : "#6c757d",
                  color: "white",
                  border: "none",
                  borderRadius: "6px",
                  cursor: selectedStories.size > 0 ? "pointer" : "not-allowed"
                }}
              >
                Send Selected to Jira ({selectedStories.size})
              </button>
            </section>
          )}

        </>
      )}
    </div>
  );
}

function Badge({label, value}:{label:string; value:number}) {
  return (
    <div style={{border:"1px solid #ddd", borderRadius:8, padding:"8px 12px"}}>
      <div style={{fontSize:12, opacity:.7}}>{label}</div>
      <div style={{fontSize:20, fontWeight:700}}>{value}</div>
    </div>
  );
}
