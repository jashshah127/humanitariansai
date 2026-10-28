"""Self-reported confidence vs self-consistency (agreement across repeated runs)."""
import json, os, time, urllib.request, urllib.error
from collections import Counter

KEY = os.environ["GEMINI_API_KEY"]
BASE = "https://generativelanguage.googleapis.com/v1beta"
MODELS = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-flash-latest", "gemini-flash-lite-latest"]
RUNS = 5
TOPICS = ["Mechanics", "E&M", "Thermodynamics", "Other"]
SUBTOPICS = ["Kinematics", "Dynamics", "Work & Energy", "Momentum", "Rotation", "Gravitation",
             "Vibrations and Waves", "Electrostatics", "Circuits", "Magnetism", "Induction",
             "Gas Laws", "Calorimetry", "Heat Engines", "Entropy", "Laws", "Other"]
SCHEMA = {"type": "OBJECT", "required": ["topic", "subtopic", "confidence"],
          "properties": {"topic": {"type": "STRING", "enum": TOPICS},
                         "subtopic": {"type": "STRING", "enum": SUBTOPICS},
                         "confidence": {"type": "NUMBER"}}}
PROBLEMS = [
    ("clear",     "Two blocks of mass 4 kg and 6 kg are connected by a string over a frictionless pulley. Find the acceleration and the tension."),
    ("ambiguous", "A 0.2 kg charged ball hangs from a string in a uniform horizontal electric field and makes a 10 degree angle with the vertical. Find the tension in the string."),
    ("clear",     "An engine operates between 800 K and 300 K. What is its maximum possible efficiency?"),
]

def ask(prompt):
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 1.0, "responseMimeType": "application/json", "responseSchema": SCHEMA}}
    for model in MODELS:
        for wait in (5, 10, 20, 40):
            time.sleep(7)
            try:
                req = urllib.request.Request(f"{BASE}/models/{model}:generateContent", data=json.dumps(body).encode(),
                                             headers={"X-goog-api-key": KEY, "Content-Type": "application/json"})
                d = json.loads(urllib.request.urlopen(req, timeout=60).read())
                return model, json.loads(d["candidates"][0]["content"]["parts"][0]["text"])
            except urllib.error.HTTPError as e:              # the server answered with an error code
                if e.code == 404:
                    break
                if e.code in (429, 503):
                    print(f"     ({model}: {e.code}, retrying in {wait}s)"); time.sleep(wait); continue
                raise SystemExit(f"{model}: error {e.code}: {e.read().decode()[:200]}")
            except (TimeoutError, urllib.error.URLError, ConnectionError) as e:   # no answer at all
                print(f"     ({model}: no response - {type(e).__name__}, retrying in {wait}s)"); time.sleep(wait); continue
    raise SystemExit("all models unavailable right now - try again in a few minutes")

for kind, p in PROBLEMS:
    print(f"\n=== [{kind}] {p[:80]}...")
    answers, confs, models = [], [], []
    for _ in range(RUNS):
        m, d = ask(f"Classify this physics problem. Use 'Other' if no listed topic fits. Confidence is 0-1.\n\nProblem: {p}")
        answers.append(f"{d['topic']} / {d['subtopic']}"); confs.append(d["confidence"]); models.append(m)
    top, n = Counter(answers).most_common(1)[0]
    print(f"  answers           : {dict(Counter(answers))}")
    print(f"  agreement         : {n}/{RUNS} on '{top}'")
    print(f"  self-confidence   : min {min(confs):.2f}  avg {sum(confs)/len(confs):.2f}  max {max(confs):.2f}")
    print(f"  models used       : {dict(Counter(models))}")
