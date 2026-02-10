import os
import re
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

# 1. Configuration & Setup
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

SYSTEM_PROMPT = """
You are an Indian Government Rules Assistant.

STRICT RULES:
- Answer ONLY Indian government rules, laws, schemes, IPC sections.
- Use simple language.
- Do NOT give opinions.
- Do NOT guess.
- If unsure, say so clearly.

FORMAT EVERY ANSWER EXACTLY LIKE THIS:

SHORT ANSWER:
(one clear sentence)

DETAILS:
- Bullet point
- Bullet point

PUNISHMENT / IMPLICATIONS (if applicable):
- Bullet point

SOURCE:
- Name of Act / Department (example: Indian Penal Code, Motor Vehicles Act, NPCI)

NOTE:
- Rules may change. Always verify with official government notification.
"""

# 2. Helper Functions & Models
class Question(BaseModel):
    question: str

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', '', text)
    text = text.strip().replace(' ', '-')
    return text

# 3. Routes

@app.get("/sitemap.xml")
def sitemap():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url>
<loc>https://rulemate-india.onrender.com/</loc>
<changefreq>daily</changefreq>
<priority>1.0</priority>
</url>
</urlset>
"""
    return Response(content=xml, media_type="application/xml")

@app.post("/ask")
def ask_rule(q: Question):
    # Main answer
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": q.question}
        ],
        temperature=0.2
    )

    answer = response.choices[0].message.content
    slug = slugify(q.question)

    # Related questions
    related_prompt = f"""
