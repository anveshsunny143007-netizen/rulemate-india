import re
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()
from fastapi.responses import Response
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

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', '', text)
    text = text.strip().replace(' ', '-')
    return text


class Question(BaseModel):
    question: str

@app.get("/", response_class=HTMLResponse)
def home():
    return """
return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>

<meta name="description" content="Understand Indian government rules, laws, fines and procedures in simple language. RuleMate India explains IPC, traffic rules and legal procedures clearly.">
<meta name="viewport" content="width=device-width, initial-scale=1">

<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

<style>
* {{
    box-sizing: border-box;
    font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont;
}}

body {{
    margin: 0;
    background: radial-gradient(circle at top, #eef2ff, #f8fafc);
    color: #0f172a;
}}

.hero {{
    max-width: 900px;
    margin: 80px auto;
    padding: 50px;
    background: rgba(255,255,255,0.75);
    backdrop-filter: blur(14px);
    border-radius: 28px;
    box-shadow: 0 30px 80px rgba(0,0,0,0.12);
    text-align: center;
}}

.hero h1 {{
    font-size: 44px;
    font-weight: 800;
    margin-bottom: 10px;
}}

.hero p {{
    font-size: 18px;
    color: #475569;
    margin-bottom: 35px;
}}

.search-box {{
    display: flex;
    gap: 12px;
    margin-bottom: 18px;
}}

.search-box input {{
    flex: 1;
    padding: 18px;
    font-size: 16px;
    border-radius: 14px;
    border: 1px solid #c7d2fe;
    outline: none;
}}

.search-box button {{
    padding: 18px 28px;
    border-radius: 14px;
    border: none;
    background: linear-gradient(135deg, #2563eb, #1e40af);
    color: white;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
}}

.search-box button:hover {{
    transform: translateY(-1px);
}}

.trust {{
    margin-top: 10px;
    font-size: 14px;
    color: #2563eb;
    font-weight: 500;
}}

.answer-box {{
    margin-top: 30px;
    padding: 28px;
    background: white;
    border-radius: 20px;
    box-shadow: 0 20px 50px rgba(0,0,0,0.08);
    border-left: 6px solid #2563eb;
    white-space: pre-wrap;
    line-height: 1.7;
    text-align: left;
}}

.section {{
    max-width: 900px;
    margin: 60px auto;
    padding: 0 20px;
}}

.cards {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 20px;
}}

.card {{
    background: white;
    padding: 24px;
    border-radius: 20px;
    box-shadow: 0 15px 40px rgba(0,0,0,0.08);
}}

.card h3 {{
    margin-top: 0;
    font-size: 18px;
}}

.footer {{
    max-width: 900px;
    margin: 60px auto 40px;
    font-size: 13px;
    color: #475569;
    text-align: center;
}}
</style>
</head>

<body>

<div class="hero">
    <h1>🇮🇳 RuleMate India</h1>
    <p>Simple explanations of Indian government rules, laws, fines and procedures</p>

    <div class="search-box">
        <input id="q" placeholder="Example: Traffic fine for no helmet in Telangana">
        <button onclick="ask()">Ask</button>
    </div>

    <div class="trust">✔ Educational explanation based on Indian government laws</div>

    <div id="a" class="answer-box" style="display:none;"></div>
    <div id="related" style="margin-top:20px;"></div>
</div>

<div class="section">
    <h2>Why RuleMate India?</h2>
    <div class="cards">
        <div class="card">
            <h3>🚦 Traffic Rules</h3>
            <p>Understand fines, penalties and driving rules clearly.</p>
        </div>
        <div class="card">
            <h3>⚖ IPC & Laws</h3>
            <p>Simple breakdown of Indian Penal Code sections.</p>
        </div>
        <div class="card">
            <h3>📄 Legal Procedures</h3>
            <p>Know what to do and how government processes work.</p>
        </div>
    </div>
</div>

<div class="footer">
<b>Disclaimer:</b><br>
This website provides general information on Indian government rules and laws for educational purposes only.
It is not legal advice. Laws may change. Always verify with official government notifications.
</div>

<script>
function setQuestion(text) {{
    document.getElementById("q").value = text;
    ask();
}}

async function ask() {{
    const q = document.getElementById("q").value;
    const box = document.getElementById("a");
    box.style.display = "block";
    box.innerText = "Thinking...";

    const r = await fetch("/ask", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{ question: q }})
    }});

    const d = await r.json();
    box.innerText = d.answer;

    let html = "<b>Related questions</b><br>";
    d.related.forEach(r => {{
        if (r.trim() !== "") {{
            const safe = r.replace(/'/g, "");
            html += `<div style="margin-top:8px;color:#2563eb;cursor:pointer" onclick="setQuestion('${safe}')">• ${r}</div>`;
        }}
    }});
    document.getElementById("related").innerHTML = html;

    window.history.pushState({{}}, "", "/" + d.slug);
}}
</script>

</body>
</html>
"""

@app.get("/{slug}", response_class=HTMLResponse)
def dynamic_page(slug: str):
    return home()

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

from fastapi.responses import Response

@app.get("/sitemap.xml", response_class=Response)
def sitemap():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://rulemate-india.onrender.com/</loc>
    <priority>1.0</priority>
  </url>
</urlset>
"""
    return Response(content=xml, media_type="application/xml")


from fastapi.responses import Response

@app.get("/sitemap.xml", response_class=Response)
def sitemap():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://rulemate-india.onrender.com/</loc>
    <priority>1.0</priority>
  </url>
</urlset>
"""
    return Response(content=xml, media_type="application/xml")




