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
            --india-saffron: #FF9933;
            --india-white: #FFFFFF;
            --india-green: #138808;
            --india-blue: #000080;
            --primary-blue: #2563eb;
        }

        body {
            margin: 0; padding: 0; min-height: 100vh;
            display: flex; flex-direction: column; align-items: center;
            background-color: #f0f4f8;
            font-family: 'Inter', sans-serif;
            overflow-x: hidden;
            position: relative;
        }

        /* VIBRANT TRICOLOR BACKGROUND MESH */
        .background-mesh {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            z-index: -2;
            background: 
                radial-gradient(at 0% 0%, rgba(255, 153, 51, 0.15) 0px, transparent 50%),
                radial-gradient(at 100% 0%, rgba(37, 99, 235, 0.1) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(19, 136, 8, 0.15) 0px, transparent 50%),
                radial-gradient(at 0% 100%, rgba(37, 99, 235, 0.1) 0px, transparent 50%);
        }

        /* DECORATIVE WAVES */
        .wave {
            position: fixed; width: 200%; height: 400px; z-index: -1; opacity: 0.4;
            left: -50%; filter: blur(60px); pointer-events: none;
        }
        .wave-top { top: -200px; background: var(--india-saffron); border-radius: 40%; transform: rotate(-5deg); }
        .wave-bottom { bottom: -200px; background: var(--india-green); border-radius: 43%; transform: rotate(5deg); }

        /* LOGO & HEADER */
        .header { text-align: center; padding: 60px 20px 40px; }
        .logo { font-size: 3rem; font-weight: 800; color: #1e293b; letter-spacing: -1px; }
        .logo span.in { font-size: 1.2rem; vertical-align: middle; color: #64748b; margin-right: 10px; }
        .logo span.india { color: var(--primary-blue); }
        .subtitle { color: #475569; font-size: 1.2rem; margin-top: 10px; }

        /* HIGH-DEPTH GLASS CARD */
        .card-container { width: 100%; max-width: 850px; padding: 0 20px; box-sizing: border-box; perspective: 1000px; }
        .glass-card {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(20px);
            border-radius: 35px;
            padding: 50px;
            border: 1px solid rgba(255, 255, 255, 0.8);
            box-shadow: 
                0 30px 60px rgba(0, 0, 0, 0.08),
                inset 0 0 0 1px rgba(255, 255, 255, 0.5);
            position: relative;
            transform: rotateX(1deg);
        }

        /* MONUMENT SVGS */
        .monument { position: absolute; bottom: 20px; width: 120px; opacity: 0.08; pointer-events: none; fill: #1e293b; }
        .mon-left { left: 40px; }
        .mon-right { right: 40px; }

        /* INPUTS */
        #userInput {
            width: 100%; background: #f1f5f9; border: 1px solid #e2e8f0;
            border-radius: 18px; padding: 24px; color: #1e293b; font-size: 1.1rem;
            margin-bottom: 25px; box-sizing: border-box; outline: none;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.03);
        }
        .btn-ask {
            width: 100%; background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            color: white; border: none; padding: 22px; border-radius: 18px;
            font-size: 1.3rem; font-weight: 700; cursor: pointer;
            box-shadow: 0 15px 35px rgba(37, 99, 235, 0.3);
            transition: all 0.3s ease;
        }
        .btn-ask:hover { transform: translateY(-3px); box-shadow: 0 20px 45px rgba(37, 99, 235, 0.4); }

        .tagline {
            display: inline-flex; align-items: center; margin-top: 35px;
            padding: 12px 25px; border-radius: 100px; background: rgba(37, 99, 235, 0.05);
            color: #1e40af; font-size: 0.9rem; font-weight: 600; border: 1px solid rgba(37,99,235,0.1);
        }

        /* ASHOKA CHAKRA BG */
        .chakra-bg {
            position: fixed; top: 15%; left: -150px; width: 500px; height: 500px;
            opacity: 0.03; z-index: -1; transform: rotate(15deg);
        }

        .footer { text-align: center; padding: 80px 20px; max-width: 800px; margin: 0 auto; }
        .footer h3 { color: #1e293b; margin-bottom: 15px; }
        .footer p { color: #64748b; line-height: 1.6; }
    </style>
</head>
<body>
    <div class="background-mesh"></div>
    <div class="wave wave-top"></div>
    <div class="wave wave-bottom"></div>

    <svg class="chakra-bg" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="45" fill="none" stroke="#000080" stroke-width="1"/>
        <circle cx="50" cy="50" r="5" fill="#000080"/>
        <g stroke="#000080" stroke-width="0.5">
            <script>
                for(let i=0; i<24; i++) {
                    let angle = i * 15 * (Math.PI/180);
                    let x2 = 50 + 45 * Math.cos(angle);
                    let y2 = 50 + 45 * Math.sin(angle);
                    document.write(`<line x1="50" y1="50" x2="${x2}" y2="${y2}" />`);
                }
            </script>
        </g>
    </svg>

    <div class="header">
        <h1 class="logo"><span class="in">IN</span> RuleMate <span class="india">India</span></h1>
        <p class="subtitle">Government rules made easy. Just ask.</p>
    </div>

    <div class="card-container">
        <div class="glass-card">
            <svg class="monument mon-left" viewBox="0 0 24 24"><path d="M5 21h14v-2H5v2zm2-4h10V9l-5-4-5 4v8zm3-6h4v4h-4v-4z"/></svg>
            <svg class="monument mon-right" viewBox="0 0 24 24"><path d="M11 21h2V6l-1-3-1 3v15zM9 21h1v-2H9v2zm5 0h1v-2h-1v2z"/></svg>

            <input type="text" id="userInput" placeholder="Example: What are the traffic rules for 2-wheelers?">
            <button id="askBtn" class="btn-ask" onclick="handleAsk()">Ask</button>

            <div id="resultArea" style="display:none; margin-top:30px;">
                <div id="aiAnswer" style="background:#fff; padding:25px; border-radius:20px; border:1px solid #e2e8f0; line-height:1.7;"></div>
                <div id="relatedQuestions" style="margin-top:20px;"></div>
            </div>

            <div style="text-align: center;">
                <div class="tagline">✓ Clarifying Indian regulations through an educational lens.</div>
            </div>
        </div>
    </div>

    <div class="footer">
        <h3>About RuleMate India</h3>
        <p>RuleMate India helps people understand Indian government rules, laws, and procedures in simple language. This platform is for educational purposes only and does not constitute legal advice.</p>
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
            btn.innerText = "Processing...";
            aiAnswer.innerHTML = "Consulting official records...";
            resultArea.style.display = "block";
            
            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ question: queryInput.value })
                });
                const data = await response.json();
                
                aiAnswer.innerText = data.answer;
                relatedBox.innerHTML = '<p style="font-weight:700; color:#64748b; margin:20px 0 10px;">RELATED:</p>';
                data.related.forEach(q => {
                    const div = document.createElement('div');
                    div.style = "background:#f8fafc; padding:15px; border-radius:12px; margin-bottom:8px; cursor:pointer; border:1px solid #e2e8f0;";
                    div.innerText = q;
                    div.onclick = () => { queryInput.value = q; handleAsk(); };
                    relatedBox.appendChild(div);
                });
            } catch (err) {
                aiAnswer.innerText = "Connection error. Please try again.";
            } finally {
                btn.disabled = false; btn.innerText = "Ask";
            }
        }
    </script>
</body>
</html>
"""

@app.get("/{slug}", response_class=HTMLResponse)
def dynamic_page(slug: str):
    return home()

