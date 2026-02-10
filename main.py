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
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RuleMate India</title>
    <style>
        /* 1. BACKGROUND & LAYOUT (AISongCreator Style) */
        body {
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            /* Radial glow from the top center */
            background: radial-gradient(circle at 50% -10%, #1a1b3a 0%, #030414 70%);
            background-color: #030414;
            color: #ffffff;
            font-family: 'Inter', -apple-system, sans-serif;
            padding: 60px 20px;
        }

        /* 2. HEADER & LOGO */
        .logo-container {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            margin-bottom: 10px;
        }

     

        h1 {
            font-size: 3.5rem;
            font-weight: 800;
            margin: 0;
            letter-spacing: -0.04em;
        }

        .hero-subtitle {
            color: rgba(255, 255, 255, 0.7);
            font-size: 1.25rem;
            margin-bottom: 40px;
            text-align: center;
        }

        /* 3. THE GLASS CARD (Semi-transparent with blur) */
        .glass-card {
            background: rgba(25, 25, 31, 0.6);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
            padding: 40px;
            width: 100%;
            max-width: 720px;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.6);
            margin-bottom: 60px;
            box-sizing: border-box;
        }

        .search-input {
            width: 100%;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            color: white;
            font-size: 1.05rem;
            margin-bottom: 24px;
            box-sizing: border-box;
            outline: none;
        }

        /* THE SPECIFIC PURPLE BUTTON */
        .btn-ask {
            width: 100%;
            background: #7053ff;
            color: white;
            border: none;
            padding: 18px;
            border-radius: 12px;
            font-size: 1.15rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .btn-ask:hover {
            background: #5a3fff;
            transform: translateY(-1px);
            box-shadow: 0 0 25px rgba(112, 83, 255, 0.4);
        }

        .check-tag {
            display: inline-flex;
            margin-top: 25px;
            padding: 8px 18px;
            border-radius: 100px;
            background: rgba(112, 83, 255, 0.1);
            border: 1px solid rgba(112, 83, 255, 0.2);
            color: #7053ff;
            font-size: 0.9rem;
        }

        /* 4. FOOTER & VERIFIED CONTENT */
        .footer-section {
            text-align: center;
            max-width: 650px;
        }

        .about-title {
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 12px;
        }

        .about-text {
            color: rgba(255, 255, 255, 0.5);
            font-size: 1rem;
            line-height: 1.6;
            margin-bottom: 40px;
        }

        .disclaimer-container {
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            padding-top: 25px;
            font-size: 0.8rem;
            color: rgba(255, 255, 255, 0.35);
            line-height: 1.5;
            text-align: justify;
        }

        @media (max-width: 640px) {
            h1 { font-size: 2.2rem; }
            .glass-card { padding: 25px; }
        }
    </style>
</head>
<body>

    <div class="logo-container">
        <h1>🇮🇳 RuleMate India</h1>
    </div>
    <p class="hero-subtitle">Government rules made easy. Just ask.</p>

    <div class="glass-card">
        <input type="text" class="search-input" placeholder="Example: What are the latest traffic rules in India?">
        
        <button class="btn-ask">Ask</button>

        <div style="text-align: center;">
            <div class="check-tag">
                ✓ Clarifying Indian regulations through an educational lens.
            </div>
        </div>
    </div>

    <div class="footer-section">
        <div class="about-title">About RuleMate India</div>
        <p class="about-text">
            RuleMate India helps people understand Indian government rules, laws,
            fines and procedures in simple language.        
        </p>
        
        <div class="disclaimer-container">
            <strong>Disclaimer:</strong> This website provides general information on Indian government rules and laws
        for educational purposes only. It is not legal advice.
        Laws and rules may change. Always verify with official government notifications
        or consult a qualified professional.
        </div>
    </div>

</body>
</html>
"""

# Dynamic Route (Must be last to avoid conflicts)
@app.get("/{slug}", response_class=HTMLResponse)
def dynamic_page(slug: str):
    return home()


