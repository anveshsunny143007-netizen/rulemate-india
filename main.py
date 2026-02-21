import os
import re
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
import json
from fastapi import Request
from fastapi.responses import RedirectResponse

# 1. Configuration & Setup
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = FastAPI()

@app.middleware("http")
async def force_domain(request: Request, call_next):
    host = request.headers.get("host")

    if host == "rulemate-india.onrender.com":
        new_url = str(request.url).replace(
            "rulemate-india.onrender.com",
            "rulemate.in"
        )
        return RedirectResponse(url=new_url, status_code=301)

    return await call_next(request)

import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def get_cursor():
    conn = get_conn()
    return conn, conn.cursor()


# Create table safely
conn, cursor = get_cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS pages (
    slug TEXT PRIMARY KEY,
    question TEXT,
    answer TEXT,
    related TEXT,
    category TEXT
)
""")
conn.commit()
conn.close()

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

def is_legal_question(question: str) -> bool:
    legal_keywords = [
        "fine", "penalty", "punishment", "law", "rule", "rules",
        "ipc", "section", "court", "judge", "constitution",
        "legal", "rights", "act", "government", "license",
        "permit", "procedure", "certificate", "apply",
        "tax", "gst", "traffic", "driving", "offence",
        "crime", "arrest", "bail",

        # 🔥 ADD THESE IMPORTANT WORDS
        "passport", "aadhaar", "pan", "voter", "ration",
        "fir", "police", "complaint", "income", "return",
        "document", "documents", "update", "renewal",
        "registration", "apply for", "online", "process"
    ]


    q = question.lower()

    # Step 1: keyword check
    for word in legal_keywords:
        if word in q:
            return True

    # Step 2: fallback only if meaningful length
    if len(q) < 20:
        return False
    # Step 2: fallback to AI check
    check = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Answer ONLY YES or NO. Is this question about Indian government rules, laws, constitution, legal system, or official procedures?"
            },
            {"role": "user", "content": question}
        ],
        temperature=0
    )

    decision = check.choices[0].message.content.strip().upper()
    return "YES" in decision

def detect_category(question: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": """
Classify the user's question into ONE of these categories ONLY:

traffic-rules-india
passport-rules
income-tax-rules
police-procedure
identity-documents
constitution-law
general-laws

Return ONLY the category name.
No explanation.
"""
            },
            {"role": "user", "content": question}
        ]
    )

    category = response.choices[0].message.content.strip().lower()

    allowed = [
        "traffic-rules-india",
        "passport-rules",
        "income-tax-rules",
        "police-procedure",
        "identity-documents",
        "constitution-law",
        "general-laws"
    ]

    if category not in allowed:
        return "general-laws"

    return category

def clean_question_text(text: str) -> str:
    # Remove numbering like "1.", "2)", "3 -"
    text = re.sub(r'^\s*\d+[\.\)\-\s]+', '', text.strip())

    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

def slugify(text):
    # remove numbering
    text = re.sub(r'^[0-9]+[\.\)\-\s]+', '', text.lower())

    # remove useless words
    text = re.sub(r'\b(is|are|was|were|do|does|did|can|could|should|would|will|shall)\b', '', text)

    # remove symbols
    text = re.sub(r'[^a-z0-9 ]', '', text)

    # clean spaces
    text = re.sub(r'\s+', ' ', text).strip()

    slug = text.replace(' ', '-')
    slug = slug.strip("-")

    # ⭐ IMPORTANT — LIMIT SLUG LENGTH
    MAX_LEN = 80
    if len(slug) > MAX_LEN:
        slug = slug[:MAX_LEN]
        slug = slug.rsplit('-', 1)[0]  # don't cut words

    return slug

@app.get("/sitemap.xml", response_class=Response)
def sitemap():
    conn, cursor = get_cursor()
    cursor.execute("SELECT slug FROM pages")
    rows = cursor.fetchall()
    conn.close()
    
    # 🔥 GET ALL CATEGORIES
    conn, cursor = get_cursor()
    cursor.execute("""
        SELECT DISTINCT category
        FROM pages
        WHERE category IS NOT NULL
    """)
    categories = cursor.fetchall()
    conn.close()
    
    base = "https://rulemate.in"

    # 🚨 Block dangerous patterns
    bad_words = [
        ".env", "debug", "php", "aws", "config",
        "login", "admin", "root", "sql", "backup",
        "test", "tmp", "cache", "s3cfg"
    ]

    urls = ""
    # 🔥 ADD CATEGORY PAGES TO SITEMAP
    for c in categories:
        cat = c[0]
        urls += f"""
        <url>
            <loc>{base}/category/{cat}</loc>
        </url>
        """

    # 🔥 ADD QUESTION PAGES
    for r in rows:
        slug = r[0].lower()

        # Skip junk / dangerous slugs
        if any(word in slug for word in bad_words):
            continue

        # Skip file-type slugs
        if slug.endswith((".ico", ".png", ".jpg", ".jpeg", ".js", ".css", ".json")):
            continue

        # Skip very short or weird slugs
        if len(slug) < 5 or "--" in slug:
            continue

        urls += f"""
        <url>
            <loc>{base}/{slug}</loc>
        </url>
        """

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">

<url>
<loc>{base}/</loc>
</url>

{urls}

</urlset>
"""
    return Response(content=xml.strip(), media_type="application/xml")

