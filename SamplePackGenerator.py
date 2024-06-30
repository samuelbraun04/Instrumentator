from copy import deepcopy
from google.auth.transport.requests import Request
from moviepy.editor import *
from music21 import note
from os import path, remove
from pprint import pprint
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep
import glob
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import json
import librosa
import os
import pickle
import py_midicsv as pm
import pyperclip
import random
import undetected_chromedriver as uc

def midi_to_content(midi_file_path):
    midi_content = pm.midi_to_csv(midi_file_path)

    structured_content = []
    for line in midi_content:
        stripped_line = line.strip()
        split_line = stripped_line.split(',')
        processed_line = [element.strip() for element in split_line]
        structured_content.append(processed_line)
        
    return structured_content

def content_to_midi(midi_content, filename):

    midi_content = deepcopy(midi_content)

    for line in range(len(midi_content)):
        midi_content[line] = ', '.join(midi_content[line])+'\n'

    midi_object = pm.csv_to_midi(midi_content)
    with open(filename, "wb") as output_file:
        midi_writer = pm.FileWriter(output_file)
        midi_writer.write(midi_object)
    
    return filename

def clean_directory(directory):
    files = glob.glob(path.join(directory, '*'))
    for file in files:
        if path.isfile(file):
            remove(file)

def save_state(plugin, name):
    pyperclip.copy(name.split('\\')[-1])
    plugin.open_editor()
    plugin.save_state(name)

def get_all_note_on_c(data):
    chords = {}
    for index, item in enumerate(data):
        if 'Note_on_c' in item:
            time_stamp = item[1]
            if time_stamp not in chords:
                chords[time_stamp] = [[index, item]]
            else:
                chords[time_stamp].append([index, item])

    chord_groups = list(chords.values())

    return chord_groups

def extract_all_notes(chord_progression_content):
    notes = []
    for note1 in chord_progression_content:
        if (note1[2].strip() == 'Note_on_c'):
            notes.append(int(note1[4]))
    notes = list(set(notes))
    notes = sorted(notes)

    return notes

def midi_numbers_to_unique_notes(midi_numbers):
    unique_notes = set()
    
    # Convert MIDI numbers to unique note names without octaves
    for midi_number in midi_numbers:
        n = note.Note()
        n.pitch.midi = midi_number
        note_name = n.pitch.name  # This gets the note name without octave
        unique_notes.add(note_name)
    
    # Convert unique note names back to MIDI numbers
    # Note: The octave is arbitrarily chosen here. C4 is chosen as the default octave.
    unique_midi_numbers = []
    for note_name in unique_notes:
        # Assuming C4 as the base octave
        n = note.Note(note_name + '5')
        unique_midi_numbers.append(n.pitch.midi)

    return sorted(unique_midi_numbers)

def randomize_subsection_by_indexes(content, indexes):

    content = deepcopy(content)

    changes = [0, 0, 0, 0, 0, 0, 12, 12, 12]
    other_changes = [-12, 0, 0, 0, 0, 0, 0, 12, 12, 12]
    note_on_c_list = {}
    note_off_c_list = {}

    for line in indexes:
        if 'Note_on_c' in str(line):
            note_on_c_list[line[1]] = line[0][4]
        else:
            note_off_c_list[line[0][4]] = line[1]

    for index in note_on_c_list.keys():
        if int(content[index][4]) <= 60:
            new_note = str(int(content[index][4]) + random.choice(other_changes))
        else:    
            new_note = str(int(content[index][4]) + random.choice(changes))
        
        content[index][4] = new_note
        content[note_off_c_list[note_on_c_list[index]]][4] = new_note
        
    return content

