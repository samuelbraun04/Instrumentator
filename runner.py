from BeatGenerator import BeatGenerator
from datetime import datetime
from ImageGenerator import ImageGenerator
from os import listdir, getcwd
from random import randint
from random import randint
from random_word import RandomWords
from shutil import move, rmtree
from time import sleep
from Uploader import Uploader
import datetime

#testing variable
TRAP_TESTING = False

def addToTextfile(textfile, addedElement):
    with open(textfile, "a") as f:
        f.write("\n"+addedElement)

def makeTrapBeat():
    
    #set instances
    beatGenerator.shuffleFiles()
    addToTextfile(informationTextFile, "openai key: "+openAIKey)
    print("Instances created.")

    #set values
    bpm = randint(130,170)
    nameGenerator = RandomWords()
    name = nameGenerator.get_random_word().upper()
    beatstarsTitle = name+' beat title additive'
    addToTextfile(informationTextFile, "random name: "+name)
    addToTextfile(informationTextFile, "beatstars title: "+beatstarsTitle)
    print("Values created.")

    #choose random image and create a variation
    availableImagesTrapBeat = listdir(notUsedImagesTrapBeat)
    if (len(availableImagesTrapBeat) == 0):
        for file in listdir(usedImagesTrapBeat):
            move(usedImagesTrapBeat+file, notUsedImagesTrapBeat+file)
        availableImagesTrapBeat = listdir(notUsedImagesTrapBeat)
    imageLocation, chosenImage = imageGenerator.generateImage(notUsedImagesTrapBeat+availableImagesTrapBeat[randint(0,len(availableImagesTrapBeat)-1)], workspaceTrapBeat)
    move(notUsedImagesTrapBeat+chosenImage, usedImagesTrapBeat+chosenImage)
    addToTextfile(informationTextFile, "base image: "+chosenImage)
    print("Image generated.")
    
    #generate the beat
    beatFolder = beatGenerator.run(randint(1,7), bpm)

    return imageLocation, bpm, beatstarsTitle, beatFolder, youtubeTitle, name

#set paths
programLocation = getcwd()
usedImagesTrapBeat = programLocation+'\\Base Images\\Used\\'
notUsedImagesTrapBeat = programLocation+'\\Base Images\\Not Used\\'
workspaceTrapBeat = programLocation+'\\Workspace\\'
trapDescriptionLocation = programLocation + "\\Ingredients\\trapDescription.txt"
informationTextFile = programLocation+'\\information.txt'

openAIKey = ''
imageGenerator = ImageGenerator(openAIKey)
beatGenerator = BeatGenerator(programLocation)
uploader = Uploader(programLocation)

uploader.driver.execute_script('''window.open("","_blank");''')
while(1):
    
    if ((((datetime.now().hour*60 + datetime.now().minute) % 720) == 0) or (TRAP_TESTING == True)):
        
        imageLocation, bpm, beatstarsTitle, beatFolder, youtubeTitle, name = makeTrapBeat(openAIKey)

        #it's time
        if TRAP_TESTING == False:
            sleep(randint(10,360))
        print("Beginning uploading process.")

        #upload to beatstars
        counter = 0
        while(counter != 3):
            try:
                uploader.driver.switch_to.window(uploader.driver.window_handles[0])
                link = uploader.uploadToBeatstars('email', 'password', beatFolder, beatstarsTitle, bpm, imageLocation)
                break
            except Exception as e:
                print(str(e))
                uploader.driver.quit()
                sleep(300)
                imageLocation, bpm, beatstarsTitle, beatFolder, youtubeTitle, name = makeTrapBeat(openAIKey)
                uploader = Uploader(programLocation)
                uploader.driver.execute_script('''window.open("","_blank");''')
                counter += 1
        print("Uploaded to Beatstars.")

        #delete used beat folder
        rmtree(beatFolder)
        print("Beat folder deleted.")
        
        #leave this loop
        if TRAP_TESTING == True:
            break

    else:
        sleep(5)