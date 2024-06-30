from bs4 import BeautifulSoup
from copy import deepcopy
from google.auth.transport.requests import Request
from moviepy.editor import *
from my_pushover import Pushover
from os import listdir, getcwd, path
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
from random import randint
from random_word import RandomWords
from runner import generate_sample_pack
from SamplePackGenerator import midi_to_content, content_to_midi, get_individual_chords, exclude_lowest_note_indexes, upload_to_website, send_notification
from scipy.io import wavfile
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, ElementNotInteractableException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from time import time, sleep
import dawdreamer as daw
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import json
import librosa
import os
import pickle
import requests
import shutil
import traceback
import zipfile

notification = Pushover(open('pushover_keys.txt').readlines()[0].strip())
notification.user(open('pushover_keys.txt').readlines()[1].strip())

def random_sleep():
    sleep(randint(450,750)/100)

def download_images(search_query, output_folder):

    used_images = r'C:\Users\samlb\OneDrive\Projects\SamplePackGenerator\BeatGeneration\used_images.txt'
    used_images_list = open(used_images, 'r').readlines()

    #  Any infinity scroll URL
    url = "https://in.pinterest.com/search/pins/?q=" + search_query 
    sleepTimer = 2    # Waiting 1 second for page to load

    #  Bluetooth bug circumnavigate
    options = webdriver.ChromeOptions() 
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")

    driver = webdriver.Chrome(options=options)  # path=r'to/chromedriver.exe'
    driver.get(url)
    leave = False

    while(1):
        driver.execute_script("window.scrollTo(1,100000)")
        print("scrolling")
        sleep(sleepTimer)

        soup = BeautifulSoup(driver.page_source,'html.parser')

        all_links = []
        for link in soup.find_all('img'):
            if link not in used_images_list:
                image_link = link.get('src')
                all_links.append(image_link)
                with open(used_images, 'a') as file:
                    file.write(image_link+'\n')
                leave = True
                break
        
        parts = image_link.split('/')
        parts[3] = 'originals'
        image_link = '/'.join(parts)

        response = requests.get(image_link)
        final_path = os.path.join(output_folder, 'downloaded_image.jpg')

        if response.status_code == 200:
            with open(final_path, 'wb') as file:
                file.write(response.content)
            print("Image downloaded successfully")
        else:
            print("Failed to retrieve the image")
        
        if leave == True:
            break
    
    driver.quit()
            
    return final_path
        
def adjust_volume(audio_segment, target_db):
    """
    Adjust the volume of an AudioSegment to a target dB.
    """
    print('Original dB:', audio_segment.dBFS, 'Target dB:', target_db)
    print('Change in dB:', target_db - audio_segment.dBFS)
    change_in_db = target_db - audio_segment.dBFS

    x = audio_segment.apply_gain(change_in_db)
    print('New dB:', x.dBFS)

    return x

def remove_trailing_zeroes_integer(number):
    return int(str(number).rstrip('0'))

def get_par_index(desc, par_name):
    for parDict in desc:
        if parDict['name'] == par_name:
            return parDict['index']
    raise ValueError(f"Parameter '{par_name}' not found.")

def copy_and_zip_files(src_dir, dest_dir, zip_name):
    # Copy all files in src_dir to dest_dir
    for filename in os.listdir(src_dir):
        src_file = os.path.join(src_dir, filename)
        if os.path.isfile(src_file):
            print(filename)
            shutil.copy(src_file, dest_dir)
    
    # Create a ZipFile object
    with zipfile.ZipFile(zip_name, 'w') as zipf:
        # Zip the files from directory, which we copied the files to
        for foldername, subfolders, filenames in os.walk(dest_dir):
            for filename in filenames:
                # Create complete filepath of file in directory
                file_path = os.path.join(foldername, filename)
                # Add file to zip
                zipf.write(file_path, os.path.basename(file_path))

def find_lowest_notes(chord_content):
    chords = {}  # Dictionary to hold notes grouped by their start times
    lowest_notes = []  # List to hold the lowest note of each chord

    # Group notes by their start times
    for event in chord_content:
        if 'Note_on_c' in event:
            start_time = int(event[1])
            note = int(event[4])
            velocity = int(event[5])
            if velocity > 0:  # Note on
                if start_time in chords:
                    chords[start_time].append(note)
                else:
                    chords[start_time] = [note]

    # Find the lowest note in each chord
    for start_time in sorted(chords.keys()):
        lowest_notes.append(min(chords[start_time]))

    return lowest_notes

def convert_wav_to_mp3(wav_file, mp3_file):
    audio = AudioSegment.from_wav(wav_file)
    audio.export(mp3_file, format="mp3")

