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
app.mount("/", StaticFiles(directory="static", html=True), name="static")
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
        body {
            margin: 0;
            font-family: system-ui, Arial;
            background: linear-gradient(135deg, #f8fafc, #eef2ff);
        }

        .container {
            max-width: 650px;
            margin: 60px auto;
            background: #ffffff;
            padding: 30px;
            border-radius: 14px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.08);
        }

        h1 {
            margin-top: 0;
            text-align: center;
        }

        .subtitle {
            text-align: center;
            color: #555;
            margin-bottom: 25px;
        }

        input {
            width: 100%;
            padding: 14px;
            font-size: 16px;
            border-radius: 8px;
            border: 1px solid #ccc;
            box-sizing: border-box;
        }

        button {
            width: 100%;
            padding: 14px;
            margin-top: 14px;
            font-size: 16px;
            border-radius: 8px;
            border: none;
            background: #2563eb;
            color: white;
            cursor: pointer;
        }

        button:hover {
            background: #1d4ed8;
        }

       .answer-box {
    margin-top: 25px;
    padding: 20px;
    background: #f9fafb;
    border-radius: 12px;
    border-left: 5px solid #2563eb;
    white-space: pre-wrap;
    font-size: 15px;
    line-height: 1.6;
}

.answer-box strong {
    color: #111827;
}

.answer-box h3 {
    margin-bottom: 6px;
    color: #1d4ed8;
}


        .footer {
            margin-top: 30px;
            font-size: 12px;
            color: #777;
            text-align: center;
        }
    </style>
</head>

<body>
<div class="container">
    <h1>🇮🇳 RuleMate India</h1>
    <div class="subtitle">
        Ask Indian government rules in simple language
    </div>

    <input id="q" placeholder="Example: Traffic fine for no helmet in Telangana" />
    <button onclick="ask()">Ask</button>

    <div style="font-size:12px;color:#2563eb;margin-top:14px;">
    ✔ Verified Government Rule Explanation
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


