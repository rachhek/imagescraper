from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
from django.template import loader
from .forms import WebsiteForm
from urllib.parse import urlparse
from .models import Image, Website
import tempfile
from django.core import files
from django.conf import settings
import zipfile
from wsgiref.util import FileWrapper
import logging
from .lib import ScraperTool
import os

logger = logging.getLogger(__name__)


def index(request):
    scraped_images = []
    details = {}
    if request.method == "POST":
        form = WebsiteForm(request.POST)
        if form.is_valid():
            # save websiteurl to db
            website = form.save()

            # Instantiate Image scraper class
            scraperTool = ScraperTool()
            scraped_images = scraperTool.visit_url(website)
            details = {"website": website, "storage": settings.MEDIA_URL,
                       "image_count": len(scraped_images)}

    form = WebsiteForm()
    context = {'form': form, 'images': scraped_images, "details": details}
    return render(request, 'scraper_app/index.html', context)


def downloadZip(request, websiteId):
    zf = zipfile.ZipFile("images.zip", "w")

    # Get all the images urls downloaded from the website
    filtered_images = Image.objects.filter(website=websiteId)
    for image in filtered_images:
        current_file = settings.BASE_DIR + image.image_file.url
        url_path = urlparse(current_file).path
        file_name = os.path.basename(url_path)
        zf.write(current_file, file_name)
    zf.close()
    wrapper = FileWrapper(open('images.zip', 'rb'))
    content_type = 'application/zip'
    content_disposition = 'attachment; filename=images.zip'
    response = HttpResponse(wrapper, content_type=content_type)
    response['Content-Disposition'] = content_disposition
    return response
