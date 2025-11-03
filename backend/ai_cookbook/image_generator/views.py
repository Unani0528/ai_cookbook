from django.shortcuts import render
from django.http import HttpResponse
from image_generator import image_generator

# Create your views here.
def index(request):
    # image_generator.generateImages([
    #     ("A fantasy landscape with castles and dragons", "test.png"),
    #     ("A futuristic city with flying cars", "test2.png"),
    # ])
    return HttpResponse("Hello, world. You're at the image generator index.")