
from django.conf import settings
from django.core import files
import tempfile
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from .models import Image, Website
import requests
import re
import os
import urllib.request
import cssutils
import logging
logger = logging.getLogger(__name__)


class ScraperTool:
    def visit_url(self, website):
        content = requests.get(website.url).content
        soup = BeautifulSoup(content, "lxml")

        # Scraping the HTML tags for images
        self.scrape_html(soup, website)

        # Scraping the CSS from the HTML Tags for images
        self.scrape_css(soup, website)

        # Retreiving all the Image objects downloaded for this particular website
        image_objects = Image.objects.filter(website=website.id)
        return [image_obj.image_file.url for image_obj in image_objects]

    def scrape_html(self, soup, website):
        # Parse the HTML for <img> tags
        img_tags = soup.find_all("img")
        for tag in img_tags:
            src = tag.get("src")
            # Converting the image url to absolute path if it is relative
            if not urlparse(src).netloc:
                src = (
                    urlparse(website.url).scheme
                    + "://"
                    + urlparse(website.url).netloc
                    + "/"
                    + src
                )

            self.download_image(src, website)

    def scrape_css(self, soup, website):
        # Parse the HTML for tage with inline css like
        # <div style="background-image: url('/image.jpg');"></div>

        tags_with_style = soup.find_all(lambda tag: tag.has_attr("style"))
        for tag in tags_with_style:
            style_content = tag.get("style")
            style = cssutils.parseStyle(style_content)
            src = style["background-image"]

            if src:
                # extracting the path only
                src = src.replace("url(", "").replace(")", "")
                # Converting the image url to absolute path if it is relative
                if not urlparse(src).netloc:
                    src = (
                        urlparse(website.url).scheme
                        + "://"
                        + urlparse(website.url).netloc
                        + "/"
                        + src
                    )

                self.download_image(src, website)

    def download_image(self, src, website):
        # building the outpath
        url_path = urlparse(src).path

        # Prepend with website.id to make it unique
        file_name = str(website.id) + "_" + os.path.basename(url_path)
        request = requests.get(src, stream=True)

        # Checking if the result was fetched properly
        if request.status_code != requests.codes.ok:
            logger.error("Couldn't download image {}".format(src))
            return

        lf = tempfile.NamedTemporaryFile()
        for block in request.iter_content(1024 * 8):
            if not block:
                break
            lf.write(block)

        # Saving the image to the database. Also stores it in the folder /media/images
        image = Image()
        image.website = website
        image.image_file.save(file_name, files.File(lf))

        # append url to the file
        self.append_url_to_file(src, website)

    def append_url_to_file(self, src, website):
        # The url path for the .txt file is set by default. Check Models.py
        out_path = settings.BASE_DIR + website.img_urls_file
        file_object = open(out_path, "a+")
        file_object.write(src + "\n")
        file_object.close()