@app.get("/robots.txt", response_class=Response)
def robots():
    content = """
User-agent: *
Allow: /

Sitemap: https://rulemate.in/sitemap.xml
"""
    return Response(content=content.strip(), media_type="text/plain")

def is_ai_fragment(text: str) -> bool:
    text = text.lower().strip()

    junk_patterns = [
        "certainly",
        "here are",
        "related questions",
        "sure here",
        "provide 4",
    ]

    # starts with junk phrase
    if any(text.startswith(j) for j in junk_patterns):
        return True

    # incomplete fragment starts
    if text.startswith(("and ", "or ", "about ")):
        return True

    return False

@app.post("/ask")
def ask_rule(q: Question):

    # STEP 1: Smart legal filter
    if not is_legal_question(q.question):
        return {
            "answer": "This website only answers questions about Indian government rules, laws, fines, and official procedures.",
            "slug": "",
            "related": []
        }
        
    clean_q = clean_question_text(q.question)
    if is_ai_fragment(clean_q):
        return {
            "answer": "Please ask a complete question about Indian laws.",
            "slug": "",
            "related": []
        }
    # 🔥 NEW: Check if same question already exists
    conn, cursor = get_cursor()
    cursor.execute(
        "SELECT slug, answer, related FROM pages WHERE question=%s",
        (clean_q,)
    )
    existing = cursor.fetchone()
    conn.close()
    
    if existing:
        return {
            "answer": existing[1],
            "slug": existing[0],
            "related": json.loads(existing[2]) if existing[2] else []
        }

    # Only generate slug if not found
    slug = slugify(clean_q)

    # 🚨 BLOCK NON-LEGAL SINGLE WORD JUNK
    if len(clean_q.split()) < 3:
        return {
            "answer": "Please ask a complete question about Indian laws or government rules.",
            "slug": "",
            "related": []
        }

    if len(clean_q) < 15:
        return {
            "answer": "Please ask a detailed question about Indian laws.",
            "slug": "",
            "related": []
        }

    # 🚨 FILTER BAD / JUNK URLS
    bad_words = [
        ".env", "debug", "php", "aws", "config",
        "login", "admin", "root", "sql", "backup", "certainly", "sure"
    ]

    if any(word in slug.split("-") for word in bad_words):
        return {
            "answer": "Invalid query.",
            "slug": "",
            "related": []
        }

    # Check if already exists
    conn, cursor = get_cursor()
    cursor.execute("SELECT answer, related FROM pages WHERE slug=%s", (slug,))
    existing = cursor.fetchone()
    conn.close()
    
    if existing:
        answer = existing[0]
        related = json.loads(existing[1]) if existing[1] else []
    else:
        # Generate answer
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": clean_q}
            ],
            temperature=0.2
        )
        answer = response.choices[0].message.content

        # Generate related
        related_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Generate EXACTLY 4 short related questions about Indian laws. Return them one per line."},
                {"role": "user", "content": f"Provide 4 follow-up questions for: {clean_q}"}
            ],
            temperature=0.5
        )

        related = []
        for r in related_response.choices[0].message.content.split("\n"):
            r = clean_question_text(r.strip("- ").strip())
            if r and not is_ai_fragment(r):
                related.append(r)

        related = related[:4]

        # Store in DB
        category = detect_category(clean_q)
        conn, cursor = get_cursor()
        cursor.execute("""
        INSERT INTO pages (slug, question, answer, related, category)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (slug) DO NOTHING
        """, (slug, clean_q, answer, json.dumps(related), category))

        conn.commit()
        conn.close()
        
    return {
        "answer": answer,
        "slug": slug,
        "related": related
    }

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
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
        .hero-subtitle { color: rgba(255, 255, 255, 0.5); font-size: 1.1rem; margin-bottom: 35px; text-align: center; }
        
        /* 3D METALLIC GLASS CARD */
        .glass-card {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%);
            background-image: radial-gradient(at 0% 0%, rgba(255,255,255,0.1) 0%, transparent 50%);
            backdrop-filter: blur(25px);
            border-top: 1px solid rgba(255, 255, 255, 0.3);
            border-left: 1px solid rgba(255, 255, 255, 0.1);
            border-bottom: 2px solid rgba(0, 0, 0, 0.6);
            border-right: 2px solid rgba(0, 0, 0, 0.4);
            border-radius: 24px;
            padding: 40px; width: 100%; max-width: 720px;
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(255,255,255,0.05);
            margin-bottom: 50px; box-sizing: border-box;
        }

        /* SUNKEN INPUT */
        #userInput {
            width: 100%; background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px; padding: 20px; color: white; font-size: 1rem;
            margin-bottom: 20px; box-sizing: border-box; outline: none;
            box-shadow: inset 0 4px 12px rgba(0,0,0,0.9);
        }

        /* FADED METALLIC BUTTON (Lowered Brightness) */
        .btn-ask {
            width: 100%; 
            /* Desaturated "Deep Purple Steel" Gradient */
            background: linear-gradient(to bottom, 
                #6352c7 0%, 
                #4e3eb3 45%, 
                #44369e 50%, 
                #372b85 100%);
            color: rgba(255, 255, 255, 0.9); border: none;
            padding: 18px; border-radius: 12px; font-size: 1.1rem; font-weight: 700;
            cursor: pointer; position: relative;
            
            border-top: 1px solid rgba(255,255,255,0.2);
            border-bottom: 5px solid #1f1752;
            
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.6);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5);
            transition: all 0.1s;
        }

        .btn-ask:hover { 
            filter: brightness(1.15); 
            background: linear-gradient(to bottom, #6d5dd1 0%, #44369e 100%);
        }

        .btn-ask:active {
            transform: translateY(3px);
            border-bottom: 2px solid #1f1752;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5);
        }
        
        /* PULSE ANIMATION */
        @keyframes pulse-fade {
            0% { opacity: 0.3; } 50% { opacity: 0.6; } 100% { opacity: 0.3; }
        }
        .loading-pulse {
            animation: pulse-fade 1.5s infinite ease-in-out;
            color: rgba(255, 255, 255, 0.4);
            font-style: italic; text-align: center; padding: 20px;
        }

        #resultArea { margin-top: 30px; display: none; text-align: left; }
        .answer-box { 
            background: rgba(0, 0, 0, 0.3); border: 1px solid rgba(255,255,255,0.05); 
            border-radius: 15px; padding: 25px; white-space: pre-wrap; line-height: 1.6;
            box-shadow: inset 0 2px 10px rgba(0,0,0,0.6);
            transition: opacity 0.4s ease-in-out;
        }
        
        .related-title { margin-top: 25px; font-weight: 700; color: #6352c7; font-size: 0.9rem; }
        
        /* UPDATED: More visible and pop up effect */
        .related-q { 
            display: block; 
            background: rgba(255, 255, 255, 0.08); /* Brighter base */
            border: 1px solid rgba(255,255,255,0.15); /* Stronger border */
            padding: 15px 20px; 
            border-radius: 10px; margin-top: 12px;
            cursor: pointer; font-size: 0.9rem; 
            transition: all 0.25s ease; /* Smoother transition */
            color: rgba(255,255,255,0.9); /* Brighter text */
            box-shadow: 0 4px 6px rgba(0,0,0,0.2); /* Base shadow */
        }
        .related-q:hover { 
            background: rgba(255, 255, 255, 0.15); /* Brighter on hover */
            color: white; 
            border-color: rgba(255,255,255,0.3); /* Pop the border */
            transform: translateY(-2px); /* Pop up effect */
            box-shadow: 0 6px 12px rgba(0,0,0,0.4); /* Stronger shadow on hover */
        }

        .check-tag {
            display: inline-flex; margin-top: 25px; padding: 8px 18px;
            border-radius: 100px; background: rgba(99, 82, 199, 0.08);
            border: 1px solid rgba(99, 82, 199, 0.15); color: #7a68e8; font-size: 0.8rem;
        }

        .footer-section { text-align: center; max-width: 650px; margin-top: auto; }
        .disclaimer-container {
            border-top: 1px solid rgba(255, 255, 255, 0.08); padding-top: 25px;
            font-size: 0.75rem; color: rgba(255, 255, 255, 0.3);
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
            btn.innerText = "Processing...";
            aiAnswer.style.opacity = "0";
            
            setTimeout(() => {
                aiAnswer.innerHTML = '<div class="loading-pulse">Searching official codes...</div>';
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
                window.history.pushState({}, "", "/" + data.slug);
                
                aiAnswer.style.opacity = "0";
                
                setTimeout(() => {
                    aiAnswer.innerText = data.answer;
                    aiAnswer.style.opacity = "1";
                    relatedBox.innerHTML = "";
                    data.related.forEach(q => {
                        const div = document.createElement('div');
                        div.className = 'related-q';
                        let cleanQ = q.replace(/^\\d+[\\.\\)\\s]+/, '');
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

@app.get("/{slug}", response_class=HTMLResponse)
def dynamic_page(slug: str):
    # 🚨 BLOCK JUNK / HACKER SLUGS
    bad_words = [
        ".env", "debug", "php", "aws", "config",
        "login", "admin", "root", "sql", "backup",
        "test", "tmp", "cache"
    ]

    slug_lower = slug.lower()
    # 🔥 AUTO REDIRECT OLD NUMBERED SLUGS
    clean_slug = slugify(slug.replace("-", " "))

    # redirect only if slug starts with number OR exceeds length
    if slug != clean_slug and len(clean_slug) > 0:
        return RedirectResponse(url=f"/{clean_slug}", status_code=301)

    # BLOCK FILE REQUESTS
    if slug_lower.endswith((".ico", ".png", ".jpg", ".jpeg", ".css", ".js", ".json")):
        return HTMLResponse(content="Page not found", status_code=404)

    # Block dangerous patterns
    if any(word in slug_lower for word in bad_words):
        return HTMLResponse(content="Page not found", status_code=404)

    # Block weird slugs
    if len(slug) < 5 or "--" in slug:
        return HTMLResponse(content="Page not found", status_code=404)
    conn, cursor = get_cursor()
    cursor.execute("""
    SELECT question, answer, related
    FROM pages
    WHERE slug=%s
    """, (slug,))

    page = cursor.fetchone()
    conn.close()
    
    if not page:
        return HTMLResponse("Page not found", status_code=404)

    question = page[0]
    answer = page[1]
    related_json = page[2]
 
    # 🔥 REMOVE SERIAL NUMBERS FROM OLD QUESTIONS
    clean_question = re.sub(r'^\d+[\.\)\s]+', '', question)
    related = json.loads(related_json) if related_json else []
    
    # Generate related HTML using your SAME styling (Flattened string to prevent pre-wrap issues)
    related_html = ""
    for q in related:
        clean_q = q.replace('"', '').replace("'", "")
        related_html += f'<div class="related-q"><a href="/{slugify(clean_q)}" style="color:inherit; text-decoration:none; display:block;">{clean_q}</a></div>'

    # Extract SHORT ANSWER for meta description
    meta_summary = answer

    if "SHORT ANSWER:" in answer:
        try:
            meta_summary = answer.split("SHORT ANSWER:")[1].split("DETAILS:")[0].strip()
        except:
            meta_summary = answer

    # Clean meta summary
    meta_summary = meta_summary.replace("\n", " ").replace('"', '').strip()

    # Limit to 155 characters
    meta_summary = meta_summary[:155]
    
    # SEO HEAD CONTENT
    seo_head = f"""
        <title>{clean_question.title()} | RuleMate India</title>
        <meta name="description" content="{meta_summary}">
        <link rel="canonical" href="https://rulemate.in/{slug}">
    """

    html = home().replace(
        "<title>RuleMate India</title>",
        seo_head
    ).replace(
        '<div class="answer-box" id="aiAnswer"></div>',
        f'<div class="answer-box" id="aiAnswer">{answer}</div>'
    )

    # Structured Data (FAQ Schema)
    structured_data = f"""
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {{
                "@type": "Question",
                "name": "{clean_question}",
                "acceptedAnswer": {{
                    "@type": "Answer",
                    "text": "{meta_summary}"
                }}
            }}
        ]
    }}
    </script>
    """

    inject = f"""
    <script>
    window.onload = () => {{
        document.getElementById("resultArea").style.display = "block";
        document.getElementById("aiAnswer").innerText = {json.dumps(answer)};
        document.getElementById("userInput").value = `{clean_question}`;

        const relatedBox = document.getElementById("relatedQuestions");
        relatedBox.innerHTML = `{related_html}`;
    }};
    </script>
    """

    return html.replace("</body>", structured_data + inject + "</body>")


@app.get("/category/{category}", response_class=HTMLResponse)
def category_page(category: str):
    conn, cursor = get_cursor()
    cursor.execute("""
        SELECT slug, question FROM pages
        WHERE category=%s
        ORDER BY question
    """, (category,))

    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return HTMLResponse("<h2>No content found for this category yet.</h2>")

    links_html = ""

    for slug, question in rows:
        clean_q = re.sub(r'^\d+[\.\)\s]+', '', question)

        # Flattened string to prevent pre-wrap issues
        links_html += f'<div class="related-q"><a href="/{slug}" style="color:inherit; text-decoration:none; display:block;">{clean_q}</a></div>'

    title = category.replace("-", " ").title()

    seo_head = f"""
        <title>{title} | RuleMate India</title>
        <meta name="description" content="Complete guide about {title} rules, fines, penalties and laws in India.">
    """

    html = home().replace("<title>RuleMate India</title>", seo_head)

    content = f"""
    <script>
    window.onload = () => {{
        document.getElementById("resultArea").style.display = "block";
        document.getElementById("aiAnswer").innerHTML = `
        <h2>{title}</h2>
        <p>Below are all important questions related to this topic:</p>
        {links_html}
        `;
    }};
    </script>
    """

    return html.replace("</body>", content + "</body>")
