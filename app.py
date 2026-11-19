import os
from flask import Flask, render_template, jsonify, request
from pathlib import Path
import csv
import re
from difflib import SequenceMatcher

try:
    from rapidfuzz import fuzz, process
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "products.csv"

def clean(value):
    value = str(value or "").lower().strip()
    value = re.sub(r"[^a-z0-9.%+\s-]", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def load_products():
    products = []

    if not CSV_PATH.exists():
        return products

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames or "Product" not in reader.fieldnames:
            raise ValueError("CSV must contain a Product column")

        for row in reader:
            name = (row.get("Product") or "").strip()

            if name and name.lower() not in {"test", "nan", "none"}:
                products.append({
                    "name": name,
                    "aliases": [name]
                })

    # Remove duplicate product names
    unique_products = {}
    for product in products:
        key = clean(product["name"])
        if key not in unique_products:
            unique_products[key] = product

    return list(unique_products.values())
# Load products from the CSV file
PRODUCTS = load_products()

# Create product alias mapping
ALIAS_MAP = {}

for product in PRODUCTS:
    for alias in product["aliases"]:
        ALIAS_MAP[clean(alias)] = product


def number_from_tokens(tokens):
    number_words = {
        "zero": 0, "one": 1, "two": 2, "three": 3,
        "four": 4, "five": 5, "six": 6, "seven": 7,
        "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "thirteen": 13,
        "fourteen": 14, "fifteen": 15, "sixteen": 16,
        "seventeen": 17, "eighteen": 18, "nineteen": 19,
        "twenty": 20, "thirty": 30, "forty": 40,
        "fifty": 50, "sixty": 60, "seventy": 70,
        "eighty": 80, "ninety": 90,
        "hundred": 100
    }

    ignored = {
        "quantity", "is", "are", "of", "pieces", "piece",
        "units", "unit", "boxes", "box", "no", "number"
    }

    for i, token in enumerate(tokens):
        if token.isdigit():
            return int(token)

        if token not in number_words:
            continue

        total = 0
        current = 0
        found = False

        for word in tokens[i:]:
            if word in ignored or word == "and":
                continue

            if word not in number_words:
                break

            found = True
            value = number_words[word]

            if value == 100:
                current = max(1, current) * 100
            elif value >= 20:
                current += value
            else:
                current += value

        if found:
            return total + current

    return None


def locate_aliases(transcript):
    """Find product aliases in transcript, preferring longer phrases."""
    tokens = clean(transcript).split()
    matches = []
    aliases = sorted(ALIAS_MAP.keys(), key=lambda x: len(x.split()), reverse=True)
    occupied = set()
    for alias in aliases:
        a = alias.split()
        n = len(a)
        if not n:
            continue
        for start in range(0, len(tokens) - n + 1):
            end = start + n
            if any(i in occupied for i in range(start, end)):
                continue
            phrase = " ".join(tokens[start:end])
            score = 100 if phrase == alias else 0
            if HAS_RAPIDFUZZ:
                score = fuzz.ratio(phrase, alias)
            else:
                score = int(SequenceMatcher(None, phrase, alias).ratio() * 100)
            # Exact alias phrases are accepted; fuzzy matching is conservative.
            if score >= (86 if len(alias) > 5 else 92):
                matches.append({"start": start, "end": end, "alias": alias, "score": score, "product": ALIAS_MAP[alias]})
                occupied.update(range(start, end))
                break
    return sorted(matches, key=lambda x: x["start"])


def extract_quantity(tokens, start, end, next_start):

    # First check immediately after the product name
    after = tokens[end:min(next_start, end + 8)]

    qty = number_from_tokens(after)

    if qty is not None:
        return qty

    # Also support quantity before the product name
    before = tokens[max(0, start - 6):start]

    qty = number_from_tokens(before)

    if qty is not None:
        return qty

    # Do not assume quantity is 1
    return None

def process_transcript(transcript):
    tokens = clean(transcript).split()
    found = locate_aliases(transcript)

    result = []
    unmatched = []

    for i, item in enumerate(found):
        next_start = (
            found[i + 1]["start"]
            if i + 1 < len(found)
            else len(tokens)
        )

        qty = extract_quantity(
            tokens,
            item["start"],
            item["end"],
            next_start
        )

        p = item["product"]

        result.append({
            "name": p["name"],
            "quantity": qty if qty is not None and qty > 0 else "",
            "confidence": item["score"]
        })

    if not result:
        unmatched = [transcript.strip()] if transcript.strip() else []

    # Combine duplicate products safely
    combined = {}

    for row in result:
        key = clean(row["name"])

        if key in combined:
            old_qty = combined[key]["quantity"]
            new_qty = row["quantity"]

            if old_qty != "" and new_qty != "":
                combined[key]["quantity"] = int(old_qty) + int(new_qty)
            else:
                combined[key]["quantity"] = ""

        else:
            combined[key] = row.copy()

    return {
        "items": list(combined.values()),
        "unmatched": unmatched
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/process")
def api_process():
    data = request.get_json(silent=True) or {}
    transcript = str(data.get("transcript", "")).strip()

    if not transcript:
        return jsonify({
            "items": [],
            "unmatched": [],
            "error": "No speech text was received."
        }), 400

    return jsonify(process_transcript(transcript))


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "products_loaded": len(PRODUCTS)
    })


if __name__ == "__main__":
    print(f"Loaded {len(PRODUCTS)} product records from {CSV_PATH.name}")

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )