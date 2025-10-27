from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, constr
from typing import Annotated
from enum import Enum

app = FastAPI(title="AI Greeting Bot", version="0.1.0")

# ---- Domain enums & models ----

class Mood(str, Enum):
    happy = "happy"
    neutral = "neutral"
    tired = "tired"
    excited = "excited"
    sad = "sad"

class GreetRequest(BaseModel):
    # constr: min/max length + trims type to str
    name: Annotated[str, Field(strip_whitespace=True, min_length=1, max_length=50)]
    mood: Mood = Field(..., description="User mood to tailor the tone")
    language: str = Field("en", description="Language code: 'en' or 'hi'")
    time_of_day: str | None = Field(
        None,
        description="Optional hint like 'morning', 'afternoon', 'evening'"
    )

class GreetResponse(BaseModel):
    message: str
    tone: str
    tips: list[str] = []

# ---- Helpers ----

def craft_message(name: str, mood: Mood, language: str, time_of_day: str | None) -> tuple[str, str, list[str]]:
    # very simple “rule-based” personalization to show structure
    tod_prefix = {
        "morning": {"en": "Good morning", "hi": "सुप्रभात"},
        "afternoon": {"en": "Good afternoon", "hi": "नमस्ते"},
        "evening": {"en": "Good evening", "hi": "शुभ संध्या"},
    }
    hello = {"en": "Hello", "hi": "नमस्ते"}

    # choose greeting
    if time_of_day and time_of_day.lower() in tod_prefix:
        base = tod_prefix[time_of_day.lower()].get(language, hello.get(language, "Hello"))
    else:
        base = hello.get(language, "Hello")

    # tone & tips
    tone = "friendly"
    tips: list[str] = []
    if mood == Mood.tired:
        tone = "gentle"
        tips.append("Take a short break and hydrate.")
    elif mood == Mood.excited:
        tone = "energetic"
        tips.append("Channel that energy into your top task for 25 minutes.")
    elif mood == Mood.sad:
        tone = "supportive"
        tips.append("A short walk or a call with a friend can help.")

    message = f"{base}, {name}! Hope you’re doing {mood.value}."
    return message, tone, tips

def validate_language(code: str) -> None:
    if code.lower() not in {"en", "hi"}:
        # Demonstrates a custom 400 error instead of generic 422
        raise HTTPException(status_code=400, detail="Unsupported language. Use 'en' or 'hi'.")

# ---- Endpoint ----

@app.post("/greet", response_model=GreetResponse, status_code=200)
def greet(payload: GreetRequest):
    # extra validation/business rules
    validate_language(payload.language)

    # simple guardrail example: names shouldn’t be all digits
    if payload.name.isdigit():
        raise HTTPException(status_code=400, detail="Name cannot be all digits.")

    msg, tone, tips = craft_message(
        name=payload.name,
        mood=payload.mood,
        language=payload.language.lower(),
        time_of_day=payload.time_of_day
    )
    return GreetResponse(message=msg, tone=tone, tips=tips)

# ---- Health check (useful for uptime monitoring) ----
@app.get("/health")
def health():
    return {"status": "ok"}
