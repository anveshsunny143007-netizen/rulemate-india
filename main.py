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
<html lang="en">
<head>
<meta charset="UTF-8">
<title>RuleMate India</title>

<meta name="description" content="Understand Indian government rules, laws, fines and procedures in simple language.">
<meta name="viewport" content="width=device-width, initial-scale=1">

<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">

<style>
body {
    margin: 0;
    font-family: 'Inter', system-ui;
    background: radial-gradient(circle at top, #eef2ff, #f8fafc);
    color: #0f172a;
}
.hero {
    max-width: 900px;
    margin: 80px auto;
    padding: 50px;
    background: white;
    border-radius: 24px;
    box-shadow: 0 30px 80px rgba(0,0,0,0.12);
    text-align: center;
}
input {
    width: 100%;
    padding: 18px;
    font-size: 16px;
    border-radius: 12px;
    border: 1px solid #c7d2fe;
}
button {
    margin-top: 14px;
    padding: 18px;
    width: 100%;
    border-radius: 12px;
    border: none;
    background: #2563eb;
    color: white;
    font-size: 16px;
    font-weight: 600;
}
.answer-box {
    margin-top: 25px;
    padding: 25px;
    background: #f9fafb;
    border-radius: 16px;
    border-left: 6px solid #2563eb;
    white-space: pre-wrap;
    text-align: left;
}
</style>
</head>

<body>
<div class="hero">
<h1>🇮🇳 RuleMate India</h1>
<p>Simple explanations of Indian government rules</p>

<input id="q" placeholder="Example: Traffic fine for no helmet in Telangana">
<button onclick="ask()">Ask</button>

<div id="a" class="answer-box" style="display:none;"></div>
</div>

<script>
async function ask() {
    const q = document.getElementById("q").value;
    const box = document.getElementById("a");
    box.style.display = "block";
    box.innerText = "Thinking...";

    const r = await fetch("/ask", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({question: q})
    });

    const d = await r.json();
    box.innerText = d.answer;
    window.history.pushState({}, "", "/" + d.slug);
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







