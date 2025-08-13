import os, re, json
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
app = Flask(__name__)

def parse_transcript(raw: str):
    """Parses transcripts that contain headers like 'You said:' / 'ChatGPT said:'.
       Also strips obvious boilerplate lines."""
    if not raw.strip():
        return []

    # Remove common boilerplate, export UI junk
    raw = re.sub(r"^(Skip to content|Report conversation)\s*$", "", raw, flags=re.MULTILINE|re.IGNORECASE)
    raw = re.sub(r"No file chosenNo file chosen", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"New version of GPT available.*", "", raw, flags=re.IGNORECASE)

    lines = raw.splitlines()
    turns, role, buf = [], None, []

    def flush():
        nonlocal buf, role, turns
        if role and buf:
            content = "\n".join(buf).strip()
            if content:
                turns.append({"role": role, "content": content})
        buf = []

    for line in lines:
        s = line.strip()

        if re.match(r"^you said:\s*$", s, flags=re.IGNORECASE):
            flush(); role = "user"; continue
        if re.match(r"^chatgpt said:\s*$", s, flags=re.IGNORECASE):
            flush(); role = "assistant"; continue

        if role is None and not s:
            continue

        buf.append(s)

    flush()

    if not turns:
        turns = [{"role": "user", "content": raw.strip()}]

    return turns

DEVELOPER_TEXT = '''
    You are a language assessment expert.
'''
INPUT_TEXT = '''
Above is a transcript of a learner interacting with ChatGPT to practice Japanese.
Evaluate the transcript on five metrics:
1. Fluency (0-5) 
2. Coherence (0-5) 
3. Complexity (0-5)
4. Engagement (0-5)
5. Frustration (0-5)

Without preamble, respond with:
{
    "fluency": {
        "score": 0-5,
        "confidence": 0.0-1.0, 
        "evidence": "Provide specific examples or explanations supporting the fluency rating"
    },
    "coherence": {
        "score": 0-5,
        "confidence": 0.0-1.0, 
        "evidence": "Provide specific examples or explanations supporting the coherence rating"
    },
    "complexity": {
        "score": 0-5,
        "confidence": 0.0-1.0, 
        "evidence": "Provide specific examples or explanations supporting the complexity rating"
    },
    "engagement": { 
        "score": 0-5,
        "confidence": 0.0-1.0, 
        "evidence": "Cues for engagement level" 
    },
    "frustration": { 
        "score": 0-5,
        "confidence": 0.0-1.0, 
        "evidence": "Cues for frustration level" 
    }
}
'''

MIN_TEMP = 0.0
MAX_TEMP = 2.0
def call_openai_with_messages(turns, temp):
    """
    Uses chat.completions (as in your snippet).
    We pass your developer_text, then the parsed turns, then your user instruction.
    """
    # Keep tokens sane
    MAX_CHARS = 3000
    compact = [{"role": t["role"], "content": t["content"][:MAX_CHARS]} for t in turns]

    messages = [{"role":"developer","content": DEVELOPER_TEXT}] + compact + [{"role":"user","content": INPUT_TEXT}]

    resp = client.chat.completions.create(
        model="gpt-4.1",
        temperature=temp,
        messages=messages
    )

    text = resp.choices[0].message.content.strip() if resp and resp.choices else ""
    return text

def coerce_to_scores(text):
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    candidate = m.group(0) if m else text
    try:
        data = json.loads(candidate)
        # normalize keys/fields a bit
        def norm(k): return k.strip().lower()
        out = {}
        for k in ["fluency","coherence","complexity","engagement","frustration"]:
            v = data.get(k) or data.get(norm(k)) or {}
            score = v.get("score")
            confidence = v.get("confidence")
            ev = v.get("evidence") or ""
            out[k] = {"score": score, "confidence": confidence, "evidence": ev}
        return out
    except Exception:
      fallback = {"score": None, "confidence": None, "evidence": text}
      return {
          "fluency": fallback,
          "coherence": fallback,
          "complexity": fallback,
          "engagement": fallback,
          "frustration": fallback,
      }


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(force=True)
    raw = (data.get("transcript") or "").strip()

    if not raw:
      return jsonify({"error": "Empty transcript"}), 400
    try:
        temp = float(data.get("temperature", MIN_TEMP))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid temperature (must be a number)"}), 400
    temp = max(MIN_TEMP, min(MAX_TEMP, temp))

    turns = parse_transcript(raw)
    model_text = call_openai_with_messages(turns, temp)
    scores = coerce_to_scores(model_text)

    return jsonify({"scores": scores, "turns": turns, "temperature": temp})

if __name__ == "__main__":
    app.run(debug=True)
