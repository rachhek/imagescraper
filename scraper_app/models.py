from django.db import models
from django.conf import settings
import uuid


def get_default_file_out_path():
    return settings.MEDIA_URL + str(uuid.uuid1()) + ".txt"


class Website(models.Model):
    url = models.URLField()

    # the path for the text file with all the downloaded URLs
    img_urls_file = models.URLField(
        default=get_default_file_out_path)


class Image(models.Model):
    image_file = models.ImageField(
        upload_to='images'
    )
    website = models.ForeignKey(Website, on_delete=models.CASCADE)
