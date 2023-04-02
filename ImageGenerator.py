from os import remove
from PIL import Image
from platform import system
import openai
import requests

class ImageGenerator():

    def __init__(self, key):
        self.KEY = key

        if system() == "Windows":
            self.conjoiner = "\\"
        else:
            self.conjoiner = "/"

    def generateImage(self, imageLocation, saveLocation):
        
        image = Image.open(imageLocation)
        if imageLocation[-3:] != 'png':
            image.save(imageLocation[:-3]+'png')
            remove(imageLocation)
            imageLocation = imageLocation[:-3]+'png'
        imageSize = image.size
        if imageSize[0] > imageSize[1]:
            image = image.crop((0, 0, imageSize[1], imageSize[1]))
            image.save(imageLocation[:-4]+"_altered.png")
            remove(imageLocation)
            imageLocation = imageLocation[:-4]+"_altered.png"
        if imageSize[1] > imageSize[0]:
            image = image.crop((0, 0, imageSize[0], imageSize[0]))
            image.save(imageLocation[:-4]+"_altered.png")
            remove(imageLocation)
            imageLocation = imageLocation[:-4]+"_altered.png"
        image.close()
        openai.api_key = self.KEY
        response = openai.Image.create_variation(
            image=open(imageLocation, "rb"),
            n=1,
            size="512x512"
        )

        image_url = response['data'][0]['url']
        img_data = requests.get(image_url).content
        with open(saveLocation+self.conjoiner+'beatImage.png', 'wb') as handler:
            handler.write(img_data)

        imageOnly = imageLocation[imageLocation.rfind("\\")+1:]
        
        return saveLocation+self.conjoiner+'beatImage.png', imageOnly