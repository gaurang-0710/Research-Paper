from django.shortcuts import render

def home_page(request):
    if request.method == "POST":
        file_type = request.POST.get('type')
        print(file_type)
    return render(request, "home.html")