def adjust_notes(data, segment, lowest_notes_per_bar):
    NOTE_ON = 'Note_on_c'
    NOTE_OFF = 'Note_off_c'
    processed_data = []
    current_note_on_c = []
    notes_to_adjust = []
    last_processed_bar = -1

    # First pass: Adjust notes crossing bar boundaries and prepare for melody matching
    for i, event in enumerate(data):
        if event[2] == NOTE_ON:
            note_on_time = int(event[1])
            note_pitch = event[4]
            note_on_bar = note_on_time // segment

            for j in range(i + 1, len(data)):
                off_event = data[j]
                if off_event[2] == NOTE_OFF and off_event[4] == note_pitch:
                    note_off_time = int(off_event[1])
                    note_off_bar = note_off_time // segment
                    break
            else:
                continue  # Skip if no corresponding Note_off is found

            if note_on_bar != note_off_bar:
                # Note crosses a bar boundary, adjust the Note_off to the end of the current bar
                bar_end = (note_on_bar + 1) * segment
                data[j][1] = str(bar_end)  # Adjust Note_off time
                notes_to_adjust.append((bar_end, note_pitch))  # Mark for adjustment in melody matching

    # Second pass: Match 808 pattern to melody, considering adjusted notes
    for index, line in enumerate(data):
        if NOTE_ON in line or NOTE_OFF in line:
            current_time = int(line[1])
            current_bar = current_time // segment

            if last_processed_bar != current_bar - 1:
                counter = current_bar
            else:
                counter = current_bar if NOTE_ON in line else last_processed_bar

            if NOTE_ON in line:
                old_note = line[4]
                if (current_time, old_note) not in notes_to_adjust:  # Check if note was adjusted
                    line[4] = str(lowest_notes_per_bar[counter])
                current_note_on_c.append([old_note, line[4]])
                last_processed_bar = current_bar

            elif NOTE_OFF in line:
                for note in current_note_on_c:
                    if note[0] == line[4]:
                        line[4] = note[1]
                        current_note_on_c.remove(note)
                        break

        processed_data.append(line)

    return processed_data

def adjust_pitch_to_range(data):
    for event in data:
        # Check if event is a Note_on_c or Note_off_c event
        if event[2] in ['Note_on_c', 'Note_off_c']:
            pitch = int(event[4])
            # Adjust the pitch until it's within the desired range
            while pitch < 0:
                pitch += 12
            while pitch > 12:
                pitch -= 12
            # Update the event with the adjusted pitch
            event[4] = str(pitch)
            event[5] = '100'
    return data

