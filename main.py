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
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RuleMate India</title>
    <style>
        body {
            margin: 0; padding: 0; min-height: 100vh;
            display: flex; flex-direction: column; align-items: center;
            background: radial-gradient(circle at 50% -10%, #1a1b3a 0%, #030414 70%);
            background-color: #030414; color: #ffffff;
            font-family: 'Inter', -apple-system, sans-serif;
            padding: 60px 20px;
        }
        .logo-container { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
        h1 { font-size: 3.5rem; font-weight: 800; margin: 0; letter-spacing: -0.04em; }
        .hero-subtitle { color: rgba(255, 255, 255, 0.7); font-size: 1.25rem; margin-bottom: 40px; text-align: center; }
        
        .glass-card {
            background: rgba(25, 25, 31, 0.6); backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px); border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px; padding: 40px; width: 100%; max-width: 720px;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.6); margin-bottom: 40px; box-sizing: border-box;
        }
        #userInput {
            width: 100%; background: rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px; padding: 20px; color: white; font-size: 1.05rem;
            margin-bottom: 24px; box-sizing: border-box; outline: none;
        }
        .btn-ask {
            width: 100%; background: #7053ff; color: white; border: none;
            padding: 18px; border-radius: 12px; font-size: 1.15rem; font-weight: 700;
            cursor: pointer; transition: all 0.2s ease;
        }
        .btn-ask:disabled { background: #4a3ba3; cursor: not-allowed; opacity: 0.7; }

        /* AI Result Styling */
        #resultArea { margin-top: 30px; display: none; text-align: left; }
        .answer-box { 
            background: rgba(255, 255, 255, 0.05); border-radius: 15px; 
            padding: 25px; line-height: 1.6; white-space: pre-wrap; 
        }
        .related-title { margin-top: 25px; font-weight: 700; color: #7053ff; }
        .related-q { 
            display: block; background: rgba(112, 83, 255, 0.1); 
            padding: 10px 15px; border-radius: 8px; margin-top: 10px;
            cursor: pointer; font-size: 0.9rem; transition: 0.2s;
        }
        .related-q:hover { background: rgba(112, 83, 255, 0.2); }

        .footer-section { text-align: center; max-width: 650px; }
        .about-title { font-size: 1.1rem; font-weight: 700; margin-bottom: 12px; cursor: pointer; text-decoration: underline; }
        #aboutContent { color: rgba(255, 255, 255, 0.5); font-size: 1rem; line-height: 1.6; display: none; margin-bottom: 30px;}
        .disclaimer-container {
            border-top: 1px solid rgba(255, 255, 255, 0.08); padding-top: 25px;
            font-size: 0.8rem; color: rgba(255, 255, 255, 0.35); text-align: justify;
        }
    </style>
</head>
<body>
    <div class="logo-container">
        <h1>🇮🇳 RuleMate India</h1>
    </div>
    <p class="hero-subtitle">Government rules made easy. Just ask.</p>

    <div class="glass-card">
        <input type="text" id="userInput" placeholder="Example: What are the latest traffic rules in India?">
        <button id="askBtn" class="btn-ask" onclick="handleAsk()">Ask</button>

        <div id="resultArea">
            <div class="answer-box" id="aiAnswer"></div>
            <div class="related-title">Related Questions:</div>
            <div id="relatedQuestions"></div>
        </div>
    </div>

    <div class="footer-section">
        <div class="about-title" onclick="toggleAbout()">About RuleMate India</div>
        <p id="aboutContent">RuleMate India helps people understand Indian government rules, laws, fines and procedures in simple language.</p>
        <div class="disclaimer-container">
            <strong>Disclaimer:</strong> This website provides general information on Indian government rules and laws for educational purposes only. It is not legal advice. Laws and rules may change. Always verify with official government notifications or consult a qualified professional.
        </div>
    </div>

    <script>
        async function handleAsk() {
            const queryInput = document.getElementById('userInput');
            const btn = document.getElementById('askBtn');
            const resultArea = document.getElementById('resultArea');
            const aiAnswer = document.getElementById('aiAnswer');
            const relatedBox = document.getElementById('relatedQuestions');

            if (queryInput.value.trim() === "") return alert("Please enter a question!");

            // UI Loading State
            btn.disabled = true;
            btn.innerText = "Processing...";
            
            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ question: queryInput.value })
                });
                
                const data = await response.json();
                
                // Update UI with AI Data
                aiAnswer.innerText = data.answer;
                relatedBox.innerHTML = "";
                data.related.forEach(q => {
                    const div = document.createElement('div');
                    div.className = 'related-q';
                    div.innerText = q;
                    div.onclick = () => { queryInput.value = q; handleAsk(); };
                    relatedBox.appendChild(div);
                });

                resultArea.style.display = "block";
            } catch (err) {
                alert("Error fetching answer. Please try again.");
            } finally {
                btn.disabled = false;
                btn.innerText = "Ask";
            }
        }

        function toggleAbout() {
            const content = document.getElementById('aboutContent');
            content.style.display = (content.style.display === "none" || content.style.display === "") ? "block" : "none";
        }
    </script>
</body>
</html>
"""

# Dynamic Route
@app.get("/{slug}", response_class=HTMLResponse)
def dynamic_page(slug: str):
    return home()
