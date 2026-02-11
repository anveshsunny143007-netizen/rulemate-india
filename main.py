import os
import re
import sqlite3
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = FastAPI()

# ---------------- DATABASE ----------------

conn = sqlite3.connect("rulemate.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT,
    answer TEXT,
    slug TEXT UNIQUE
)
""")
conn.commit()

# ---------------- SYSTEM PROMPT ----------------

SYSTEM_PROMPT = """
You are an Indian Government Rules Assistant.
Answer ONLY Indian government rules.
Use simple language.
"""

class Question(BaseModel):
    question: str

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', '', text)
    text = text.strip().replace(' ', '-')
    return text

# ---------------- SITEMAP ----------------

@app.get("/sitemap.xml", response_class=Response)
def sitemap():
    cursor.execute("SELECT slug FROM questions")
    rows = cursor.fetchall()

    urls = ""
    for row in rows:
        urls += f"<url><loc>https://rulemate-india.onrender.com/{row[0]}</loc></url>"

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>https://rulemate-india.onrender.com/</loc></url>
{urls}
</urlset>"""

    return Response(content=xml, media_type="application/xml")

# ---------------- ASK API ----------------

@app.post("/ask")
def ask_rule(q: Question):
    slug = slugify(q.question)

    cursor.execute("SELECT answer FROM questions WHERE slug=?", (slug,))
    row = cursor.fetchone()

    if row:
        answer = row[0]
    else:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": q.question}
            ],
            temperature=0.2
        )
        answer = response.choices[0].message.content

        cursor.execute(
            "INSERT INTO questions (question, answer, slug) VALUES (?, ?, ?)",
            (q.question, answer, slug)
        )
        conn.commit()

    return {"answer": answer, "slug": slug, "related": []}

# ---------------- HOME PAGE ----------------

@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RuleMate India</title>

<style>
body {
    margin: 0;
    padding: 0;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    background: radial-gradient(circle at 50% -10%, #1a1b3a 0%, #030414 70%);
    color: #ffffff;
    font-family: Arial, sans-serif;
    padding: 40px 20px;
}

.logo-container {
    display: flex;
    align-items: center;
    gap: 10px;
}

.flag-emoji {
    font-size: 2rem;
}

h1 {
    font-size: 2.5rem;
    margin: 0;
}

.glass-card {
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 30px;
    width: 100%;
    max-width: 700px;
    margin-top: 30px;
}

input {
    width: 100%;
    padding: 15px;
    border-radius: 10px;
    border: none;
    margin-bottom: 15px;
}

button {
    width: 100%;
    padding: 15px;
    border-radius: 10px;
    border: none;
    background: #6352c7;
    color: white;
    font-weight: bold;
    cursor: pointer;
}

.answer-box {
    margin-top: 20px;
    white-space: pre-wrap;
}
</style>
</head>

<body>

<div class="logo-container">
    <span class="flag-emoji">🇮🇳</span>
    <h1>RuleMate India</h1>
</div>

<div class="glass-card">
    <input type="text" id="q" placeholder="Ask about Indian rules">
    <button onclick="ask()">Ask</button>

    <div id="a" class="answer-box"></div>
</div>

<script>
async function ask() {
    const q = document.getElementById("q").value;

    const r = await fetch("/ask", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({question:q})
    });

    const d = await r.json();

    document.getElementById("a").innerText = d.answer;

    // VERY IMPORTANT — dynamic URL
    window.history.pushState({}, "", "/" + d.slug);
}
</script>

</body>
</html>
"""


# ---------------- DYNAMIC PAGE ----------------

@app.get("/{slug}", response_class=HTMLResponse)
def dynamic_page(slug: str):
    cursor.execute("SELECT question, answer FROM questions WHERE slug=?", (slug,))
    row = cursor.fetchone()

    if not row:
        return home()

    question, answer = row

    return f"""
    <html>
    <head>
        <title>{question} | RuleMate India</title>
    </head>
    <body style="font-family:Arial;max-width:600px;margin:50px auto;">
        <h1>{question}</h1>
        <div style="white-space:pre-wrap;">{answer}</div>
        <br><br>
        <a href="/">Ask another question</a>
    </body>
    </html>
    """