def uploadToBeatstars(driver, email, password, final_wav_path, stems_path, beatstars_title, downloaded_image, beatstars_tags, major_style):

    url = 'https://studio.beatstars.com/dashboard'
    cookies_path = r"C:\Users\samlb\OneDrive\Projects\SamplePackGenerator\BeatGeneration\beatstars_cookies.txt"
    driver.get(url)


    try:
        with open(cookies_path, "r") as file:
            cookies = json.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)
        driver.get(url)
        driver.refresh()
        sleep(3)
        driver.execute_script("window.open('');")
        sleep(1)
        driver.switch_to.window(driver.window_handles[0])

    except Exception as e:
        print("Error loading cookies.")
        driver.get(url)
        try:
            #input username
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "oath-email"))).send_keys(email)
            random_sleep()
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'btn-submit-oath'))).click()
            random_sleep()

            #input password
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'userPassword'))).send_keys(password)
            random_sleep()
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'btn-submit-oath'))).click()
            random_sleep()

            print('start')
            sleep(30)
            print('done')

            driver.switch_to.default_content()
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.mat-menu-trigger.wrapper-button button.bs-btn.action-element")))

            driver.get(url)
            with open(cookies_path, "w") as file:
                json.dump(driver.get_cookies(), file)

        except Exception as e:
            print(traceback.format_exc())
            send_notification(notification, "SAMPLE PACK LOGIN FAIL", "Sample Pack Failed to Re-Login In. Trying again in 10 minutes. If this is the first error, wait for next iteration to solve captcha."+str(e))
            driver.quit()
            exit()


    #make a new track
    while(1):
        try:
            createButton = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.mat-menu-trigger.wrapper-button button.bs-btn.action-element")))
            createButton.click()
            random_sleep()
            break
        except StaleElementReferenceException:
            random_sleep()
        except ElementNotInteractableException:
            random_sleep()
    while(1):
        try:
            newTrack = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-cy="undefined-button-create-track"]')))
            newTrack.click()
            random_sleep()
            break
        except StaleElementReferenceException:
            random_sleep()
        except ElementNotInteractableException:
            random_sleep()
    
    #hit upload button
    while(1):
        try:
            uploadButtons = WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.XPATH, "//bs-square-button//button//span[text()='Upload']")))
            uploadButtons[0].click()
            random_sleep()
            break
        except StaleElementReferenceException:
            random_sleep()
        except ElementNotInteractableException:
            random_sleep()

    #upload the file
    while(1):
        try:
            dropBoxWav = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'uppy-DragDrop-input')))
            dropBoxWav.send_keys(final_wav_path)
            random_sleep()
            break
        except StaleElementReferenceException:
            random_sleep()
        except ElementNotInteractableException:
            random_sleep()
        
    #wait until beat upload is complete
    startTime = time()
    while(1):
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//span[text()='Replace']")))
            if ((startTime - time()) > 120.0):
                raise Exception("Upload of beat took to long. Restarting.")
            while(1):
                tabList = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'mat-tab-list')))
                x = WebDriverWait(tabList, 20).until(EC.presence_of_all_elements_located((By.XPATH, '//div[@role="tab"]')))
                if x[1].get_attribute('aria-disabled') == 'false':
                    break
                random_sleep()    
            break
        except TimeoutException:
            pass
        except StaleElementReferenceException:
            random_sleep()
        except ElementNotInteractableException:
            random_sleep()
    
    #hit the upload button
    while(1):
        try:
            uploadButtons = WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.XPATH, "//bs-square-button//button//span[text()='Upload']")))
            uploadButtons[0].click()
            random_sleep()
            break
        except StaleElementReferenceException:
            random_sleep()
        except ElementNotInteractableException:
            random_sleep()
        except ElementClickInterceptedException:
            print('this check went off')
            random_sleep()
    
    #upload the stems
    while(1):
        try:
            dropBoxZip = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'uppy-DragDrop-input')))
            dropBoxZip.send_keys(stems_path)
            random_sleep()
            break
        except StaleElementReferenceException:
            random_sleep()
        except ElementNotInteractableException:
            random_sleep()
        
    #wait until stems upload is complete
    startTime = time()
    while(1):
        try:
            replaceButtons = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.XPATH, "//span[contains(text(), 'Replace')]")))
            if len(replaceButtons) == 3:
                break
            if ((startTime - time()) > 180.0):
                raise Exception("Upload of stems took to long. Restarting.")
            sleep(5)
        except TimeoutException:
            pass
        except StaleElementReferenceException:
            random_sleep()
        except ElementNotInteractableException:
            random_sleep()

    #click next step
    while(1):
        try:
            nextStepButton = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//bs-square-button[@data-qa="button_upload_next"]')))
            while(nextStepButton.is_enabled() == False):
                random_sleep()
            try:
                nextStepButton.click()
            except ElementNotInteractableException:
                driver.execute_script("arguments[0].click();", nextStepButton)
            try:
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Edit Artwork')]")))    
                random_sleep()
                break
            except TimeoutException:
                pass
        except StaleElementReferenceException:
            random_sleep()            

    #upload title
    while(1):
        try:
            titleInput = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'title')))
            titleInput.clear()
            titleInput = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'title')))
            titleInput.send_keys(beatstars_title)
            random_sleep()
            break
        except StaleElementReferenceException:
            random_sleep()
        except ElementNotInteractableException:
            random_sleep()
        
    #upload image
    while(1):
        try:
            uploadImageButton = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Edit Artwork')]")))
            uploadImageButton.click()
            random_sleep()
            break
        except StaleElementReferenceException:
            random_sleep()
        except ElementNotInteractableException:
            random_sleep()
        
    while(1):
        try:
            menuButton = WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.XPATH, '//button[@role="menuitem"]')))[0]
            menuButton.click()
            random_sleep()
            break
        except StaleElementReferenceException:
            random_sleep()
        except ElementNotInteractableException:
            random_sleep()
        
    while(1):
        try:
            dropBoxImage = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'uppy-DragDrop-input')))
            dropBoxImage.send_keys(downloaded_image)
            random_sleep()
            break
        except StaleElementReferenceException:
            random_sleep()
        except ElementNotInteractableException:
            random_sleep()
        
    while(1):
        try:
            saveCropButton = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//bs-square-button[@data-qa="button_save_cropt"]')))
            saveCropButton.click()
            random_sleep()
            break
        except StaleElementReferenceException:
            random_sleep()
        except ElementNotInteractableException:
            random_sleep()

    while(1):
        try:
            button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//button[contains(@class, "bs-btn action-element") and span[text()=" Next Step "]]')))
            button.click()
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//bs-square-button[contains(@class, "vb-btn-additional-primary-text-s")]//button[contains(@class, "bs-btn action-element") and .//span[text()=" Autofill Metadata "]]')))
            random_sleep()
            break
        except StaleElementReferenceException:
            random_sleep()
        except ElementNotInteractableException:
            random_sleep()
        except TimeoutException:
            random_sleep()

    while(1):
        try:
            autoFillButton = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//bs-square-button[contains(@class, "vb-btn-additional-primary-text-s")]//button[contains(@class, "bs-btn action-element") and .//span[text()=" Autofill Metadata "]]')))
            autoFillButton.click()
            random_sleep()
            break
        except StaleElementReferenceException:
            random_sleep() 
        except ElementNotInteractableException:
            random_sleep()
    
    while(1):
        try:
            enableButton = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//bs-square-button[contains(@class, "confirm-btn vb-system vb-btn-primary-text-m")]//button[@data-cy="confirm-button" and contains(., "Enable Autofill")]')))
            enableButton.click()
            random_sleep()
            break
        except StaleElementReferenceException:
            random_sleep() 
        except ElementNotInteractableException:
            random_sleep()

    while(1):
        try:
            tags = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//div[@class="mat-chip-list-wrapper"]/input[contains(@class, "mat-chip-input mat-input-element")]')))
            beatstars_tags = major_style+', '+beatstars_tags[beatstars_tags.find(',')+2:]+', '
            tags.send_keys(beatstars_tags)
            random_sleep()
            break
        except StaleElementReferenceException:
            random_sleep() 
        except ElementNotInteractableException:
            random_sleep()

    #publish the beat
    while(1):
        try:
            publishButton = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//bs-square-button[@data-qa="button_upload_publish"]')))
            while(publishButton.is_enabled() == False):
                random_sleep()
            publishButton.click()
            try:
                button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//button[@data-cy="confirm-button" and contains(., "Confirm and publish")]')))
                button.click()
                print("Button clicked")
            except TimeoutException as e:
                print("Button did not appear within 10 seconds")
            random_sleep()
            break
        except StaleElementReferenceException:
            random_sleep()
        except ElementNotInteractableException:
            random_sleep()
            
    #get the link
    while(1):
        try:
            input_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input.input-suffix[type="text"]')))
            link = input_element.get_attribute('value')
            random_sleep()
            break
        except StaleElementReferenceException:
            random_sleep()
        except ElementNotInteractableException:
            random_sleep()

    print(link)
    return link

