import os
from django.shortcuts import render
from dotenv import  load_dotenv
import fitz  # pymupdf
import requests
from django.core.files.storage import default_storage
from gtts import gTTS
from .helpers import generate_final_video

load_dotenv()

def extract_text(pdf_path):
    doc = fitz.open(pdf_path, filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text()

    return full_text

def text_explanation(text_chunk):
    open_router_api = os.getenv("OPENROUTER_API_KEY")  # now loaded via dotenv
    if not open_router_api:
        raise Exception("Missing OPENROUTER_API_KEY in environment.")
    payload = {
        "model": "mistralai/mistral-7b-instruct:free",
        "messages": [
            {"role": "user", "content": f"""\
            You are an AI assistant specialized in breaking down complex academic papers into simple, easy-to-understand explanations. Your goal is to help someone with no background in the field understand each part of the research paper clearly.

            Please read the following text from a research paper and explain it section by section in plain English:
            - For each section (e.g., Abstract, Introduction, Methodology, Results, Discussion), provide a clear and concise summary.
            - Avoid technical jargon or explain it when necessary.
            - Highlight the main idea, why it matters, and what problem the paper is trying to solve.
            - Use bullet points or short paragraphs for readability.

            Here’s the paper content:

            {text_chunk}
            """},
            {"role": "user", "content": f"Explain this paper in simple English:\n\n{text_chunk}"}
        ]
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {open_router_api}",
            "Content-Type": "application/json"
        },
        json=payload
    )

    try:
        data = response.json()
    except Exception as e:
        raise Exception(f"Failed to parse response JSON: {e}\nRaw response: {response.text}")

    if response.status_code != 200:
        raise Exception(f"API Error {response.status_code}: {data}")

    if "choices" not in data:
        raise Exception(f"Unexpected API response format: {data}")

    return data["choices"][0]["message"]["content"]


def audio_explanation(text):
    VOICE_PATH = "output/voice.mp3"

    tts = gTTS(text)
    tts.save(VOICE_PATH)

def video_explanation():
    print("video explanation")
    return "video explanation"

def home_page(request):
    context = {}
    if request.method == "POST":
        file_type = request.POST.get('type')
        pdf_file = request.FILES.get('pdf')
        if pdf_file:
            # Save PDF temporarily
            file_path = default_storage.save(f'media/media/temp/{pdf_file.name}', pdf_file)
            full_path = default_storage.path(file_path)

            # Extract text and explanation
            text_chunk = extract_text(pdf_path=full_path)
            explanation = text_explanation(text_chunk)

            # Handle output type
            if file_type == "text":
                context["output_type"] = "text"
                context["explanation"] = explanation

            elif file_type == "audio":
                tts = gTTS(explanation)
                audio_path = "media/voice.mp3"
                tts.save(audio_path)
                context["output_type"] = "audio"
                context["audio_url"] = "/" + audio_path  # for <audio> src

            elif file_type == "video":
                video_path = generate_final_video(explanation)
                context["output_type"] = "video"
                context["video_url"] = "/" + video_path  # for <video> src

            default_storage.delete(file_path)

    return render(request, "home.html", context)