def generate_melody_bar(chord_notes, diatonic_notes, is_first_bar, there_is_zero, overall_timer, hyperness=1):

    # Assuming a bar length of 3840 ticks
    if there_is_zero:
        bar_length = 3840
        fragment = 480
    else:
        bar_length = 384
        fragment = 48
    
    if is_first_bar:
        note_starts = [bar_length // 4, bar_length // 2, bar_length * 3 // 4]
    else:
        note_starts = [0, bar_length // 4, bar_length // 2, bar_length * 3 // 4]

    # Choose the first note from the chord and play it at a higher octave
    first_note = random.choice(chord_notes)
    first_note_start_time = random.choice(note_starts)
    time_left = 0
    new_length = (bar_length-first_note_start_time)//fragment
    if new_length < hyperness:
        new_length = hyperness
    
    starting_velocity = str(random.randint(70, 90))
    melody = [['2', str(first_note_start_time + overall_timer), 'Note_on_c', '0', str(first_note), starting_velocity],
              ['2', str(first_note_start_time + overall_timer + fragment * random.randint(hyperness, new_length)), 'Note_off_c', '0', str(first_note), starting_velocity]]
    time_left = int(melody[-1][1])

    #should spend little time on diatonic notes and more time on chord notes
    is_diatonic = False
    while(time_left < (bar_length + overall_timer)):
        old_end_time = melody[-1][1]
        old_note = melody[-1][4]
        random_note = old_note

        letter_old_note = midi_numbers_to_notes([int(old_note)])[0]
        if letter_old_note in midi_numbers_to_notes(chord_notes):
            old_note_number = note_to_midi(letter_old_note)
            random_note = random.choice(change_probability_of_next_note(old_note_number, diatonic_notes))
            all_available_notes = expand_number_range(random_note)
            random_note = find_closest_number(old_note_number, all_available_notes)
            is_diatonic = True
        else:
            random_note = random.choice(chord_notes)
            all_available_notes = expand_number_range(random_note)
            random_note = find_closest_number(note_to_midi(letter_old_note), all_available_notes)
            is_diatonic = False
        
        random_velocity = str(random.randint(50, 90))
        melody.append(['2', old_end_time, 'Note_on_c', '0', str(random_note), random_velocity])
        if is_diatonic:
            length = ((overall_timer+bar_length)-int(old_end_time))//int(fragment*2)
        else:
            length = ((overall_timer+bar_length)-int(old_end_time))//fragment
        if length < hyperness:
            length = hyperness
        
        note_end = int(old_end_time) + fragment * random.randint(hyperness, length)
        if note_end > bar_length + overall_timer:
            note_end = bar_length + overall_timer
        melody.append(['2', str(note_end), 'Note_off_c', '0', str(random_note), random_velocity])
        time_left = int(melody[-1][1])

    overall_timer+=bar_length

    return melody, overall_timer

def adjust_note_lengths(input_data):
    adjusted_data = []  # New list to hold the adjusted MIDI events
    ongoing_notes = {}  # Dictionary to track ongoing notes
    content_to_midi(input_data, 'test1.mid')
    pprint(input_data)

    for item in input_data:
        event_type = item[2]
        time_stamp = int(item[1])

        # Handling 'Note_on_c' events
        if event_type == 'Note_on_c':
            note_key = item[4]  # Use channel and note as a unique identifier
            ongoing_notes[note_key] = time_stamp  # Store the start time
            adjusted_data.append(item)  # Add the 'Note_on_c' event to the adjusted data

        # Handling 'Note_off_c' events
        elif event_type == 'Note_off_c':
            note_key = item[4]
            
            if note_key in ongoing_notes.keys():
                start_time = ongoing_notes[note_key]
                
                if start_time % 3840 == 0:  # If the note started on a multiple of 3840
                    # Don't add the 'Note_off_c' event yet
                    continue
                else:
                    # If the note did not start on a multiple of 3840, add it normally
                    print(item)
                    adjusted_data.append(item)
                    del ongoing_notes[note_key]  # Remove from ongoing notes

        else:
            # For all other events, just add them to the adjusted data
            adjusted_data.append(item)

        # Check and add 'Note_off_c' events for notes that should end at this timestamp
        if time_stamp % 3840 == 0:
            
            to_remove = []
            for note_key in ongoing_notes.keys():
                start_time = ongoing_notes[note_key]
                if start_time % 3840 == 0 and start_time != time_stamp:
                    # Add a 'Note_off_c' event at this timestamp for the note
                    adjusted_data.append(['2', str(time_stamp), 'Note_off_c', note_key[0], note_key[1], '0'])
                    to_remove.append(note_key)
            # Remove notes that have been ended
            for note_key in to_remove:
                del ongoing_notes[note_key]
    
    pprint(adjusted_data)
    content_to_midi(adjusted_data, 'test2.mid')
    exit()

    # # Add any remaining 'Note_off_c' events for notes still ongoing at the end
    # for note_key, start_time in ongoing_notes.items():
    #     adjusted_data.append(['2', '30720', 'Note_off_c', note_key[0], note_key[1], '0'])  # Assuming 30720 as a closing timestamp

    return adjusted_data

def fix_midi_notes(midi_list):
    def next_multiple_of_3840(n):
        # This only affects notes starting exactly on a multiple of 3840
        return ((n + 3839) // 3840) * 3840 if n % 3840 == 0 else n

    # Initialize containers for processed events and active notes
    processed_events = []
    active_notes = {}  # Format: {(track, channel, note): (note_on_event, scheduled_note_off_time)}

    # Process notes, ensuring correct note_off scheduling
    for event in midi_list:
        if len(event) > 2:
            event_type = event[2]
            if event_type in ['Note_on_c', 'Note_off_c'] and len(event) >= 6:
                track, timestamp, _, channel, note, velocity = event[:6]
                timestamp = int(timestamp)
                if event_type == 'Note_on_c' and int(velocity) > 0:
                    end_time = next_multiple_of_3840(timestamp)
                    if end_time != timestamp:  # Only modify if starting on a multiple of 3840
                        active_notes[(track, channel, note)] = (event, end_time)
                    else:
                        processed_events.append(event)
                elif (track, channel, note) in active_notes:
                    _, scheduled_end = active_notes[(track, channel, note)]
                    if timestamp < scheduled_end:
                        continue  # Skip this note_off, it will be added later
                    else:
                        note_on_event, _ = active_notes.pop((track, channel, note))
                        processed_events.append(note_on_event)
                        processed_events.append(event)
                else:
                    processed_events.append(event)
            else:
                # For non-note events, add them directly
                processed_events.append(event)

    # Add scheduled note_off events for notes still on
    for (track, channel, note), (note_on_event, end_time) in active_notes.items():
        processed_events.append(note_on_event)
        processed_events.append([track, str(end_time), 'Note_off_c', channel, note, '0'])

    # Sort by timestamp, then by ensuring note_off comes before note_on when timestamps match
    processed_events.sort(key=lambda x: (int(x[1]), x[2] != 'Note_off_c'))

    # Remove existing 'End_of_file' and ensure it's correctly placed at the end
    processed_events = [e for e in processed_events if e[2] != 'End_of_file']

    for dead_index2, line2 in enumerate(processed_events):
        if 'End_track' in str(line2) and line2[1] != '0':
            processed_events.remove(line2)
    processed_events.append(['0', str(processed_events[-1][1]), 'End_track'])
    processed_events.append(['0', '0', 'End_of_file'])

    return processed_events

def load_audio_file(file_path: str, duration=None, offset=0):

	file_path = str(file_path)

	if True:

		sig, rate = librosa.load(file_path, duration=duration, mono=False, sr=44100, offset=offset)
		assert(rate == 44100)
	
	else:
		# todo: soundfile doesn't allow you to specify the duration or sample rate, unless the file is RAW
		sig, rate = soundfile.read(file_path, always_2d=True)
		sig = sig.T

		if duration is not None:
			sig = sig[:,:int(duration*rate)]

	return sig

def remove_duplicate_notes(content):

    events = {}
    new_content = []
    for index, line in enumerate(content):
        if 'Note_on_c' in line[2]:
            the_note = line[4]
            if the_note in events.keys():
                content = replace_note(content, line, index, 40, 84, True)
                return content, False
            else:
                events[the_note] = True
                new_content.append(line)
        elif 'Note_off_c' in line[2]:
            the_note = line[4]
            if the_note in events:
                del events[the_note]
                new_content.append(line)
        else:
            new_content.append(line)

    return new_content, True

def change_probability_of_next_note(x, numbers):
    # Sort the list to make it easier to find closest numbers
    sorted_numbers = sorted(set(numbers))  # Remove duplicates to handle multiplication correctly

    # Separate numbers into those above and below x
    above_x = [num for num in sorted_numbers if num > x]
    below_x = [num for num in sorted_numbers if num < x]
    
    # Identify the closest and second closest numbers above x
    closest_above = above_x[0] if above_x else None
    second_closest_above = above_x[1] if len(above_x) > 1 else None
    
    # Identify the closest and second closest numbers below x
    closest_below = below_x[-1] if below_x else None
    second_closest_below = below_x[-2] if len(below_x) > 1 else None

    # Modify the original list based on the rules
    modified_list = []
    for num in numbers:
        if num == closest_above or num == closest_below:
            modified_list.extend([num] * 3)  # Triple the number of elements
        elif num == second_closest_above or num == second_closest_below:
            modified_list.extend([num] * 2)  # Double the number of elements
        else:
            modified_list.append(num)  # Keep other elements unchanged

    return modified_list

def find_closest_number(target, numbers):
    # Initialize with the first number in the list as the closest number
    closest = numbers[0]
    
    # Iterate through the list and update the closest number if a closer one is found
    for number in numbers:
        if abs(number - target) < abs(closest - target):
            closest = number
    
    return closest

def expand_number_range(number):
    # Initialize the list with the starting number
    numbers = [number]
    
    # Subtract 12 until <= 0
    current = number
    while current - 12 >= 0:
        current -= 12
        numbers.append(current)
    
    # Reset current to the starting number
    current = number
    # Add 12 until >= 127
    while current + 12 <= 127:
        current += 12
        numbers.append(current)
    
    # Sort the list to have the sequence in ascending order
    numbers.sort()
    
    return numbers

def get_diatonic_notes_midi(chord_notes_midi, key, key_type):
    # Map the key to its MIDI number (assuming octave 4 for simplicity)
    key_midi = note_to_midi(key)
    
    # Define the scale intervals for major and minor keys

    major_intervals = [2, 2, 1, 2, 2, 2, 1]
    minor_intervals = [2, 1, 2, 2, 1, 2, 2]
    
    # Choose the correct intervals based on the key type
    intervals = major_intervals if key_type == 'major' else minor_intervals
    
    # Generate the scale for the key in MIDI numbers
    scale_midi = [key_midi]
    current_note = key_midi
    for interval in intervals:
        current_note += interval
        if current_note > 83:
            current_note-=12
        scale_midi.append(current_note)

    scale_midi = [item for item in scale_midi if item not in chord_notes_midi]

    # Since we're asked for the key's diatonic notes, we return the scale MIDI numbers
    return scale_midi

def note_to_midi(note):

    note_semitone = {
        'C': 72, 'C#': 73, 'Db': 73, 'D': 74, 'D#': 75, 'Eb': 75, 'E': 76, 'F': 77,
        'F#': 78, 'Gb': 78, 'G': 79, 'G#': 80, 'Ab': 80, 'A': 81, 'A#': 82, 'Bb': 82, 'B': 83
    }

    return note_semitone[note]

def move_within_note_range(content, lower_bound, higher_bound):
    for index, item in enumerate(content):
        if 'Note_on_c' in item[2]:
            content = replace_note(content, item, index, lower_bound, higher_bound)

    return content

def find_numbers(base_number):
    # Initialize an empty list to store the results
    results = []

    base_number = int(base_number)
    
    # Check numbers by adding 12
    current_number = base_number
    while current_number <= 84:
        if current_number >= 40 and current_number not in results:
            results.append(current_number)
        current_number += 12
    
    # Check numbers by subtracting 12
    current_number = base_number
    while current_number >= 40:
        if current_number <= 84 and current_number not in results:
            results.append(current_number)
        current_number -= 12
    
    # Sort the results for better readability
    results.sort()
    return results

def replace_note(content, item, index, lower_bound=40, higher_bound=84, just_change=False):
    new_note = int(item[4])
    old_note = str(item[4])

    if just_change == False:
        while new_note < lower_bound:
            new_note += 12  # Increase by an octave until within range
        while new_note > higher_bound:
            new_note -= 12  # Decrease by an octave until within range
    else:
        new_note = int(random.choice(find_numbers(old_note)))

    content[index][4] = str(new_note)

    temp_index = index+1
    while (len(content) > temp_index):
        if (('Note_off_c' in content[temp_index][2]) and (content[temp_index][4] == str(old_note))):
            content[temp_index][4] = str(new_note)
            break
        temp_index+=1
    
    return content

def generate_melody_content(grouped_chords, there_is_zero, key_type, key, hyperness):
    melody_bars = []
    overall_timer = 0
    for index2, chord_group in enumerate(grouped_chords):
        notes = []
        for note1 in chord_group:
            the_note = int(note1[0][4])
            while the_note < 72:
                the_note += 12
            while the_note > 83:
                the_note -= 12
            notes.append(the_note)
 
        chord_notes = list(set(notes))

        diatonic_notes = get_diatonic_notes_midi(chord_notes, key, key_type.lower())
        melody, overall_timer = generate_melody_bar(chord_notes, diatonic_notes, True if index2 == 0 else False, there_is_zero, overall_timer, hyperness)
        
        melody_bars.append(melody)
    
    return melody_bars

def midi_numbers_to_notes(midi_numbers):
    """Convert MIDI numbers to note letters."""
    notes_sharp = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    note_letters = []

    for midi in midi_numbers:
        note_index = midi % 12  # Get the position in the octave
        note = notes_sharp[note_index]
        note_letters.append(note)

    return note_letters

def merge_content(content):
    all_content = []

    for sub_content in content:
        all_content += sub_content
    
    all_content = sorted(all_content, key=lambda x: int(x[1]))

    return all_content

def create_strummed_version(midi_content, there_is_zero, beat_generating):

    midi_content = deepcopy(midi_content)

    strum_style= random.choice(['reverse exponential', 'linear', 'exponential', 'reverse linear'])

    if 'exponential' in strum_style:
        if beat_generating:
            strum_speed = random.choice([10, 20])
        else:
            strum_speed = random.choice([20, 40])
    else:
        strum_speed = random.choice([80, 160, 320, 640])
    
    if there_is_zero == False:
        strum_speed = strum_speed//10

    bar_size = 0
    for line in midi_content:
        if line[2] == 'Note_off_c':
            bar_size = int(line[1])
            break

    counter = 0
    for line in range(len(midi_content)):
        if (midi_content[line][2] == 'Note_on_c'):
            counter += 1
        else:
            if counter > 0:
                additional_times = []
                for i in range(counter):
                    if strum_style in ['linear', 'reverse linear']:
                        additional_time = i * strum_speed
                    elif strum_style in ['exponential', 'reverse exponential']:
                        additional_time = strum_speed * int(2 ** i) if i > 0 else 0
                    
                    if additional_time > bar_size:
                        additional_time = bar_size - (bar_size//2)

                    additional_times.append(additional_time)

                if 'reverse' in strum_style:
                    additional_times.reverse()

                for i in range(counter):
                    midi_content[line-counter+i][1] = str(int(midi_content[line-counter+i][1]) + additional_times[i])

                counter = 0
    
    start = 0
    end = 0
    for index, line in enumerate(midi_content):
        if (line[2] == 'Note_on_c') and (start == 0):
            start = index
        if line[2] == 'End_of_file':
            end = index
    main_midi_content = sorted(midi_content[start:end-1], key=lambda x: int(x[1]))
    new_midi_content = midi_content[0:start] + main_midi_content + midi_content[end-1:]

    return new_midi_content

def fit_within_range(chord_progression_content, lower_bound, higher_bound):
    chord_progression_content = move_within_note_range(chord_progression_content, lower_bound, higher_bound)
    maybe_duplicate = False

    while(maybe_duplicate == False):
        chord_progression_content, maybe_duplicate = remove_duplicate_notes(chord_progression_content)
    
    return chord_progression_content

def transpose_notes_within_bounds(midi_list, lower_bound=40, upper_bound=84):
    """
    Transposes notes in a MIDI list so that all notes fall within the specified bounds.
    
    Parameters:
    - midi_list: A list of MIDI events.
    - lower_bound: The lowest MIDI note number allowed.
    - upper_bound: The highest MIDI note number allowed.
    
    Returns:
    - A new list of MIDI events with all notes transposed within the specified bounds.
    """
    transposed_midi_list = []

    for event in midi_list:
        if len(event) > 2 and event[2] in ['Note_on_c', 'Note_off_c'] and len(event) >= 6:
            track, timestamp, event_type, channel, note, velocity = event[:6]
            note = int(note)

            # Transpose note into the specified range if necessary
            while note < lower_bound:
                note += 12
            while note > upper_bound:
                note -= 12

            # Replace the original note number with the transposed one
            transposed_event = event[:4] + [str(note)] + event[5:]
            transposed_midi_list.append(transposed_event)
        else:
            # Add non-note events directly to the transposed list
            transposed_midi_list.append(event)

    return transposed_midi_list

def exclude_lowest_note_indexes(notes_grouped):

    updated_groups = []
    lowest_notes_indexes = []

    for group in notes_grouped:
        # Find the minimum note value in the current group
        min_note_value = min(group, key=lambda x: int(x[0][4]))[0][4]
        
        # Initialize a list to store indexes of the lowest note in the group
        # min_note_indexes = []

        # Filter out the lowest notes and collect their overall indexes
        filtered_group = []
        for item in group:
            if item[0][4] == min_note_value:
                lowest_notes_indexes.append(item[1])
            else:
                filtered_group.append(item)
        
        # Add the filtered group and the lowest note indexes to their respective lists
        updated_groups.append(filtered_group)
        # lowest_notes_indexes.append(min_note_indexes)

    return updated_groups, lowest_notes_indexes

def get_individual_chords(content, split_by_event_type, include_index=True):

    all_chords = []
    end_section = []
    start_section = []
    local_chord = []
    restart = False
    for index, note in enumerate(content):
        if 'Note_on_c' in str(note) and (restart == False):
            if include_index:
                local_chord.append([note, index])
            else:
                local_chord.append(note)
        elif 'Note_off_c' in str(note):
            
            if restart == False and split_by_event_type:
                all_chords.append(local_chord)
                local_chord = []
            if include_index:
                local_chord.append([note, index])
            else:
                local_chord.append(note)
            restart = True
        else:
            if 'Note_on_c' in str(note):
                restart = False
                all_chords.append(local_chord)
                local_chord = []
                if include_index:
                    local_chord.append([note, index])
                else:
                    local_chord.append(note)
            else:
                if ('End_track' in str(note)) or ('End_of_file' in str(note)):
                    if note[1] == '0' and note[2] == 'End_track':
                        start_section.append(note)
                    else:
                        end_section.append(note)
                    continue
                elif ('Header' in str(note)) or ('Start_track' in str(note)) or ('Tempo' in str(note)) or ('Title_t' in str(note)):
                    start_section.append(note)
                    continue
                restart = False
                if local_chord != []:
                    all_chords.append(local_chord)
                pass
    
    if local_chord != []:
        all_chords.append(local_chord)

    return all_chords, start_section, end_section

def create_lower_root_version(content, lowest_notes):

    content = deepcopy(content)

    for index in lowest_notes:
        lower_note = str(int(content[index][4]) - 12)
        if int(lower_note) > 0:
            content[index][4] = lower_note
    return content

def create_chord_timing_version(chord_progression_content, there_is_zero):

    chord_progression_content = deepcopy(chord_progression_content)

    individual_chords, start_section, end_section = get_individual_chords(chord_progression_content, True)
    type = random.choice(['early start', 'early staggered'])

    if there_is_zero == True:
        bar = 3840
    else:
        bar = 384

    match type:
        case 'early start':
            inside_note_on_c = 0
            for index, chord_line in enumerate(individual_chords):
                if (inside_note_on_c == 1) or (inside_note_on_c == 2):
                    for note_line in individual_chords[index]:
                        note_line[0][1] = str(int(int(note_line[0][1]) - (bar*0.25)))
                    inside_note_on_c+=1
                elif (inside_note_on_c == 3):
                    inside_note_on_c = 0
                else:
                    inside_note_on_c+=1
        case 'early staggered':
            inside_note_on_c = 0
            for index, chord_line in enumerate(individual_chords):
                if (inside_note_on_c == 1):
                    for note_line in individual_chords[index]:
                        note_line[0][1] = str(int(int(note_line[0][1]) - (bar*0.25)))
                    inside_note_on_c+=1
                elif (inside_note_on_c == 3):
                    inside_note_on_c = 0
                else:
                    inside_note_on_c+=1
    
    individual_chords = [sublist[0] for list_of_lists in individual_chords for sublist in list_of_lists]
    output_content = start_section + individual_chords + end_section

    return output_content

def extend_to_eight_bars(content, there_is_zero):

    old_content = deepcopy(content)

    if there_is_zero:
        extend = 15360
    else:
        extend = 1536

    for line in content:
        if ('Note_on_c' in str(line)) or ('Note_off_c' in str(line)) or ('End_track' in str(line)) and (line[0] == '2'):
            line[1] = str(int(line[1]) + extend)
    
    grouped_chords1, start_section1, end_section1 = get_individual_chords(old_content, False, False)
    old_content = [item for sublist in grouped_chords1 for item in sublist]

    grouped_chords2, start_section2, end_section2 = get_individual_chords(content, False, False)
    new_content = [item for sublist in grouped_chords2 for item in sublist]

    merged_content = merge_content([old_content, new_content])
    merged_content = start_section2 + merged_content + end_section2

    return merged_content

def cut_chord_progression_to_4_bars(chord_progression_content):
    remove_indexes = []
    there_is_zero = False
    for index, note_line in enumerate(chord_progression_content):
        if (str(chord_progression_content[index][2]).strip() != 'Note_on_c') and (str(chord_progression_content[index][2]).strip() != 'Note_off_c'):
            continue
        elif str(chord_progression_content[index][1]).strip() == '0':
            zero_stripped_time = str(chord_progression_content[index][1])
        else:
            if chord_progression_content[index][1][-1] == '0':
                there_is_zero = True
                zero_stripped_time = chord_progression_content[index][1][0:-1]
            else:
                zero_stripped_time = chord_progression_content[index][1]
        
        if (int(zero_stripped_time) == 1536 and str(chord_progression_content[index][2]).strip() == 'Note_on_c') or int(zero_stripped_time) > 1536:
            remove_indexes.append(chord_progression_content[index])

    for dead_line in remove_indexes:
        chord_progression_content.remove(dead_line)

    # set the end_track
    chord_progression_content[-2][1] = chord_progression_content[-3][1]
    
    return chord_progression_content, there_is_zero

def send_notification(notification, title, message):
    msg = notification.msg(message)
    msg.set("title", title)
    try:
        notification.send(msg)
    except Exception as e:
        print(str(e))
        pass

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
        return authenticate_channel(client_secrets_file, ["https://www.googleapis.com/auth/youtube"], channel_name, full_path)

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

def seconds_to_timestamp(seconds):
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)  # Convert to int to remove fractional part
    return f"{minutes}:{remaining_seconds:02d}"

def turn_into_shorturl(notification, username, password, old_link, short_link_title):

    driver = uc.Chrome()

    username = ''
    password = ''

    url = 'https://publisher.linkvertise.com/dashboard#link-create'

    try:
        driver.get(url)
        with open("link_cookies.txt", "r") as file:
            cookies = json.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)
        driver.get(url)

        x = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CLASS_NAME, 'col title'))).text
        if 'Create Link' not in x:
            raise ValueError("Not on right page")
    
    except Exception as e:
        print(f"Error loading cookies: {e}")
        while(1):
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-target="#modal_login"]'))).click()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'email'))).send_keys(username)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(password)
                WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR,"iframe[name^='a-'][src^='https://www.google.com/recaptcha/api2/anchor?']")))
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//span[@id='recaptcha-anchor']"))).click()
                sleep(10)
                driver.switch_to.default_content()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button.btn.btn-block.btn-success[type="submit"]'))).click()

                driver.get(url)

                with open("link_cookies.txt", "w") as file:
                    json.dump(driver.get_cookies(), file)
                send_notification(notification, "SAMPLE PACK LOGIN SUCCESS", "Link for Ads Succesfully Re-Logged In")
                break
            except Exception as e:
                send_notification(notification, "SAMPLE PACK LOGIN FAIL", "Link for Ads Failed to Re-Login In. Trying again in 10 minutes.")
                driver.quit()
                sleep(600)
                driver = uc.Chrome()
    
    sleep(3)
    driver.get(url)

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[formcontrolname="target"]'))).send_keys(old_link)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.lv-button-component.lv-orange'))).click()
    toggle_input  = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, '.mat-slide-toggle input[role="switch"]')))
    if toggle_input.get_attribute('aria-checked') == 'true':
        toggle_input.click()
    else:
        pass
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'mat-input-1'))).send_keys(short_link_title[:24]) #max of 25 characters
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.lv-button-component.lv-orange'))).click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//lv-available-ads-card[.//div[@class='title' and contains(text(), 'Non-skippable Ads')]]"))).click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.lv-button-component.lv-orange'))).click()
    url_link = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'url-field')))[0]
    the_url_link = WebDriverWait(url_link, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="url"][readonly="true"]')))
    shortened_url = url = the_url_link.get_attribute('value').get_attribute('value')

    driver.quit()

    return shortened_url


