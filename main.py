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
    # Main Answer call
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": q.question}],
        temperature=0.2
    )
    answer = response.choices[0].message.content
    slug = slugify(q.question)
    
    # Related Questions Prompt to ensure exactly 4
    related_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Generate EXACTLY 4 short related questions about Indian laws. Return them as a simple list with one question per line. Do not include extra text."},
            {"role": "user", "content": f"Provide 4 follow-up questions for: {q.question}"}
        ],
        temperature=0.5
    )
    
    related = [r.strip("- ").strip() for r in related_response.choices[0].message.content.split("\n") if r.strip()]
    related = related[:4] 

    return {"answer": answer, "slug": slug, "related": related}

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
            padding: 40px 20px;
        }
        .logo-container { display: flex; align-items: center; gap: 10px; margin-bottom: 5px; }
        .flag-emoji { font-size: 2rem; }
        h1 { font-size: 2.8rem; font-weight: 800; margin: 0; letter-spacing: -0.04em; }
        .hero-subtitle { color: rgba(255, 255, 255, 0.6); font-size: 1.1rem; margin-bottom: 35px; text-align: center; }
        
        /* 3D METALLIC GLASS CARD */
        .glass-card {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.03) 100%);
            background-image: radial-gradient(at 0% 0%, rgba(255,255,255,0.15) 0%, transparent 50%);
            backdrop-filter: blur(20px);
            border-top: 1px solid rgba(255, 255, 255, 0.4);
            border-left: 1px solid rgba(255, 255, 255, 0.2);
            border-bottom: 3px solid rgba(0, 0, 0, 0.5);
            border-right: 2px solid rgba(0, 0, 0, 0.4);
            border-radius: 24px;
            padding: 40px; width: 100%; max-width: 720px;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255,255,255,0.1);
            margin-bottom: 50px; box-sizing: border-box;
        }

        /* SUNKEN INPUT */
        #userInput {
            width: 100%; background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px; padding: 20px; color: white; font-size: 1rem;
            margin-bottom: 20px; box-sizing: border-box; outline: none;
            box-shadow: inset 0 4px 10px rgba(0,0,0,0.7);
        }

        /* 3D GLOSSY BUTTON */
        .btn-ask {
            width: 100%; 
            background: linear-gradient(to bottom, #8e78ff 0%, #7053ff 45%, #5a3fff 50%, #4a2fe0 100%);
            color: white; border: none;
            padding: 18px; border-radius: 12px; font-size: 1.1rem; font-weight: 700;
            cursor: pointer; position: relative;
            border-top: 1px solid rgba(255,255,255,0.4);
            border-bottom: 5px solid #2d1b9e;
            box-shadow: 0 8px 20px rgba(0,0,0,0.4);
            transition: all 0.1s;
        }
        .btn-ask:hover { filter: brightness(1.1); }
        .btn-ask:active {
            transform: translateY(3px);
            border-bottom: 2px solid #2d1b9e;
            box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        }
        
        /* PULSE ANIMATION */
        @keyframes pulse-fade {
            0% { opacity: 0.3; }
            50% { opacity: 0.6; }
            100% { opacity: 0.3; }
        }
        .loading-pulse {
            animation: pulse-fade 1.5s infinite ease-in-out;
            color: rgba(255, 255, 255, 0.4);
            font-style: italic; text-align: center; padding: 20px;
        }

        #resultArea { margin-top: 30px; display: none; text-align: left; }
        .answer-box { 
            background: rgba(0, 0, 0, 0.2); border: 1px solid rgba(255,255,255,0.05); 
            border-radius: 15px; padding: 25px; white-space: pre-wrap; line-height: 1.6;
            box-shadow: inset 0 2px 10px rgba(0,0,0,0.5);
            transition: opacity 0.4s ease-in-out;
            opacity: 1;
        }
        
        .related-title { margin-top: 25px; font-weight: 700; color: #7053ff; }
        .related-q { 
            display: block; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255,255,255,0.05);
            padding: 12px 15px; border-radius: 10px; margin-top: 10px;
            cursor: pointer; font-size: 0.9rem; transition: 0.2s; color: rgba(255,255,255,0.8);
        }
        .related-q:hover { background: rgba(255, 255, 255, 0.08); color: white; }

        .check-tag {
            display: inline-flex; margin-top: 25px; padding: 8px 18px;
            border-radius: 100px; background: rgba(112, 83, 255, 0.1);
            border: 1px solid rgba(112, 83, 255, 0.2); color: #7053ff; font-size: 0.85rem;
        }

        .footer-section { text-align: center; max-width: 650px; margin-top: auto; }
        .about-title { font-size: 1rem; font-weight: 700; margin-bottom: 10px; color: #fff; }
        .about-text { color: rgba(255, 255, 255, 0.5); font-size: 0.95rem; line-height: 1.6; margin-bottom: 30px; }
        .disclaimer-container {
            border-top: 1px solid rgba(255, 255, 255, 0.08); padding-top: 25px;
            font-size: 0.8rem; color: rgba(255, 255, 255, 0.3); text-align: justify;
        }
    </style>
</head>
<body>
    <div class="logo-container">
        <span class="flag-emoji">🇮🇳</span>
        <h1>RuleMate India</h1>
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

        <div style="text-align: center;">
            <div class="check-tag">✓ Clarifying Indian regulations through an educational lens.</div>
        </div>
    </div>

    <div class="footer-section">
        <div class="about-title">About RuleMate India</div>
        <p class="about-text">RuleMate India helps people understand Indian government rules, laws, fines and procedures in simple language.</p>
        <div class="disclaimer-container">
            <strong>Disclaimer:</strong> This website provides general information for educational purposes only. It is not legal advice. Always verify with official sources.
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
            btn.innerText = "Processing...";
            
            // Step 1: Fade out the current answer box
            aiAnswer.style.opacity = "0";
            
            setTimeout(() => {
                aiAnswer.innerHTML = '<div class="loading-pulse">Consulting Indian Regulations...</div>';
                aiAnswer.style.opacity = "1";
                resultArea.style.display = "block";
            }, 400);
            
            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ question: queryInput.value })
                });
                const data = await response.json();
                
                // Step 2: Fade out the loader
                aiAnswer.style.opacity = "0";
                
                setTimeout(() => {
                    // Step 3: Insert new answer and fade in
                    aiAnswer.innerText = data.answer;
                    aiAnswer.style.opacity = "1";
                    
                    relatedBox.innerHTML = "";
                    data.related.forEach(q => {
                        const div = document.createElement('div');
                        div.className = 'related-q';
                        // Strip serial numbers/bullets from strings
                        let cleanQ = q.replace(/^\d+[\.\)\s]+/, '');
                        div.innerText = cleanQ;
                        div.onclick = () => { 
                            queryInput.value = cleanQ; 
                            handleAsk(); 
                            window.scrollTo({ top: 0, behavior: 'smooth' }); 
                        };
                        relatedBox.appendChild(div);
                    });
                }, 400);
            } catch (err) {
                aiAnswer.innerText = "Error fetching answer.";
                aiAnswer.style.opacity = "1";
            } finally {
                btn.disabled = false;
                btn.innerText = "Ask";
            }
        }
    </script>
</body>
</html>
"""

# 4. Dynamic Route
@app.get("/{slug}", response_class=HTMLResponse)
def dynamic_page(slug: str):
    return home()
