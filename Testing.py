# File for quick playground or testing purposes

from SamplePackGenerator import *
import os
from pprint import pprint

x = midi_to_content(r"C:\Users\samlb\OneDrive\Projects\SamplePackGenerator\BeatGeneration\Proletarized - 98 BPM - G Minor - 412295795.mid")
pprint(x)
exit()

# x = VideoFileClip(r"C:\Users\samlb\Downloads\Zenawi Hailemariam - ZERO ZERO ⧸ ዜሮ ዜሮ - New Tigrigna Music 2023 [Official Video]-(2160p24).webm").audio
# y = VideoFileClip(r"C:\Users\samlb\Downloads\Master KG - Jerusalema  [Feat. Nomcebo] (Official Music Video)-(1080p25).webm").audio
# z = VideoFileClip(r"C:\Users\samlb\Downloads\BRENDA FASSIE - Vulindlela-(480p25).webm").audio
# a = VideoFileClip(r"C:\Users\samlb\Downloads\Los Del Rio - Macarena (Lyrics)-(1080p60).webm").audio

# from moviepy.editor import *

# finalvideoclip = concatenate_audioclips([x,y,z,a])
# finalvideoclip.write_audiofile('MusicVideos_Video.mp3')
# exit()
# import filecmp
# import difflib

# def simple_file_compare(file1, file2):
#     # Check if files are exactly the same
#     if filecmp.cmp(file1, file2, shallow=False):
#         print("The files are identical.")
#     else:
#         print("The files are different.")
#         detailed_file_compare(file1, file2)

# def detailed_file_compare(file1, file2):
#     # Read the files
#     with open(file1, 'r') as f1:
#         f1_text = f1.readlines()
#     with open(file2, 'r') as f2:
#         f2_text = f2.readlines()
    
#     # Find and print the differences
#     for line in difflib.unified_diff(f1_text, f2_text, fromfile=file1, tofile=file2, lineterm=''):
#         print(line)

# # Example usage
# file1_path = r'C:\Users\samlb\OneDrive\Projects\SamplePackGenerator\pre_plugin_info.txt'
# file2_path = r'C:\Users\samlb\OneDrive\Projects\SamplePackGenerator\post_plugin_info.txt'
# simple_file_compare(file1_path, file2_path)

# exit()

x = open(r'C:\Users\samlb\OneDrive\Projects\SamplePackGenerator\Keywords\Vital - R and B.txt', 'r').read()
x = x.replace('\n', '')
open(r'C:\Users\samlb\OneDrive\Projects\SamplePackGenerator\Keywords\Vital - R and B.txt', 'w').write(x)
exit()

randb = r'C:\Users\samlb\OneDrive\Projects\SamplePackGenerator\States and Presets\Vital\R and B'
for file in os.listdir(randb):
    os.utime(os.path.join(randb, file), (1710706019, 1710706019))

exit(0)


def midi_to_note_name(midi_number):
    # Define the sequence of note names, ignoring octaves
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    # Calculate the note name by using modulo operation to wrap around the note_names list
    note_name = note_names[midi_number % 12]
    
    return note_name

minor_loc = r'C:\Users\samlb\Downloads\MIDI FILES\Minor'
major_loc = r'C:\Users\samlb\Downloads\MIDI FILES\Major'

main_directory = r'C:\Users\samlb\Downloads\Hyperbits-&-Piano-For-Producers-Producer-Creators-Toolkit\Hyperbits & Piano For Producers - Producer Creators Toolkit\PIANO FOR PRODUCERS MELODY PACK'
for dir in os.listdir(main_directory):
    for file in os.listdir(os.path.join(main_directory, dir, 'Other MIDI')):
        content = midi_to_content(os.path.join(main_directory, dir, 'Other MIDI', file))
        
        new_content = []
        for line in content:
            if 'Header' in str(line):
                line[5] = '960'
            line[1] = str(int(line[1])*10)
        
            if ('Note_off_c' not in str(line) and (int(line[1]) % 3840 == 0)):
                new_content.append(line)
        
        even_newer_content = []
        current_time = -1
        temp123 = []
    
        for line in new_content:
            if current_time != line[1]:
                current_time = line[1]
                even_newer_content.extend(temp123)
                temp123 = []
            
            if 'Note_on_c' in str(line):
                even_newer_content.append(line)
                new_line = deepcopy(line)
                new_line[1] = str(int(new_line[1])+3840)
                new_line[2] = 'Note_off_c'
                temp123.append(new_line)
            else:
                even_newer_content.append(line)

        roman_numerals = file[file.find('(')+1:file.find(')')]
        roman_numerals = roman_numerals.replace('-', ' ')
        key, key_type = (dir[dir.find('-')+1:].strip()).split(' ')

        content_to_midi(even_newer_content, os.path.join(r'C:\Users\samlb\Downloads\MIDI FILES', key_type, key+' - '+roman_numerals+".mid"))
        # print(key+' - '+roman_numerals+".mid")
        # exit()
        # pprint(even_newer_content)
        # exit(0)



exit()

notes = []

dic = r'C:\Users\samlb\Downloads\MIDI FILES'
for the_file in os.listdir(dic):
    my_midi_content = midi_to_content(os.path.join(dic, the_file))
    for line in my_midi_content:
        if ('Note_off_c' in str(line)) or ('Note_on_c' in  str(line)):
            notes.append(midi_to_note_name(int(line[4].strip())))
    print(notes)
    # notes = list(set(notes))
    # notes.sort()
    # print(the_file)
    # print(notes)
    # print('-----------------------------------')