def delete_everything_in_directory(directory):
    # Check if the directory exists
    if not os.path.exists(directory):
        print("Directory does not exist.")
        return

    # Remove all files and subdirectories
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path) or os.path.islink(item_path):
            os.unlink(item_path)  # Remove files and links
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)  # Remove directories recursively

def load_audio_file(file_path, duration=None):
    sig, rate = librosa.load(file_path, duration=duration, mono=False, sr=SAMPLE_RATE)
    assert(rate == SAMPLE_RATE)
    return sig

def authenticate_channel(client_secrets_file, scopes, channel_name, full_path):
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    credentials = flow.run_local_server(port=0)
    save_credentials(channel_name, credentials, full_path)
    return googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

def load_or_authenticate_channel(channel_name, client_secrets_file, full_path):
    credentials = load_credentials(channel_name, full_path)

    if credentials and credentials.valid:
        return googleapiclient.discovery.build("youtube", "v3", credentials=credentials)
    else:
        return authenticate_channel(client_secrets_file, ["https://www.googleapis.com/auth/youtube", 'https://www.googleapis.com/auth/youtube.force-ssl'], channel_name, full_path)

def save_credentials(channel_name, credentials, full_path):
    credentials_path = full_path+'\\credentials'+channel_name+'.pkl'
    with open(credentials_path, 'wb') as credentials_file:
        pickle.dump(credentials, credentials_file)

def load_credentials(channel_name, full_path):
    credentials_path = os.path.join(full_path, 'credentials' + channel_name + '.pkl')
    if os.path.exists(credentials_path):
        with open(credentials_path, 'rb') as credentials_file:
            credentials = pickle.load(credentials_file)
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                save_credentials(channel_name, credentials, full_path)  # Save the refreshed credentials
                return credentials
            elif credentials and credentials.valid:
                return credentials
    return None

# set paths
main_directory = path.join(getcwd(), "BeatGeneration")
building_blocks_path = path.join(main_directory, "Blocks")
ingredients_samples_path = path.join(main_directory, "Ingredients", "Samples")
ingredients_midi_path = path.join(main_directory, "Ingredients", "MIDI")
modified_808_midi_path = path.join(main_directory, "Playground", "modified_808.mid")
temp_final_wav_path = path.join(main_directory, "temp_final_beat.wav")
final_wav_path = path.join(main_directory, str(time())[-4:]+"final_beat.wav")
final_mp3_path = path.join(main_directory, "final_beat.mp3")
stems_path = path.join(main_directory, "Stems")
stems_file_path = path.join(main_directory, "stems.zip")
final_video_path = path.join(main_directory, "final_video.mp4")
tag_path = path.join(main_directory, "long_TAG.mp3")
description_path = path.join(main_directory, "description.txt")

