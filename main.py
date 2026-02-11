import os
import re
import sqlite3
import json
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

# 1. Configuration & Setup
load_dotenv()
# Note: Ensure OPENAI_API_KEY is set in Render Environment Variables
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = FastAPI()

# ---------------- DATABASE SETUP ----------------

def get_db():
    # Use an absolute path if necessary for production
    conn = sqlite3.connect("rulemate.db", check_same_thread=False)
    return conn

db_conn = get_db()
cursor = db_conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT,
    answer TEXT,
    slug TEXT UNIQUE,
    related_qs TEXT
)
""")
db_conn.commit()

# ---------------- PROMPTS & UTILS ----------------

SYSTEM_PROMPT = """
You are an Indian Government Rules Assistant.
STRICT RULES:
- Answer ONLY Indian government rules, laws, schemes, IPC sections.
- Use simple language.
- Do NOT give opinions or guess.
FORMAT EVERY ANSWER EXACTLY LIKE THIS:
SHORT ANSWER:
(one clear sentence)
DETAILS:
- Bullet point
PUNISHMENT / IMPLICATIONS (if applicable):
- Bullet point
SOURCE:
- Name of Act / Department
"""

class QuestionRequest(BaseModel):
    question: str

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', '', text)
    text = text.strip().replace(' ', '-')
    return text

# ---------------- API ROUTES ----------------

@app.get("/sitemap.xml", response_class=Response)
def sitemap():
    cursor.execute("SELECT slug FROM questions")
    rows = cursor.fetchall()
    
    urls = "".join([f"<url><loc>https://rulemate-india.onrender.com/{row[0]}</loc><changefreq>weekly</changefreq></url>" for row in rows])
    
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://rulemate-india.onrender.com/</loc><priority>1.0</priority></url>
  {urls}
</urlset>"""
    return Response(content=xml, media_type="application/xml")

@app.post("/ask")
def ask_rule(q: QuestionRequest):
    slug = slugify(q.question)

    # Check Database first
    cursor.execute("SELECT answer, related_qs FROM questions WHERE slug=?", (slug,))
    existing = cursor.fetchone()

    if existing:
        return {
            "answer": existing[0],
            "slug": slug,
            "related": json.loads(existing[1])
        }

    # 1. Generate Main Answer
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": q.question}
        ],
        temperature=0.2
    )
    answer = response.choices[0].message.content

    # 2. Generate Related Questions
    related_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Generate 4 short related questions about Indian laws. Return them one per line. No numbers."},
            {"role": "user", "content": f"Follow-up for: {q.question}"}
        ],
        temperature=0.5
    )
    related = [r.strip("- ").strip() for r in related_response.choices[0].message.content.split("\n") if r.strip()][:4]

    # 3. Store in DB
    try:
        cursor.execute(
            "INSERT INTO questions (question, answer, slug, related_qs) VALUES (?, ?, ?, ?)",
            (q.question, answer, slug, json.dumps(related))
        )
        db_conn.commit()
    except sqlite3.IntegrityError:
        pass 

    return {"answer": answer, "slug": slug, "related": related}

