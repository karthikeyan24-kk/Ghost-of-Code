
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

MODEL = "gemma3:1b"
API_URL = "http://localhost:11434/api/generate"

# Project folder and story storage folder
BASE_DIR = Path(__file__).resolve().parent
STORIES_DIR = BASE_DIR / "stories"


def generate_story(topic, setting, mood):

    prompt = f"""
    You are the Ghost of Code, a spooky AI storyteller.

    Create an original ghost story using these details:

    Topic: {topic}
    Setting: {setting}
    Mood: {mood}

    Write an interesting title.
    Make the story mysterious and entertaining.
    Aim for approximately 250 words.
    """

    data = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))

        return result["response"]

    except urllib.error.URLError as error:
        print("\nCould not connect to Ollama.")
        print("Check whether Ollama is running.")
        print("Error:", error)
        return None


def save_story(topic, setting, mood, story):

    STORIES_DIR.mkdir(exist_ok=True)

    filename = datetime.now().strftime(
        "ghost_%Y%m%d_%H%M%S.md"
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

    print("\nStory saved successfully!")
    print("File location:", file_path)


def main():

    print("=" * 45)
    print("       GHOST OF CODE")
    print("   Local AI Ghost Story Generator")
    print("=" * 45)

    while True:

        topic = input("\nEnter your topic (or exit): ").strip()

        if topic.lower() in ("exit", "quit"):
            print("The ghost disappears. Goodbye!")
            break

        setting = input("Enter the setting: ").strip()
        mood = input("Enter the mood: ").strip()

        if not topic or not setting or not mood:
            print("Please enter all three details.")
            continue

        print("\nThe ghost is writing your story...\n")

        story = generate_story(topic, setting, mood)

        if story:
            print("\n" + story)

            save_story(topic, setting, mood, story)


if __name__ == "__main__":
    main()