SAMPLE_RATE = 44100

# delete_everything_in_directory(building_blocks_path)


# ### for testing
# driver = webdriver.Chrome()
# beatstars_title = 'Testing the title'
# melody_bpm = str(100)
# downloaded_image = r'C:\Users\samlb\OneDrive\Projects\SamplePackGenerator\BeatGeneration\Beat Image\downloaded_image.jpg'
# major_style = 'Acoustic Guitar'
# beatstars_tags = 'Guitar, Sad, Emotional'
# ### for testing

sample_dir_path, midi_dir_path, chord_progression_path, melody_bpm, beat_key, major_style, beatstars_tags = generate_sample_pack("ample_guitar", "Sad", True)

while(1):
    random_word = RandomWords().get_random_word()
    if len(random_word) < 10:
        break
random_word = random_word.title()


youtube_payhip_title = '[FREE FOR PROFIT] '+major_style+' Type Beat - '+beatstars_tags+' "'+random_word+'" Royalty Free'
beatstars_title = major_style+' Type Beat - '+beatstars_tags+' "'+random_word+'"'

drum_types = ["HiHat", "EightOhEight", "Kick", "Snare", "Perc1", "Perc2", "Clap"]
# 0: HiHat
# 1: Kick
# 2: EightOhEight
# 3: Snare
# 4: Perc1
# 5: Perc2
# 6: Clap

selected_midi_files = []
selected_sample_files = []

for drum_type in drum_types:
    samples_path = path.join(ingredients_samples_path, drum_type)
    midi_path = path.join(ingredients_midi_path, drum_type)
    
    midi_files = listdir(midi_path)
    selected_midi_file = path.join(midi_path, midi_files[randint(0, len(midi_files) - 1)])
    selected_midi_files.append(selected_midi_file)
    
    sample_files = listdir(samples_path)
    selected_sample_file = path.join(samples_path, sample_files[randint(0, len(sample_files) - 1)])
    selected_sample_files.append(selected_sample_file)

engine = daw.RenderEngine(SAMPLE_RATE, 128)
engine.set_bpm(melody_bpm)

instruments = []
ingredients = {}