# ---------------- UI STYLES ----------------
# We separate the CSS to avoid f-string confusion
CSS_STYLE = """
<style>
    body {
        margin: 0; padding: 0; min-height: 100vh;
        display: flex; flex-direction: column; align-items: center;
        background: radial-gradient(circle at 50% -10%, #1a1b3a 0%, #030414 70%);
        background-color: #030414; color: #ffffff;
        font-family: 'Inter', -apple-system, sans-serif;
        padding: 40px 20px;
    }
    .logo-container { display: flex; align-items: center; gap: 10px; margin-bottom: 5px; cursor: pointer; }
    .flag-emoji { font-size: 2rem; }
    h1 { font-size: 2.8rem; font-weight: 800; margin: 0; letter-spacing: -0.04em; }
    .hero-subtitle { color: rgba(255, 255, 255, 0.5); font-size: 1.1rem; margin-bottom: 35px; text-align: center; }
    
    .glass-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%);
        backdrop-filter: blur(25px);
        border-top: 1px solid rgba(255, 255, 255, 0.3);
        border-left: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 40px; width: 100%; max-width: 720px;
        box-shadow: 0 30px 60px rgba(0, 0, 0, 0.8);
        margin-bottom: 50px; box-sizing: border-box;
    }

    #userInput {
        width: 100%; background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px; padding: 20px; color: white; font-size: 1rem;
        margin-bottom: 20px; box-sizing: border-box; outline: none;
        box-shadow: inset 0 4px 12px rgba(0,0,0,0.5);
    }

    .btn-ask {
        width: 100%; 
        background: linear-gradient(to bottom, #6352c7 0%, #372b85 100%);
        color: white; border: none; padding: 18px; border-radius: 12px;
        font-size: 1.1rem; font-weight: 700; cursor: pointer;
        border-bottom: 4px solid #1f1752; transition: all 0.1s;
    }

    .btn-ask:active { transform: translateY(2px); border-bottom-width: 2px; }

    .loading-pulse {
        animation: pulse 1.5s infinite; color: rgba(255,255,255,0.4); text-align: center;
    }
    @keyframes pulse { 0% {opacity: 0.4} 50% {opacity: 0.8} 100% {opacity: 0.4} }

    .answer-box { 
        background: rgba(0, 0, 0, 0.3); border-radius: 15px; padding: 25px; 
        white-space: pre-wrap; line-height: 1.6; margin-top: 30px;
    }
    
    .related-q { 
        background: rgba(255,255,255,0.03); padding: 12px; border-radius: 10px;
        margin-top: 10px; cursor: pointer; border: 1px solid rgba(255,255,255,0.05);
        font-size: 0.9rem; transition: 0.2s;
    }
    .related-q:hover { background: rgba(255,255,255,0.1); }

    .footer-section { text-align: center; font-size: 0.8rem; color: rgba(255,255,255,0.3); margin-top: auto; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
def home():
    # Note the double curly braces {{ }} inside the script section!
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>RuleMate India | Gov Rules Simplified</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {CSS_STYLE}
</head>
<body>
    <div class="logo-container" onclick="window.location='/'">
        <span class="flag-emoji">🇮🇳</span>
        <h1>RuleMate India</h1>
    </div>
    <p class="hero-subtitle">Indian laws and government rules made easy. Just ask</p>

    <div class="glass-card">
        <input type="text" id="userInput" placeholder="e.g. What are the latest traffic rules in India?">
        <button id="askBtn" class="btn-ask" onclick="handleAsk()">Ask RuleMate</button>

        <div id="resultArea" style="display:none;">
            <div class="answer-box" id="aiAnswer"></div>
            <div style="margin-top:25px; color:#6352c7; font-weight:bold;">Related Questions:</div>
            <div id="relatedQuestions"></div>

        <div style="text-align: center;">
            <div class="check-tag">✓ Clarifying Indian regulations through an educational lens.</div>
        </div>
    </div>

    <div class="footer-section">
        <div class="about-title">About RuleMate India</div>
        <p class="about-text">RuleMate India helps people understand Indian government rules, laws, fines and procedures in simple language.</p>
        <div class="disclaimer-container">
            <strong>Disclaimer:</strong> This website provides general information on Indian government rules and laws for educational purposes only. It is not legal advice. Laws and rules may change. Always verify with official government notifications or consult a qualified professional. 
        </div>
    </div>

    <script>
        async function handleAsk() {{
            const input = document.getElementById('userInput');
            const btn = document.getElementById('askBtn');
            const resultArea = document.getElementById('resultArea');
            const aiAnswer = document.getElementById('aiAnswer');
            const relatedBox = document.getElementById('relatedQuestions');

            if(!input.value.trim()) return;

            btn.disabled = true;
            btn.innerText = "Consulting Records...";
            resultArea.style.display = "block";
            aiAnswer.innerHTML = '<div class="loading-pulse">Analyzing Indian Acts...</div>';

            try {{
                const res = await fetch('/ask', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ question: input.value }})
                }});
                const data = await res.json();

                window.history.pushState({{}}, "", "/" + data.slug);
                aiAnswer.innerText = data.answer;
                
                relatedBox.innerHTML = "";
                data.related.forEach(q => {{
                    const d = document.createElement('div');
                    d.className = 'related-q';
                    d.innerText = q;
                    d.onclick = () => {{ input.value = q; handleAsk(); window.scrollTo(0,0); }};
                    relatedBox.appendChild(d);
                }});
            }} catch(e) {{
                aiAnswer.innerText = "Error connecting to server.";
            }} finally {{
                btn.disabled = false;
                btn.innerText = "Ask RuleMate";
            }}
        }}
    </script>
</body>
</html>
"""

@app.get("/{slug}", response_class=HTMLResponse)
def dynamic_page(slug: str):
    cursor.execute("SELECT question, answer, related_qs FROM questions WHERE slug=?", (slug,))
    row = cursor.fetchone()

    if not row:
        return home()

    question, answer, related_json = row
    related = json.loads(related_json)
    
    # Pre-build related HTML to avoid f-string JS conflict
    related_html = ""
    for q in related:
        related_html += f'<div class="related-q" onclick="window.location=\'/\'">{q}</div>'

    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>{question} | RuleMate India</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {CSS_STYLE}
</head>
<body>
    <div class="logo-container" onclick="window.location='/'">
        <span class="flag-emoji">🇮🇳</span>
        <h1>RuleMate India</h1>
    </div>
    
    <div class="glass-card">
        <h2 style="margin-top:0; color:#7a68e8;">{question}</h2>
        <div class="answer-box" style="background:rgba(255,255,255,0.02)">{answer}</div>
        
        <div style="margin-top:25px; color:#6352c7; font-weight:bold;">More about this:</div>
        {related_html}
        
        <div style="margin-top:30px; text-align:center;">
            <a href="/" style="color:rgba(255,255,255,0.5); text-decoration:none;">← Ask a New Question</a>
        </div>
    </div>
</body>
</html>
"""

