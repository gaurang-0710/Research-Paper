import os
from django.shortcuts import render
from dotenv import  load_dotenv

load_dotenv()



def text_explanation():
    print("text explanation")
    return "text explanation"


def audio_explanation():
    print("audio explanation")
    return "audio explanation"

def video_explanation():
    print("video explanation")
    return "video explanation"

def home_page(request):
    if request.method == "POST":
        file_type = request.POST.get('type')
        if file_type == "text":
            text_explanation()
        elif file_type == "audio":
            audio_explanation()
        else:
            video_explanation()

    return render(request, "home.html")