for sample_index, drum in enumerate(selected_sample_files):

    if drum_types[sample_index] == 'EightOhEight':
       
        sample_midi_content = midi_to_content(midi_dir_path)
        chord_content = midi_to_content(chord_progression_path)
        grouped_chords, start_section, end_section = get_individual_chords(chord_content, False)
        grouped_chords, lowest_notes_indexes = exclude_lowest_note_indexes(grouped_chords)
        sample_midi_content = deepcopy(sample_midi_content)
        new_808_content = midi_to_content(selected_midi_files[sample_index])
        lowest_notes_per_bar = find_lowest_notes(chord_content)
        lowest_notes_per_bar.extend(lowest_notes_per_bar)
        segment = int(int(new_808_content[-3][1])/len(lowest_notes_per_bar))
        new_808_content = adjust_notes(new_808_content, segment, lowest_notes_per_bar)

        counter = 0
        current_note_on_c = []
        for index, line in enumerate(new_808_content):
            if 'Note_on_c' in str(line):
                old_note = str(new_808_content[index][4])
                current_bar = (int(line[1]) // segment)
                if current_bar == counter:
                    new_808_content[index][4] = str(lowest_notes_per_bar[counter])
                else:
                    counter+=1
                    new_808_content[index][4] = str(lowest_notes_per_bar[counter])
                current_note_on_c.append([old_note, str(lowest_notes_per_bar[counter])])
            elif 'Note_off_c' in str(line):
                for note in current_note_on_c:
                    if note[0] == line[4]:
                        new_808_content[index][4] = note[1]
                        current_note_on_c.remove(note)
                        break
        
        new_808_content = adjust_pitch_to_range(new_808_content)
        content_to_midi(new_808_content, modified_808_midi_path)
        selected_midi_files[sample_index] = modified_808_midi_path
    
    if drum_types[sample_index] == "Kick":

        new_kick_content = midi_to_content(selected_midi_files[1]) #because eightoheight is index 1

        for line in new_kick_content:
            if ('Note_on_c' in str(line)) or ('Note_off_c' in str(line)):
                line[4] = '0'
        
        content_to_midi(new_kick_content, selected_midi_files[sample_index])

    instrument = engine.make_sampler_processor(drum_types[sample_index], load_audio_file(drum))

    desc = instrument.get_parameters_description()
    instrument.set_parameter(get_par_index(desc, 'Amp Env Attack'), 1.)  # set attack in milliseconds
    instrument.set_parameter(get_par_index(desc, 'Amp Env Decay'), 0.)  # set decay in milliseconds
    instrument.set_parameter(get_par_index(desc, 'Amp Env Sustain'), 1.)  # set sustain
    instrument.set_parameter(get_par_index(desc, 'Amp Env Release'), 2.)  # set release in milliseconds
    instrument.set_parameter(get_par_index(desc, 'Amp Active'), 1.)

    instrument.load_midi(selected_midi_files[sample_index], beats=True)

    graph = [
       (instrument, [])
    ]

    engine.load_graph(graph)
    engine.render(32., beats=True)
    audio = engine.get_audio()

    wavfile.write(path.join(building_blocks_path, drum_types[sample_index]+'.wav'), SAMPLE_RATE, audio.transpose())
    ingredients[drum_types[sample_index]] = AudioSegment.from_wav(path.join(building_blocks_path, drum_types[sample_index]+'.wav'))

ingredients["Melody"] = AudioSegment.from_wav(sample_dir_path)
nonsilent_chunks = detect_nonsilent(ingredients["Melody"], min_silence_len=1, silence_thresh=-48)

# Assuming there's at least one non-silent chunk, remove silence from the beginning
if nonsilent_chunks:
    start_trim = nonsilent_chunks[0][0]
    ingredients["Melody"] = ingredients["Melody"][start_trim:] + AudioSegment.silent(duration=start_trim)

ingredients_paths = {
    "HiHat": path.join(building_blocks_path, "HiHat.wav"),
    "Snare": path.join(building_blocks_path, "Snare.wav"),
    "EightOhEight": path.join(building_blocks_path, "EightOhEight.wav"),
    "Kick": path.join(building_blocks_path, "Kick.wav"),
    "Perc1": path.join(building_blocks_path, "Perc1.wav"),
    "Perc2": path.join(building_blocks_path, "Perc2.wav"),
    "Clap": path.join(building_blocks_path, "Clap.wav"),
}

# Set target dB levels
target_db_levels = {
    "HiHat": -12,
    "Snare": -9,
    "EightOhEight": -3,
    "Kick": -3,
    "Perc1": -14,
    "Perc2": -14,
    "Clap": -6
}

# Adjust volumes
for drum, file_path in ingredients_paths.items():
    # Load the sample
    audio_segment = AudioSegment.from_wav(file_path)
    # Adjust its volume
    adjusted_segment = adjust_volume(audio_segment, target_db_levels[drum])
    # Export the adjusted sample to the same path, effectively overwriting the original
    adjusted_segment.export(file_path, format='wav')

template = randint(0,4)
if template == 0:
    bar1 = ingredients["Melody"]
    bar2 = ingredients["Melody"].overlay(ingredients["EightOhEight"]).overlay(ingredients["HiHat"])
    bar3 = ingredients["Melody"].overlay(ingredients["EightOhEight"]).overlay(ingredients["HiHat"]).overlay(ingredients["Clap"]).overlay(ingredients["Kick"])
    bar4 = ingredients["Melody"].overlay(ingredients["EightOhEight"]).overlay(ingredients["Snare"]).overlay(ingredients["Clap"]).overlay(ingredients["Kick"])
    bar5 = ingredients["Melody"]
    bar6 = ingredients["Melody"].overlay(ingredients["HiHat"]).overlay(ingredients["Clap"])
    bar7 = ingredients["Melody"].overlay(ingredients["Kick"]).overlay(ingredients["Clap"]).overlay(ingredients["EightOhEight"])
    bar8 = ingredients["Melody"].overlay(ingredients["Kick"]).overlay(ingredients["Clap"]).overlay(ingredients["EightOhEight"]).overlay(ingredients["Snare"])
    bar9 = ingredients["Melody"].overlay(ingredients["Kick"]).overlay(ingredients["Clap"]).overlay(ingredients["EightOhEight"]).overlay(ingredients["Snare"]).overlay(ingredients["HiHat"])
if template == 1:
    bar1 = ingredients["Melody"]
    bar2 = ingredients["Melody"].overlay(ingredients["Clap"]).overlay(ingredients["EightOhEight"])
    bar3 = ingredients["Melody"].overlay(ingredients["Perc1"]).overlay(ingredients["Clap"]).overlay(ingredients["EightOhEight"]).overlay(ingredients["Kick"])
    bar4 = ingredients["Melody"].overlay(ingredients["Kick"]).overlay(ingredients["Snare"]).overlay(ingredients["EightOhEight"])
    bar5 = ingredients["Melody"].overlay(ingredients["Kick"]).overlay(ingredients["Snare"]).overlay(ingredients["HiHat"]).overlay(ingredients["EightOhEight"]).overlay(ingredients["Clap"])
    bar6 = ingredients["Melody"]
    bar7 = ingredients["Melody"].overlay(ingredients["Clap"]).overlay(ingredients["EightOhEight"])
    bar8 = ingredients["Melody"].overlay(ingredients["Clap"]).overlay(ingredients["Perc2"]).overlay(ingredients["EightOhEight"])
    bar9 = ingredients["Melody"].overlay(ingredients["Kick"]).overlay(ingredients["Clap"]).overlay(ingredients["Snare"]).overlay(ingredients["HiHat"]).overlay(ingredients["EightOhEight"])
if template == 2:
    bar1 = ingredients["Melody"]
    bar2 = ingredients["Melody"].overlay(ingredients["Snare"]).overlay(ingredients["EightOhEight"])
    bar3 = ingredients["Melody"].overlay(ingredients["Snare"]).overlay(ingredients["Clap"]).overlay(ingredients["EightOhEight"])
    bar4 = ingredients["Melody"].overlay(ingredients["Kick"]).overlay(ingredients["Snare"]).overlay(ingredients["Clap"]).overlay(ingredients["EightOhEight"])
    bar5 = ingredients["Melody"].overlay(ingredients["Kick"]).overlay(ingredients["Snare"]).overlay(ingredients["Clap"]).overlay(ingredients["EightOhEight"]).overlay(ingredients["HiHat"])
    bar6 = ingredients["Melody"]
    bar7 = ingredients["Melody"].overlay(ingredients["Clap"]).overlay(ingredients["HiHat"])
    bar8 = ingredients["Melody"].overlay(ingredients["Kick"]).overlay(ingredients["Clap"]).overlay(ingredients["EightOhEight"])
    bar9 = ingredients["Melody"].overlay(ingredients["Kick"]).overlay(ingredients["Clap"]).overlay(ingredients["HiHat"]).overlay(ingredients["EightOhEight"]).overlay(ingredients["HiHat"])
if template == 3:
    bar1 = ingredients["Melody"]
    bar2 = ingredients["Melody"].overlay(ingredients["HiHat"]).overlay(ingredients["Clap"])
    bar3 = ingredients["Melody"].overlay(ingredients["HiHat"]).overlay(ingredients["Clap"]).overlay(ingredients["EightOhEight"])
    bar4 = ingredients["Melody"].overlay(ingredients["HiHat"]).overlay(ingredients["Clap"]).overlay(ingredients["EightOhEight"]).overlay(ingredients["Snare"])
    bar5 = ingredients["Melody"].overlay(ingredients["HiHat"]).overlay(ingredients["Clap"]).overlay(ingredients["EightOhEight"]).overlay(ingredients["Snare"]).overlay(ingredients["Kick"])
    bar6 = ingredients["Melody"].overlay(ingredients["EightOhEight"])
    bar7 = ingredients["Melody"].overlay(ingredients["EightOhEight"]).overlay(ingredients["Clap"]).overlay(ingredients["Perc2"])
    bar8 = ingredients["Melody"].overlay(ingredients["EightOhEight"]).overlay(ingredients["Clap"]).overlay(ingredients["Perc2"]).overlay(ingredients["Snare"])
    bar9 = ingredients["Melody"].overlay(ingredients["EightOhEight"]).overlay(ingredients["Clap"]).overlay(ingredients["Perc2"]).overlay(ingredients["Snare"]).overlay(ingredients["Kick"])
if template == 4:
    bar1 = ingredients["Melody"]
    bar2 = ingredients["Melody"].overlay(ingredients["Clap"]).overlay(ingredients["HiHat"])
    bar3 = ingredients["Melody"].overlay(ingredients["Clap"]).overlay(ingredients["EightOhEight"])
    bar4 = ingredients["Melody"].overlay(ingredients["EightOhEight"]).overlay(ingredients["HiHat"]).overlay(ingredients["Kick"])
    bar5 = ingredients["Melody"].overlay(ingredients["Clap"]).overlay(ingredients["EightOhEight"]).overlay(ingredients["HiHat"]).overlay(ingredients["Kick"]).overlay(ingredients["Snare"]).overlay(ingredients["Perc1"])
    bar6 = ingredients["Melody"]
    bar7 = ingredients["Melody"].overlay(ingredients["HiHat"])
    bar8 = ingredients["Melody"].overlay(ingredients["Clap"]).overlay(ingredients["EightOhEight"]).overlay(ingredients["HiHat"]).overlay(ingredients["Snare"])
    bar9 = ingredients["Melody"].overlay(ingredients["Clap"]).overlay(ingredients["EightOhEight"]).overlay(ingredients["HiHat"]).overlay(ingredients["Kick"]).overlay(ingredients["Snare"]).overlay(ingredients["Perc2"])

# overlay riser to bar end of bar1 and bar4 and bar
final_beat = bar1+bar2+bar3+bar4+bar5+bar6+bar7+bar8+bar9
final_beat.export(temp_final_wav_path, format='wav')

engine = daw.RenderEngine(SAMPLE_RATE, 128)
engine.set_bpm(melody_bpm)

beat_audio = engine.make_playback_processor("beat_playback", load_audio_file(temp_final_wav_path))
soft_clipper = engine.make_plugin_processor("soft_clip", r"C:\Users\samlb\OneDrive\Projects\SamplePackGenerator\Plugins\FreeClip.dll")

# desc = soft_clipper.get_parameters_description()
# pprint(desc)
# soft_clipper.open_editor()
# desc = soft_clipper.get_parameters_description()
# pprint(desc)

soft_clipper.set_parameter(3, 1.)  # set attack in milliseconds
soft_clipper.set_parameter(0, 0.193774)  # set decay in milliseconds
# soft_clipper.open_editor()
# adjusted_segment = adjust_volume(audio_segment, target_db_levels[drum])

graph = [
    (soft_clipper, []),
    (soft_clipper, ["beat_playback"])
]

engine.load_graph(graph)
engine.render(288., beats=True)
audio = engine.get_audio()

wavfile.write(final_wav_path, SAMPLE_RATE, audio.transpose())

exit() #############################################

#get image for beat
downloaded_image = download_images("lightskin girl", path.join(main_directory, "Beat Image"))

# turn the samples into a zipped folder labeled stems
copy_and_zip_files(building_blocks_path, stems_path, stems_file_path)

# turn it into a mp3 and layer the tag on top of it
convert_wav_to_mp3(final_wav_path, final_mp3_path)
mp3_segment = AudioSegment.from_mp3(final_mp3_path)
mp3_segment = mp3_segment.overlay(AudioSegment.from_mp3(tag_path), position=15, loop=True)
mp3_segment.export(final_mp3_path, format='mp3')

# upload the mp3 to payhip
free_beat_link = upload_to_website(notification, "casio.cdp.240r@gmail.com", "BDDu3j0dM1mr6!MMa92O", final_mp3_path, youtube_payhip_title, '0.00', downloaded_image, "Free MP3 version of the beat. Listen to the beat on my youtube channel.")

# upload the wav and stems to beatstars
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)
while(counter != 3):
    try:
        link = uploadToBeatstars(driver, 'ohsamuelofficial@gmail.com', '4mSChK?Ho?ko3g83', final_wav_path, stems_file_path, beatstars_title, downloaded_image, beatstars_tags, major_style)
        break
    except Exception as e:
        print(str(e))
        driver.quit()
        sleep(300)
        counter += 1
