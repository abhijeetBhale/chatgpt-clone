from groq import Groq
from settings import settings

groq_client = Groq(api_key=settings.GROQ_API_KEY)


async def generate_chat_title(history: list[dict]) -> str:
    """Generate a short, concise title for a chat conversation using Groq."""
    try:
        messages = [
            {
                "role": "system",
                "content": "Generate a short, concise title (max 40 characters) for this chat conversation. Only return the title, no quotes or extra text.",
            },
        ]

        for msg in history:
            role = "assistant" if msg.get("role") == "model" else "user"
            text = ""
            if msg.get("parts") and len(msg["parts"]) > 0:
                text = msg["parts"][0].get("text", "")[:200]
            messages.append({"role": role, "content": text})

        completion = groq_client.chat.completions.create(
            messages=messages,
            model="llama-3.1-8b-instant",
            max_tokens=50,
            temperature=0.3,
        )

        title = completion.choices[0].message.content.strip().strip("\"'")[:40]
        print(f"Generated title: {title}")
        return title
    except Exception as e:
        print(f"Title generation failed: {e}")
        return ""