def upload_to_website(notification, email, password, filename, sample_pack_name, sample_pack_price, sample_pack_image_file, description):
    driver = uc.Chrome(driver_executable_path='chromedriver.exe')#headless=True)

    ## SET THE ONE IN THE TTRY TO HEADLESS = TRUE AS WELL
    
    url = "https://payhip.com/product/add/digital"

    # login
    try:
        driver.get(url)
        with open(r"C:\Users\samlb\OneDrive\Projects\SamplePackGenerator\payhip_cookies.txt", "r") as file:
            cookies = json.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)
        driver.get(url)
        driver.refresh()
        sleep(3)
        driver.execute_script("window.open('');")
        sleep(1)
        driver.switch_to.window(driver.window_handles[0])

        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//a[contains(text(), "Add New")]'))).click()
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'digital-product-type'))).click()
    except Exception as e:
        print("Error loading cookies.")

        while(1):
            try:
                driver.get(url)
                WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "email_affil"))).send_keys(email)
                password_element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "password_f")))
                password_element.send_keys(password)
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "btn-primary"))).click()

                WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR,"iframe[name^='a-'][src^='https://www.google.com/recaptcha/api2/anchor?']")))
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//span[@id='recaptcha-anchor']"))).click()
                print('start')
                sleep(30)
                print('done')

                driver.switch_to.default_content()
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "btn-primary"))).click()

                driver.get(url)
                with open(r"C:\Users\samlb\OneDrive\Projects\SamplePackGenerator\payhip_cookies.txt", "w") as file:
                    json.dump(driver.get_cookies(), file)
                send_notification(notification, "SAMPLE PACK LOGIN SUCCESS", "Sample Pack Succesfully Re-Logged In")
                break
            except Exception as e:
                send_notification(notification, "SAMPLE PACK LOGIN FAIL", "Sample Pack Failed to Re-Login In. Trying again in 10 minutes. If this is the first error, wait for next iteration to solve captcha."+str(e))
                driver.quit()
                sleep(10)
                driver = uc.Chrome()
    
    sleep(3)
    driver.get(url)
    file_inputs = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='file'][accept][multiple]")))
    file_inputs[0].send_keys(filename)

    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "p_name"))).send_keys(sample_pack_name)
    price = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "p_price")))
    price.clear()
    price.send_keys(sample_pack_price)

    file_inputs[1].send_keys(sample_pack_image_file)
    sleep(10)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "ql-editor"))).send_keys(description)
    
    while(1):
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "addsubmit"))).click()
        sleep(3)
        try:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "confirm"))).click()
        except Exception as e:
            print("IGNORE THIS ERROR")
            print(str(e))
            break

    link = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".form-control.share-ebook-direct-link")))
    link = link.get_attribute('value')
    
    driver.quit()

    return link