print("Uploaded to Beatstars.")

# make a video and upload it to youtube
image_clip = ImageClip(downloaded_image)
image_clip = image_clip.resize(height=1080)
audio_clip = AudioFileClip(final_mp3_path)
canvas = ColorClip((1920, 1080), 'black').set_duration(audio_clip.duration)
canvas = canvas.resize((1920, 1080))
img_width, img_height = image_clip.size
x_center = (1920 - img_width) // 2
y_center = (1080 - img_height) // 2
composite = canvas.set_position((0,0))
image_clip = image_clip.set_position((x_center, y_center)).set_duration(audio_clip.duration)
final_video = CompositeVideoClip([composite, image_clip]).set_audio(audio_clip)
final_video.set_duration(audio_clip.duration)
final_video.write_videofile(final_video_path, fps=24)

# upload a youtube video for the beat and link prodohsamuel.store and the beatstars links
description = open(description_path, 'r').read()
description = description.replace('PAID_LINK', link)
description = description.replace('BEAT_BPM', str(melody_bpm))
description = description.replace('BEAT_KEY', beat_key)

youtube = load_or_authenticate_channel('prodohsamuel', r"C:\Users\samlb\OneDrive\Projects\SamplePackGenerator\client_secret_643590692955-v30jg61vqaue6odc2km5vipni0aopnej.apps.googleusercontent.com.json", getcwd())

body={
    "snippet": {
        "categoryId": "10",
        "description": description,
        "title": youtube_payhip_title.upper()
    },
    "status": {
        "privacyStatus": "public",
        "selfDeclaredMadeForKids": False,
    }
}

request = youtube.videos().insert(
    part=",".join(body.keys()),
    body=body,
    media_body=googleapiclient.http.MediaFileUpload(final_video_path, chunksize=-1, resumable=True)
)