Based on this question: "{q.question}"
Generate 4 related follow-up questions.
Return ONLY the questions, one per line.
"""

    related_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You generate related Indian government rule questions."},
            {"role": "user", "content": related_prompt}
        ],
        temperature=0.4
    )

    related = [
        r.strip("- ").strip()
        for r in related_response.choices[0].message.content.split("\n")
        if r.strip()
    ]

    return {
        "answer": answer,
        "slug": slug,
        "related": related
    }

@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<title>RuleMate India | AI Government Rules Assistant</title>
<meta name="description" content="Ask Indian government rules, IPC sections, fines, punishments and legal procedures in simple language. Trusted rule explainer for India.">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
<style>
    :root {
        --bg-color: #0f172a;
        --card-bg: #1e293b;
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --accent-color: #3b82f6;
        --accent-hover: #2563eb;
        --glow: 0 0 20px rgba(59, 130, 246, 0.5);
    }

    body {
        margin: 0;
        font-family: 'Inter', sans-serif;
        background-color: var(--bg-color);
        color: var(--text-primary);
        display: flex;
        flex-direction: column;
        min-height: 100vh;
        align-items: center;
    }

    /* Background decoration */
    body::before {
        content: "";
        position: fixed;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle at center, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 1) 70%);
        z-index: -1;
    }

    .container {
        width: 100%;
        max-width: 700px;
        margin-top: 80px;
        padding: 20px;
        box-sizing: border-box;
        text-align: center;
    }

    h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 10px;
        background: linear-gradient(90deg, #fff, #94a3b8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1px;
    }

    .subtitle {
        color: var(--text-secondary);
        font-size: 1.1rem;
        margin-bottom: 40px;
        font-weight: 300;
    }

    .search-box {
        position: relative;
        background: rgba(30, 41, 59, 0.6);
        padding: 10px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    input {
        width: 100%;
        padding: 16px;
        font-size: 16px;
        background: transparent;
        border: none;
        color: white;
        outline: none;
        box-sizing: border-box;
    }

    input::placeholder {
        color: rgba(148, 163, 184, 0.6);
    }

    button {
        width: 100%;
        padding: 14px;
        font-size: 16px;
        font-weight: 600;
        border-radius: 12px;
        border: none;
        background: var(--accent-color);
        color: white;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: var(--glow);
    }

    button:hover {
        background: var(--accent-hover);
        transform: translateY(-2px);
        box-shadow: 0 0 30px rgba(59, 130, 246, 0.7);
    }

    /* Verification Badge */
    .badge {
        display: inline-block;
        margin-top: 20px;
        padding: 6px 12px;
        font-size: 12px;
        color: #60a5fa;
        background: rgba(59, 130, 246, 0.1);
        border-radius: 20px;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }

    /* Answer Area */
    .answer-box {
        margin-top: 30px;
        text-align: left;
        background: rgba(30, 41, 59, 0.4);
        padding: 25px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        display: none; /* Hidden by default */
        animation: fadeIn 0.5s ease-in-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .answer-box strong {
        color: #fff;
    }

    .answer-box h3 {
        color: var(--accent-color);
        margin-top: 0;
    }

    /* Related Questions */
    #related {
        margin-top: 20px;
        text-align: left;
    }

    .related-item {
        background: rgba(255, 255, 255, 0.03);
        padding: 12px 16px;
        margin-top: 8px;
        border-radius: 8px;
        cursor: pointer;
        color: var(--text-secondary);
        transition: all 0.2s;
        border: 1px solid transparent;
        font-size: 14px;
    }

    .related-item:hover {
        background: rgba(255, 255, 255, 0.07);
        color: white;
        border-color: rgba(255, 255, 255, 0.1);
    }

    .footer {
        margin-top: auto;
        padding: 40px 20px;
        font-size: 12px;
        color: #475569;
        text-align: center;
        line-height: 1.5;
        max-width: 500px;
    }

    /* Mobile tweaks */
    @media (max-width: 600px) {
        .container { margin-top: 40px; }
        h1 { font-size: 2rem; }
    }
</style>
</head>

<body>

    <div class="container">
        <h1>🇮🇳 RuleMate India</h1>
        <div class="subtitle">Ask any Indian government rule in simple language.</div>

        <div class="search-box">
            <input id="q" placeholder="Type your question here... (e.g. Traffic fine for no helmet)" />
            <button onclick="ask()">Ask AI</button>
        </div>

        <div class="badge">✔ Verified Government Sources</div>

        <div class="answer-box" id="a"></div>
        <div id="related"></div>
    </div>

    <div class="footer">
        <b>Disclaimer:</b><br>
        RuleMate India provides general information for educational purposes only. 
        It is not legal advice. Always verify with official government notifications.
    </div>

<script>
    function setQuestion(text) {
        document.getElementById("q").value = text;
        ask();
    }

    async function ask() {
        const q = document.getElementById("q").value;
        if (!q) return; 
        
        const answerBox = document.getElementById("a");
        const relatedBox = document.getElementById("related");
        const btn = document.querySelector("button");

        // UI Loading State
        btn.innerText = "Searching...";
        btn.style.opacity = "0.7";
        answerBox.style.display = "block";
        answerBox.innerHTML = "<div style='color:#94a3b8'>Thinking...</div>";
        relatedBox.innerHTML = "";

        try {
            const r = await fetch("/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question: q })
            });

            const d = await r.json();
            
            // Render Answer
            answerBox.innerHTML = d.answer.replace(/\\n/g, "<br>");
            
            // Render Related Questions
            let html = "";
            if(d.related.length > 0) {
                html += "<div style='margin-top:20px; color:#64748b; font-size:13px; font-weight:600; text-transform:uppercase; letter-spacing:1px;'>Related Questions</div>";
                d.related.forEach(r => {
                    if (r.trim() !== "") {
                        const safe = r.replace(/'/g, "");
                        html += `<div class="related-item" onclick="setQuestion('${safe}')">${r}</div>`;
                    }
                });
            }
            relatedBox.innerHTML = html;

            // Update URL
            const url = "/" + d.slug;
            window.history.pushState({}, "", url);

        } catch (error) {
            answerBox.innerText = "Error fetching answer. Please try again.";
        } finally {
            btn.innerText = "Ask AI";
            btn.style.opacity = "1";
        }
    }
</script>
</body>
</html>
"""

# Dynamic Route (Must be last to avoid conflicts)
@app.get("/{slug}", response_class=HTMLResponse)
def dynamic_page(slug: str):
    return home()
