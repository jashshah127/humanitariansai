"""Plain-prompt JSON (A) vs schema-enforced output (C) for physics problem tagging."""
import json, os, time, urllib.request, urllib.error

KEY = os.environ["GEMINI_API_KEY"]
BASE = "https://generativelanguage.googleapis.com/v1beta"
MODELS = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-flash-latest", "gemini-flash-lite-latest"]
TOPICS = ["Mechanics", "E&M", "Thermodynamics", "Other"]
SUBTOPICS = ["Kinematics", "Dynamics", "Work & Energy", "Momentum", "Rotation", "Gravitation",
             "Vibrations and Waves", "Electrostatics", "Circuits", "Magnetism", "Induction",
             "Gas Laws", "Calorimetry", "Heat Engines", "Entropy", "Laws", "Other"]
GRADES = ["high_school", "intro_undergrad", "upper_undergrad", "graduate"]   # placeholder
DIFFICULTY = ["easy", "medium", "hard"]                                      # placeholder
PROBLEMS = [
    "Two blocks of mass 4 kg and 6 kg are connected by a string over a frictionless pulley. Find the acceleration and the tension.",
    "A 0.5 kg mass on a spring of constant 200 N/m has a damping constant of 1.2 kg/s. Find the damped oscillation frequency.",
    "Find the energy of the n = 2 level of a hydrogen atom.",
]

def http(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"X-goog-api-key": KEY, "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())

def ask(prompt, schema=None):
    cfg = {"temperature": 0}
    if schema:
        cfg.update({"responseMimeType": "application/json", "responseSchema": schema})
    body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": cfg}
    for model in MODELS:
        for wait in (5, 10, 20, 40):
            time.sleep(7)                                         # free-tier pacing
            try:
                d = http(f"{BASE}/models/{model}:generateContent", body)
                return model, d["candidates"][0]["content"]["parts"][0]["text"]
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    print(f"     ({model}: 404 not available to this key, skipping)"); break
                if e.code in (429, 503):
                    print(f"     ({model}: {e.code}, retrying in {wait}s)"); time.sleep(wait); continue
                raise SystemExit(f"{model}: error {e.code} (not retryable): {e.read().decode()[:200]}")
        else:
            print(f"     ({model} kept failing; falling back to next model)")
    raise SystemExit("all models unavailable right now - try again in a few minutes")

def check(raw):
    try:
        d = json.loads(raw)
    except json.JSONDecodeError:
        return "NOT valid JSON as-is", None
    bad = [k for k, allowed in (("topic", TOPICS), ("subtopic", SUBTOPICS), ("grade", GRADES), ("difficulty", DIFFICULTY))
           if d.get(k) not in allowed]
    return ("valid JSON, all values allowed" if not bad else f"valid JSON, but bad/missing: {bad}"), d

lists = f"topic: {TOPICS}\nsubtopic: {SUBTOPICS}\ngrade: {GRADES}\ndifficulty: {DIFFICULTY}"
SCHEMA = {"type": "OBJECT", "required": ["topic", "subtopic", "grade", "difficulty", "confidence"],
          "properties": {"topic": {"type": "STRING", "enum": TOPICS},
                         "subtopic": {"type": "STRING", "enum": SUBTOPICS},
                         "grade": {"type": "STRING", "enum": GRADES},
                         "difficulty": {"type": "STRING", "enum": DIFFICULTY},
                         "confidence": {"type": "NUMBER"}}}

print("trying models in order:", MODELS)
for i, p in enumerate(PROBLEMS, 1):
    print(f"\n=== Problem {i}: {p[:70]}...")
    m, raw_a = ask(f"Classify this physics problem. Reply with JSON containing topic, subtopic, grade, difficulty, "
                   f"confidence (0-1). Use only these values:\n{lists}\n\nProblem: {p}")
    verdict, _ = check(raw_a)
    print(f"  A. prompt only [{m}]: {verdict}")
    print(f"     raw reply starts: {raw_a.strip()[:60]!r}")
    m, raw_c = ask(f"Classify this physics problem. Use 'Other' if no listed topic fits. Confidence is 0-1.\n\nProblem: {p}", SCHEMA)
    verdict, d = check(raw_c)
    print(f"  C. schema      [{m}]: {verdict}")
    if d:
        print(f"     -> {d.get('topic')} / {d.get('subtopic')} / {d.get('grade')} / {d.get('difficulty')} / confidence {d.get('confidence')}")
