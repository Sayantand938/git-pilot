# utils/ai_utils.py
from google import genai
from config import GEMINI_API_KEY
import os
from datetime import datetime
import time
import random

client = genai.Client(api_key=GEMINI_API_KEY)
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "commit_template.txt")
LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "ai_raw_response.log")

MAX_RETRIES = 5
BASE_DELAY = 1  # seconds

def load_template():
    """Load commit template from file."""
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return f.read()

def log_raw_response(raw_text):
    """Append raw AI response to a log file with timestamp."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n--- {datetime.now().isoformat()} ---\n")
        f.write(repr(raw_text))
        f.write("\n-----------------------\n")

def clean_ai_fences(message: str) -> str:
    """Remove code fences (``` or ```<lang>) from the AI response."""
    lines = message.splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()

def clean_commit_body(message: str) -> str:
    """
    Keep summary on first line, combine the body into single paragraph
    but preserve bullet points.
    """
    lines = message.splitlines()
    if not lines:
        return message.strip()
    summary = lines[0].strip()
    body_lines = lines[1:]
    cleaned_body = []
    for line in body_lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            # keep bullet as a separate line
            cleaned_body.append(stripped)
        elif stripped:
            # append text to previous bullet or paragraph line
            if cleaned_body:
                cleaned_body[-1] += " " + stripped
            else:
                cleaned_body.append(stripped)
    if cleaned_body:
        return summary + "\n\n" + "\n".join(cleaned_body)
    return summary

def generate_commit_message(diff_text: str) -> str:
    """Generate AI commit message with exponential backoff and cleanup."""
    if not diff_text.strip():
        return "No changes to commit"

    template = load_template()

    prompt = (
        "You are a professional git commit assistant. Generate a commit message based on the following staged changes:\n\n"
        f"{diff_text}\n\n"
        f"Follow this template strictly:\n{template}\n\n"
        "Requirements:\n"
        "- Use imperative mood in the short summary (first line).\n"
        "- Include commit type (feat, fix, docs, style, refactor, test, chore).\n"
        "- Include optional scope if applicable.\n"
        "- Provide a short summary (≤50 chars), then the body.\n"
        "- Use bullet points (-) in the body to describe key changes or components.\n"
        "- Do NOT insert unnecessary line breaks inside bullets.\n"
        "- Return the commit message only, no explanations."
    )

    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            # Log the raw response
            log_raw_response(response.text)

            message = response.text if response.text else "No response from AI"

            # Clean fences and fix bullets/mid-line breaks
            message = clean_ai_fences(message)
            message = clean_commit_body(message)

            return message.strip()

        except Exception as e:
            attempt += 1
            delay = BASE_DELAY * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
            print(f"[Warning] AI request failed (attempt {attempt}/{MAX_RETRIES}): {e}")
            print(f"[Info] Retrying in {delay:.1f} seconds...")
            time.sleep(delay)

    print("[Error] Failed to generate commit message after multiple attempts.")
    return "AI commit message generation failed due to network/model issues."
