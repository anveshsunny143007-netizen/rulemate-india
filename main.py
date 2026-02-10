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
<!DOCTYPE html>
<html>
<head>
    <title>Indian Government Rules Explained Simply | RuleMate India</title>
    <meta name="description" content="Ask Indian government rules, IPC sections, fines, punishments and legal procedures in simple language. Trusted rule explainer for India.">

    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
        <style>
    :root {
        --primary: #2563eb;
        --bg: #f8fafc;
        --card: #ffffff;
        --text: #0f172a;
        --muted: #475569;
    }

    * {
        box-sizing: border-box;
    }

    body {
        margin: 0;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto;
        background: linear-gradient(180deg, #f1f5f9, #ffffff);
        color: var(--text);
    }

    .container {
        max-width: 720px;
        margin: 70px auto;
        background: var(--card);
        padding: 36px;
        border-radius: 18px;
        box-shadow: 0 25px 60px rgba(0,0,0,0.08);
    }

    h1 {
        text-align: center;
        margin-bottom: 6px;
        font-size: 32px;
        letter-spacing: -0.5px;
    }

    .subtitle {
        text-align: center;
        color: var(--muted);
        margin-bottom: 30px;
        font-size: 15px;
    }

    input {
        width: 100%;
        padding: 16px;
        font-size: 16px;
        border-radius: 10px;
        border: 1px solid #cbd5f5;
        outline: none;
    }

    input:focus {
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(37,99,235,0.15);
    }

    button {
        width: 100%;
        padding: 15px;
        margin-top: 14px;
        font-size: 16px;
        border-radius: 10px;
        border: none;
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: white;
        cursor: pointer;
        font-weight: 600;
    }

    button:hover {
        opacity: 0.95;
    }

    .trust {
        margin-top: 14px;
        font-size: 13px;
        color: #2563eb;
        text-align: center;
        font-weight: 500;
    }

    .answer-box {
        margin-top: 30px;
        padding: 24px;
        background: #f9fafb;
        border-radius: 14px;
        border-left: 5px solid var(--primary);
        white-space: pre-wrap;
        font-size: 15px;
        line-height: 1.7;
    }

    .answer-box strong {
        color: #020617;
    }

    #related {
        margin-top: 20px;
        font-size: 14px;
    }

    .footer {
        margin-top: 40px;
        font-size: 12px;
        color: #64748b;
        text-align: center;
        line-height: 1.6;
    }

    @media (max-width: 640px) {
        .container {
            margin: 30px 14px;
            padding: 24px;
        }
    }
</style>

</head>

<body>
<div class="container">
    <h1>🇮🇳 RuleMate India</h1>
    <div class="subtitle">
        Simple explanations of Indian government rules, laws, fines and procedures
    </div>

    <input id="q" placeholder="Example: Traffic fine for no helmet in Telangana" />
    <button onclick="ask()">Ask</button>

    <div class="trust">
    ✔ Educational explanation based on Indian government laws
</div>


<div class="answer-box" id="a"></div>
<div id="related" style="margin-top:18px;font-size:14px;"></div>

    <div style="margin-top:30px;font-size:13px;color:#555;">
    <b>About RuleMate India</b><br>
    RuleMate India helps people understand Indian government rules, laws,
    fines and procedures in simple language.
</div>

    <div class="footer">
    <b>Disclaimer:</b><br>
    This website provides general information on Indian government rules and laws
    for educational purposes only. It is not legal advice.
    Laws and rules may change. Always verify with official government notifications
    or consult a qualified professional.
</div>


<script>
function setQuestion(text) {
    document.getElementById("q").value = text;
    ask();
}

async function ask() {
    const q = document.getElementById("q").value;
    document.getElementById("a").innerText = "Thinking...";
    document.getElementById("related").innerHTML = "";

    const r = await fetch("/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q })
    });

    const d = await r.json();
    document.getElementById("a").innerText = d.answer;
    let html = "<b>🔍 Related questions</b><br>";
d.related.forEach(r => {
    if (r.trim() !== "") {
        const safe = r.replace(/'/g, "");
        html += `<div style="margin-top:6px; cursor:pointer; color:#2563eb;" onclick="setQuestion('${safe}')">• ${r}</div>`;
    }
});
document.getElementById("related").innerHTML = html;

const url = "/" + d.slug;
window.history.pushState({}, "", url);


    
}


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



