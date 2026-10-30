
import json
import os
import urllib.request
import urllib.error
import markdown
import bleach
from pathlib import Path
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/"
    f"models/{GEMINI_MODEL}:generateContent"
)

OLLAMA_MODEL = "gemma3:1b"
OLLAMA_URL = "http://localhost:11434/api/generate"

print("AI MODE:", "GEMINI CLOUD" if GEMINI_API_KEY else "LOCAL OLLAMA")



BASE_DIR = Path(__file__).resolve().parent
STORIES_DIR = BASE_DIR / "stories"


def generate_story(topic, setting, mood):

    prompt = f"""
    You are Ghost of Code, a mysterious AI storyteller.

    Create an original spooky story.

    Topic: {topic}
    Setting: {setting}
    Mood: {mood}

    Requirements:
    - Give the story an interesting title.
    - Write approximately 250 words.
    - Include mysterious computer-related elements.
    - Make it entertaining and spooky.
    """

    # Use Gemini when the cloud API key is available
    if GEMINI_API_KEY:

        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.9,
                "maxOutputTokens": 1200
            }
        }

        req = urllib.request.Request(
            GEMINI_URL,
            data=json.dumps(data).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=180) as response:
                result = json.loads(
                    response.read().decode("utf-8")
                )

            candidates = result.get("candidates", [])

            if not candidates:
                return "Could not generate a story: Gemini returned no response."

            parts = candidates[0].get("content", {}).get("parts", [])

            story = "\n".join(
                part.get("text", "")
                for part in parts
                if part.get("text")
            ).strip()

            return story or "Could not generate a story: Gemini returned empty text."

        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")

            try:
                details = json.loads(details).get(
                    "error", {}
                ).get("message", error.reason)
            except json.JSONDecodeError:
                details = error.reason

            return f"Could not use Gemini API (HTTP {error.code}): {details}"

        except urllib.error.URLError as error:
            return f"Could not connect to Gemini: {error.reason}"

        except (TimeoutError, json.JSONDecodeError) as error:
            return f"Could not generate the story: {error}"

    # Otherwise use local Ollama
    data = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.9
        }
    }

    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))

        return result.get("response", "").strip()

    except urllib.error.HTTPError as error:
        return f"Ollama error: {error.code} {error.reason}"

    except urllib.error.URLError as error:
        return f"Could not connect to local Ollama: {error.reason}"

    except (TimeoutError, json.JSONDecodeError) as error:
        return f"Could not generate the story: {error}"



def save_story(topic, setting, mood, story):

    STORIES_DIR.mkdir(exist_ok=True)

    filename = datetime.now().strftime(
        "ghost_%Y%m%d_%H%M%S_%f.md"
    )

    file_path = STORIES_DIR / filename

    content = f"""# Ghost of Code

**Topic:** {topic}

**Setting:** {setting}

**Mood:** {mood}

---

{story}
"""

    file_path.write_text(content, encoding="utf-8")

    return filename


@app.route("/", methods=["GET", "POST"])
def home():

    story = ""
    story_html = ""
    error = ""
    topic = ""
    setting = ""
    mood = ""

    if request.method == "POST":

        topic = request.form.get("topic", "").strip()
        setting = request.form.get("setting", "").strip()
        mood = request.form.get("mood", "").strip()

        if not topic or not setting or not mood:
            error = "Please fill in all fields."

        elif len(topic) > 100 or len(setting) > 150:
            error = "Please keep your inputs shorter."

        else:
            result = generate_story(topic, setting, mood)

            if result.startswith(("Ollama error:", "Could not ")):
                error = result
            elif result:
                story = result
                story_html = format_story(story)
                save_story(topic, setting, mood, story)

            else:
                error = "The AI returned an empty story."

    return render_template(
        "index.html",
        story=story,
        story_html=story_html,
        error=error,
        topic=topic,
        setting=setting,
        mood=mood
    )

def format_story(story):

    allowed_tags = {
        "p", "br", "strong", "em",
        "h1", "h2", "h3",
        "ul", "ol", "li",
        "blockquote", "code", "pre", "hr"
    }

    html = markdown.markdown(
        story,
        extensions=["fenced_code"]
    )

    safe_html = bleach.clean(
        html,
        tags=allowed_tags,
        attributes={},
        strip=True
    )

    return safe_html

@app.route("/saved-stories")
def saved_stories():
    stories = []

    if STORIES_DIR.exists():
        for file_path in STORIES_DIR.glob("*.md"):
            content = file_path.read_text(encoding="utf-8")

            # Get the actual story title
            title = file_path.stem

            for line in content.splitlines():
                line = line.strip()

                if line.startswith("#"):
                    heading = line.lstrip("#").strip()

                    if heading.lower() != "ghost of code":
                        title = heading
                        break

            stories.append({
                "filename": file_path.name,
                "title": title,
                "content": content,
                "date": datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).strftime("%d %B %Y, %I:%M %p")
            })

    stories.sort(
        key=lambda story: story["filename"],
        reverse=True
    )

    return render_template("saved_stories.html", stories=stories)


@app.template_filter("markdown_filter")
def markdown_filter(text):
    html = markdown.markdown(
        text,
        extensions=["fenced_code"]
    )

    return bleach.clean(
        html,
        tags={
            "p", "br", "strong", "em",
            "h1", "h2", "h3",
            "ul", "ol", "li",
            "blockquote", "code", "pre", "hr"
        },
        attributes={},
        strip=True
    )

@app.route("/read-story/<filename>")
def read_story(filename):

    if Path(filename).name != filename or not filename.endswith(".md"):
        return "Invalid story filename", 400

    file_path = STORIES_DIR / filename

    if not file_path.is_file():
        return "Story not found", 404

    content = file_path.read_text(encoding="utf-8")
    story_html = format_story(content)

    return render_template(
        "read_story.html",
        story_html=story_html,
        filename=filename
    )


@app.route("/delete-story/<filename>", methods=["POST"])
def delete_story(filename):

    if Path(filename).name != filename or not filename.endswith(".md"):
        return "Invalid story filename", 400

    file_path = STORIES_DIR / filename

    if file_path.is_file():
        file_path.unlink()

    return redirect(url_for("saved_stories"))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
