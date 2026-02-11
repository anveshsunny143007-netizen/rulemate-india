import os
import re
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = FastAPI()

# System Prompt as per your guidelines
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
PUNISHMENT / IMPLICATIONS (if applicable):
- Bullet point
SOURCE:
- Name of Act / Department
"""

class Question(BaseModel):
    question: str

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', '', text)
    text = text.strip().replace(' ', '-')
    return text

@app.get("/sitemap.xml")
def sitemap():
    xml = """<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://rulemate-india.onrender.com/</loc><changefreq>daily</changefreq><priority>1.0</priority></url></urlset>"""
    return Response(content=xml, media_type="application/xml")

@app.post("/ask")
def ask_rule(q: Question):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": q.question}],
        temperature=0.2
    )
    answer = response.choices[0].message.content
    slug = slugify(q.question)
    
    related_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Generate EXACTLY 4 short related questions about Indian laws. Return them as a simple list with one question per line. No serial numbers."},
            {"role": "user", "content": f"Provide 4 follow-up questions for: {q.question}"}
        ],
        temperature=0.5
    )
    related = [r.strip("- ").strip() for r in related_response.choices[0].message.content.split("\n") if r.strip()]
    return {"answer": answer, "slug": slug, "related": related[:4]}

@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RuleMate India | Indian Government Rules Assistant</title>
    <style>
        :root {
            --primary-blue: #2563eb;
            --india-saffron: #FF9933;
            --india-green: #138808;
            --glass-white: rgba(255, 255, 255, 0.95);
        }

        body {
            margin: 0; padding: 0; min-height: 100vh;
            display: flex; flex-direction: column; align-items: center;
            background-color: #f8fafc;
            font-family: 'Inter', -apple-system, sans-serif;
            overflow-x: hidden; position: relative;
        }

        /* DYNAMIC TRICOLOR BACKGROUND */
        .bg-layer {
            position: fixed; width: 100%; height: 100%; top: 0; left: 0; z-index: -2;
            background: 
                radial-gradient(circle at 0% 0%, rgba(255, 153, 51, 0.1) 0%, transparent 40%),
                radial-gradient(circle at 100% 100%, rgba(19, 136, 8, 0.1) 0%, transparent 40%);
        }

        /* ASHOKA CHAKRA - Code-based Watermark */
        .chakra-watermark {
            position: fixed; top: 10%; left: -100px; width: 400px; height: 400px;
            opacity: 0.03; z-index: -1; pointer-events: none;
        }

        /* HEADER */
        .header { text-align: center; padding: 50px 20px; z-index: 10; }
        .logo { font-size: 2.5rem; font-weight: 800; color: #0f172a; margin: 0; display: flex; align-items: center; justify-content: center; gap: 10px; }
        .logo span.in { font-size: 1.1rem; color: #64748b; font-weight: 500; }
        .logo span.india { color: var(--primary-blue); }
        .subtitle { color: #64748b; font-size: 1.1rem; margin-top: 8px; }

        /* 3D GLASS CARD */
        .card-container { width: 100%; max-width: 800px; padding: 0 20px; box-sizing: border-box; }
        .glass-card {
            background: var(--glass-white);
            backdrop-filter: blur(20px);
            border-radius: 32px;
            padding: 40px;
            border: 1px solid rgba(255, 255, 255, 1);
            box-shadow: 
                0 20px 50px rgba(0, 0, 0, 0.05),
                0 1px 3px rgba(0, 0, 0, 0.01);
            position: relative;
            transform: perspective(1000px) rotateX(1deg);
        }

        /* MONUMENT GRAPHICS (Inline SVGs for high speed/no copyright) */
        .monument-icon { position: absolute; bottom: 10px; width: 100px; opacity: 0.1; pointer-events: none; }
        .left-mon { left: 30px; }
        .right-mon { right: 30px; }

        /* FORM ELEMENTS */
        #userInput {
            width: 100%; background: #f1f5f9; border: 2px solid transparent;
            border-radius: 16px; padding: 22px; color: #1e293b; font-size: 1.1rem;
            margin-bottom: 25px; box-sizing: border-box; outline: none;
            transition: all 0.3s ease;
        }
        #userInput:focus { border-color: #bfdbfe; background: #fff; }

        .btn-ask {
            width: 100%; 
            background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%);
            color: white; border: none; padding: 20px; border-radius: 16px; 
            font-size: 1.2rem; font-weight: 700; cursor: pointer;
            box-shadow: 0 10px 25px rgba(37, 99, 235, 0.3);
            transition: transform 0.2s;
        }
        .btn-ask:hover { transform: translateY(-2px); filter: brightness(1.1); }

        .check-tag {
            display: inline-flex; margin-top: 30px; padding: 10px 20px;
            border-radius: 100px; background: #eff6ff; color: #1d4ed8;
            font-size: 0.85rem; font-weight: 600; border: 1px solid #dbeafe;
        }

        /* RESULTS AREA */
        #resultArea { margin-top: 30px; display: none; text-align: left; animation: fadeIn 0.5s; }
        .answer-box { background: #fff; border: 1px solid #e2e8f0; border-radius: 20px; padding: 30px; line-height: 1.7; color: #334155; }
        .related-title { font-weight: 700; margin: 25px 0 10px; font-size: 0.9rem; color: #94a3b8; letter-spacing: 1px; }
        .related-q { background: #f8fafc; padding: 15px; border-radius: 12px; margin-bottom: 10px; cursor: pointer; border: 1px solid #e2e8f0; }
        .related-q:hover { background: #eff6ff; border-color: #3b82f6; color: #2563eb; }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        .footer { text-align: center; padding: 60px 20px; color: #94a3b8; font-size: 0.9rem; }
    </style>
</head>
<body>

    <div class="bg-layer"></div>

    <svg class="chakra-watermark" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" stroke-width="0.5"/>
        <circle cx="50" cy="50" r="8" fill="none" stroke="currentColor" stroke-width="0.5"/>
        <script>
            for(let i=0; i<24; i++) {
                document.write(`<line x1="50" y1="50" x2="${50 + 45*Math.cos(i*15*Math.PI/180)}" y2="${50 + 45*Math.sin(i*15*Math.PI/180)}" stroke="currentColor" stroke-width="0.2"/>`);
            }
        </script>
    </svg>

    <div class="header">
        <h1 class="logo"><span class="in">IN</span> RuleMate <span class="india">India</span></h1>
        <p class="subtitle">Government rules made easy. Just ask.</p>
    </div>

    <div class="card-container">
        <div class="glass-card">
            <svg class="monument-icon left-mon" viewBox="0 0 100 100" fill="currentColor">
                <path d="M20 90h60v-5H20v5zm10-10h40V40L50 30 30 40v40zm5-30h30v25H35V50z"/>
            </svg>
            <svg class="monument-icon right-mon" viewBox="0 0 100 100" fill="currentColor">
                <path d="M45 90h10V20l-5-10-5 10v70zm2-60h6v2h-6v-2zm0 10h6v2h-6v-2z"/>
            </svg>

            <input type="text" id="userInput" placeholder="Ex: What are the documents required for a PAN card?">
            <button id="askBtn" class="btn-ask" onclick="handleAsk()">Ask</button>

            <div id="resultArea">
                <div class="answer-box" id="aiAnswer"></div>
                <div class="related-title">Related Questions:</div>
                <div id="relatedQuestions"></div>
            </div>

            <div style="text-align: center;">
                <div class="check-tag">✓ Clarifying Indian regulations through an educational lens.</div>
            </div>
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
        async function handleAsk() {
            const queryInput = document.getElementById('userInput');
            const btn = document.getElementById('askBtn');
            const resultArea = document.getElementById('resultArea');
            const aiAnswer = document.getElementById('aiAnswer');
            const relatedBox = document.getElementById('relatedQuestions');

            if (queryInput.value.trim() === "") return;

            btn.disabled = true;
            btn.innerText = "Analyzing...";
            aiAnswer.innerHTML = "Fetching official rules...";
            resultArea.style.display = "block";
            
            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ question: queryInput.value })
                });
                const data = await response.json();
                
                aiAnswer.innerText = data.answer;
                relatedBox.innerHTML = "";
                data.related.forEach(q => {
                    const div = document.createElement('div');
                    div.className = 'related-q';
                    div.innerText = q.replace(/^\d+[\.\)\s]+/, '');
                    div.onclick = () => { 
                        queryInput.value = div.innerText; 
                        handleAsk(); 
                        window.scrollTo({ top: 0, behavior: 'smooth' }); 
                    };
                    relatedBox.appendChild(div);
                });
            } catch (err) {
                aiAnswer.innerText = "Error connecting to server.";
            } finally {
                btn.disabled = false;
                btn.innerText = "Ask";
            }
        }
    </script>
</body>
</html>
"""

@app.get("/{slug}", response_class=HTMLResponse)
def dynamic_page(slug: str):
    return home()
