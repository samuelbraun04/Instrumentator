from datetime import datetime
from moviepy import *
from moviepy.editor import *
from my_pushover import Pushover
from os import getcwd, path, listdir
from PIL import Image
from pprint import pprint
from pydub import AudioSegment
from random import choice, randint, sample
from random_word import RandomWords
from SamplePackGenerator import *
from scipy.io import wavfile
from shutil import copy, make_archive
from time import time, sleep
import dawdreamer as daw
import googleapiclient.discovery
import googleapiclient.errors
import openai
import os
import random
import requests
import sys
import traceback

def choose_tags(tag_list, amount_allowed):
    tags = ''
    while(1):
        tags = ', '.join(sample(tag_list, 3))
        if len(tags) <= amount_allowed:
            break
    return tags


def generate_sample_pack(plugin_name="", set_preset_style="", beat_generating=False):

    #5 notes maximum per chord
    #max of 3 of the same notes per chord

    try:
        main_directory = getcwd()
        chord_progressions_path = path.join(main_directory, "Chord Progressions")
        states_and_presets_path = path.join(main_directory, "States and Presets")
        keywords_path = path.join(main_directory, "Keywords")
        
        # paths that get changed
        if beat_generating:
            midi_files_path = path.join(main_directory, "BeatGeneration", "Midi Files")
            sample_pack_path = path.join(main_directory, "BeatGeneration", "Sample Pack Template")
            sample_pack_midi_path = path.join(sample_pack_path, "MIDI")
            sample_pack_samples_path = path.join(sample_pack_path, "Samples")        
            zipped_folder_path = path.join(main_directory, "BeatGeneration", "ZIP Workspace")
            free_sample_pack_zip_folder = path.join(zipped_folder_path, "Free Version")
            full_sample_pack_zip_folder = path.join(zipped_folder_path, "Full Version")
            mp4_general_path = path.join(main_directory, "BeatGeneration")
        else:
            midi_files_path = path.join(main_directory, "Midi Files")
            sample_pack_path = path.join(main_directory, "Sample Pack Template")
            sample_pack_midi_path = path.join(sample_pack_path, "MIDI")
            sample_pack_samples_path = path.join(sample_pack_path, "Samples")        
            zipped_folder_path = path.join(main_directory, "ZIP Workspace")
            free_sample_pack_zip_folder = path.join(zipped_folder_path, "Free Version")
            full_sample_pack_zip_folder = path.join(zipped_folder_path, "Full Version")
            mp4_general_path = main_directory
        

        notification = Pushover(open('pushover_keys.txt').readlines()[0].strip())
        notification.user(open('pushover_keys.txt').readlines()[1].strip())

        client = openai.Client(api_key=(open(path.join(main_directory, 'openai_key.txt')).read()).strip())

        SAMPLE_RATE = 44100
        BUFFER_SIZE = 128

        addictive_keys = r"C:\Users\samlb\OneDrive\Projects\SamplePackGenerator\Plugins\Addictive Keys.vst3"
        ample_guitar = r"C:\Users\samlb\OneDrive\Projects\SamplePackGenerator\Plugins\AGM.vst3"
        serum = r"C:\Users\samlb\OneDrive\Projects\SamplePackGenerator\Plugins\Serum.vst3" #DOESNT WORK
        vital = r"C:\Users\samlb\OneDrive\Projects\SamplePackGenerator\Plugins\Vital.vst3"
        the_limiter = r"C:\Users\samlb\OneDrive\Projects\SamplePackGenerator\Plugins\Limiter6-x64.dll"

        plugins = {
            'addictive_keys' : addictive_keys,
            "ample_guitar" : ample_guitar,
            # "serum" : serum,
            "vital" : vital
        }

        # arpeggiator = "C:\Program Files\Steinberg\VstPlugins\CodeFN42\RandARP.dll"

        # clean all required directories
        clean_directory(midi_files_path)
        clean_directory(sample_pack_midi_path)
        clean_directory(sample_pack_samples_path)
        clean_directory(free_sample_pack_zip_folder)
        clean_directory(full_sample_pack_zip_folder)
        for file in listdir(mp4_general_path):
            if 'mp4' in file[-4:]:
                remove(path.join(mp4_general_path, file))
        print('Directories cleaned.')

        try:
            remove(free_sample_pack_zip_folder+'.zip')
        except Exception:
            pass
        try:
            remove(full_sample_pack_zip_folder+'.zip')
        except Exception:
            pass

        # get all plugins
        if plugin_name == "":
            plugin = random.choice([ample_guitar, ample_guitar, vital, vital]) # ADD addictive_keys,  LATER
        else:
            plugin = plugins[plugin_name]
        
        if set_preset_style == "":
            if plugin == vital:
                preset_style = random.choice(['Eighties', 'R and B'])
                # preset_style = 'R and B' # temp value temp value temp value temp value temp value temp value temp value temp value
            elif plugin == serum:
                preset_style = random.choice(['Lofi'])
            elif plugin == ample_guitar:
                preset_style = random.choice(['Sad', 'Not Sad'])
        else:
            preset_style = set_preset_style 

        # choose hyperness depending on style and plugin
        if plugin == addictive_keys:
            hyper_options = [1, 2, 2, 3]
            possible_variations = [1,2, 2,3, 3,4]
            bpm_range = [110,140]
            major_style = "Piano"
            beatstars_tags = choose_tags(['Juice WRLD', 'Piano', 'Sad', 'Lil Tecca', 'The Kid LAROI', 'Post Malone', 'Roddy Ricch', 'Drake', 'Lil Tjay', 'Polo G'], len(57-len(major_style)))
            plugin_name = 'Addictive Keys'
            preset_style = None
        elif plugin == ample_guitar:
            plugin_name = 'Ample Guitar'
            if preset_style == 'Sad':
                hyper_options = [3]
                possible_variations = [2, 2, 3, 3]
                major_style = "Guitar"
                beatstars_tags = choose_tags(['Pop', 'Bad Bunny', 'J Balvin', 'Latin Trap', 'Ozuna', 'Anuel AA'], 57-len(major_style))
                bpm_range = [80,110]
            elif preset_style == 'Not Sad':
                hyper_options = [3]
                possible_variations = [2,2,3, 3]
                major_style = "Guitar"
                beatstars_tags = choose_tags(['Pop', 'Bad Bunny', 'J Balvin', 'Latin Trap', 'Ozuna', 'Anuel AA'], 57-len(major_style))
                bpm_range = [110,140]
        elif plugin == vital:
            plugin_name = 'Vital'
            if preset_style == "Lofi":
                hyper_options = [3]
                possible_variations = [1,2, 2,3, 3,4]
                bpm_range = [100,130]
                major_style = "Lofi"
                minor_styles = 'Retro, Sad, Chill'
                beatstars_tags = ['Acoustic Guitar', 'Sad', 'Juice WRLD']
            elif preset_style == 'Eighties':
                hyper_options = [3]
                possible_variations = [1,2, 2,3, 3,4]
                bpm_range = [110,130]
                major_style = "80s Pop"
                minor_styles = 'The Weeknd, Dua Lipa'
                beatstars_tags = ['Acoustic Guitar', 'Sad', 'Juice WRLD']
            elif preset_style == 'Rage':
                hyper_options = [1, 2, 3]
                possible_variations = [1,2,3,4]
                bpm_range = [120,150]
                major_style = "Rage"
                minor_styles = 'Ken Carson, Yeat, BNYX'
                beatstars_tags = ['Acoustic Guitar', 'Sad', 'Juice WRLD']
            elif preset_style == 'R and B':
                hyper_options = [3]
                possible_variations = [1,2,3,4]
                bpm_range = [100,120]
                major_style = "R&B"
                minor_styles = 'Drake, SZA, Brent Faiyaz'
                beatstars_tags = ['Acoustic Guitar', 'Sad', 'Juice WRLD']
        elif plugin == serum:
            plugin_name = 'Serum'
            if preset_style == "Lofi":
                hyper_options = [3]
                possible_variations = [1,2, 2,3, 3,4]
                bpm_range = [100,130]
                major_style = "Lofi"
                minor_styles = 'Retro, Sad, Chill'
                beatstars_tags = ['Acoustic Guitar', 'Sad', 'Juice WRLD']
        
        if beat_generating:
            possible_variations = [1, 2, 2, 4]

        midi_files = []
        original_chord_prog = {}
        while len(midi_files) < 10:

            # decide hyperness
            hyperness = random.choice(hyper_options)

            # pick random chord progression
            key_type = choice(listdir(chord_progressions_path))
            random_chord_progression = choice(listdir(path.join(chord_progressions_path, key_type)))
            midi_key, roman_numeral_chords = random_chord_progression.split(' - ')
            midi_key = midi_key.strip()
            random_chord_progression_path = path.join(chord_progressions_path, key_type, random_chord_progression)
            chord_progression_content = midi_to_content(random_chord_progression_path)

            # cut chord progression to 4 bars. this code will only work of the fed MIDI is under 10 measures
            chord_progression_content, there_is_zero = cut_chord_progression_to_4_bars(chord_progression_content)
            
            # extract all notes from the chord progression
            melody_notes = extract_all_notes(chord_progression_content)
            melody_notes = midi_numbers_to_unique_notes(melody_notes)
            
            # randomize placement of notes in the chord unless it's the lowest note. this code requires the fed chord to each be a solid chord of 4 measures
            grouped_chords, start_section, end_section = get_individual_chords(chord_progression_content, False)
            grouped_chords, lowest_notes_indexes = exclude_lowest_note_indexes(grouped_chords)
            for chord in grouped_chords:
                chord_progression_content = randomize_subsection_by_indexes(chord_progression_content, chord)
            
            # extend to 8 bars
            chord_progression_content = extend_to_eight_bars(chord_progression_content, there_is_zero)
            roman_numeral_chords += roman_numeral_chords
            
            # make variations
            special_change = random.choice(possible_variations)
            match special_change:
                case 1:
                    chord_progression_content = create_lower_root_version(chord_progression_content, lowest_notes_indexes)
                case 2:
                    chord_progression_content = create_strummed_version(chord_progression_content, there_is_zero, beat_generating)
                case 3:
                    chord_progression_content = create_chord_timing_version(chord_progression_content, there_is_zero)
                case 4:
                    pass

            for index, line in enumerate(chord_progression_content):
                if ('Note_on_c' in str(line) or 'Note_off_c' in str(line)):
                    chord_progression_content[index][5] = '90'
            
            add_melody = random.randint(1,4)

            pre_melody_content = chord_progression_content
            if add_melody != 1:

                # make melody
                grouped_chords, start_section, end_section = get_individual_chords(chord_progression_content, False)
                melody_bars = generate_melody_content(grouped_chords, there_is_zero, key_type, midi_key, hyperness)

                # make final midi
                melody_bars = [item for sublist in melody_bars for item in sublist]
                grouped_chords, start_section, end_section = get_individual_chords(chord_progression_content, False, False)
                main_content = [item for sublist in grouped_chords for item in sublist]
                merged_content = merge_content([main_content, melody_bars])
                final_content = start_section + merged_content + end_section
                final_content, useless = remove_duplicate_notes(final_content)
                
                chord_progression_content = final_content
            
            # remove duplicates
            maybe_duplicate = False
            while(maybe_duplicate == False):
                chord_progression_content, maybe_duplicate = remove_duplicate_notes(chord_progression_content)

            # final little fix to fix issue that came up once
            for index, line in enumerate(chord_progression_content):
                if ('Note_on_c' in str(line) or 'Note_off_c' in str(line)):
                    if int(chord_progression_content[index][1]) > 30720:
                        chord_progression_content[index][1] = '30720'
            
            # if guitar plugin, put notes within the right range
            if plugin == r"C:\Users\samlb\OneDrive\Projects\SamplePackGenerator\Plugins\AGM.vst3":
                chord_progression_content = transpose_notes_within_bounds(chord_progression_content, 40, 84)
            
            chord_progression_content = fix_midi_notes(chord_progression_content)
            
            bpm = random.randint(bpm_range[0], bpm_range[1])
            random_word = RandomWords().get_random_word()
            random_word = random_word.title()
            filename = random_word+' - '+str(bpm)+' BPM - '+midi_key+' '+key_type+' - '+(str(time()).replace('.',''))[-9:]
            
            # make final midi for user
            final_user_midi = path.join(sample_pack_midi_path, filename+'.mid')
            content_to_midi(chord_progression_content, final_user_midi)

            if (plugin == vital or plugin == ample_guitar):

                # create buffer space
                if there_is_zero:
                    buffer = 15360
                else:
                    buffer = 1536
                
                for index, line in enumerate(chord_progression_content):
                    if ('Note_on_c' in str(line) or 'Note_off_c' in str(line)):
                        chord_progression_content[index][1] = str(int(chord_progression_content[index][1].strip()) + buffer)
                
                chord_progression_content[-2][1] = chord_progression_content[-3][1]
                chord_progression_content[-1][1] = '0'

                # add buffer note
                midi_buffer_note = note_to_midi(midi_key)
                line_counter = 0
                while(line_counter < len(chord_progression_content)-1):
                    if chord_progression_content[line_counter][2].strip() == 'Note_on_c':
                        note_start = ['2', '0', 'Note_on_c', '0', str(midi_buffer_note), '20']
                        note_end = ['2', '240', 'Note_off_c', '0', str(midi_buffer_note), '20']
                        temp_list = chord_progression_content[:line_counter]
                        temp_list.append(note_start)
                        temp_list.append(note_end)
                        chord_progression_content = temp_list + chord_progression_content[line_counter:]
                        break
                    line_counter+=1
            
            the_midi_file = path.join(midi_files_path, filename+'.mid')
            open('chord_log.txt', 'a+').write(the_midi_file+'\n'+str(chord_progression_content)+'\n\n\n')
            content_to_midi(chord_progression_content, the_midi_file)
            midi_files.append(the_midi_file)
            original_chord_prog[the_midi_file] = random_chord_progression_path

        print("Midi files rendered.")

        # setup plugins and get preset directory
        if plugin == ample_guitar:
            use_states = True
            preset_directory = path.join(states_and_presets_path, 'Ample Guitar')
            customizables = []
            
            # turn off echo
            match preset_style:
                case "Sad":
                    customizables = [
                        90, 0.0,
                        3
                    ]
                case "Not Sad":
                    customizables = [
                        90, 0.0,
                        3
                    ]
        elif plugin == addictive_keys:
            preset_directory = ''
            customizables = []
        elif plugin == vital:
            use_states = True
            preset_directory = path.join(states_and_presets_path, 'Vital', preset_style)
            match preset_style:
                case "Eighties":
                    customizables = [
                        445, 1.0, # TURN ON REVERB
                        3, # CHANCE 1/# THAT IT ACTIVATES
                        439, round(random.uniform(0.50, 0.60), 4),
                        1
                    ]
                case "Rage":
                    customizables = []
                case "R and B":
                    customizables = []
        elif plugin == serum:
            use_states = False
            preset_directory = path.join(states_and_presets_path, 'Serum', preset_style)
            customizables = []

        engine = daw.RenderEngine(SAMPLE_RATE, BUFFER_SIZE)
        the_plugin = engine.make_plugin_processor("my_synth", plugin)
        print("Re-loading plugin....")
        sleep(20)
        limiter = engine.make_plugin_processor("limiter", the_limiter)
        # arpeggiator = engine.make_plugin_processor("arpeggiator", arpeggiator)

        # ##########################################################
        # ############ TURN PRESETS TO STATES MANUALLY #############
        # ##########################################################

        # x = the_plugin.get_parameters_description()
        # open('plugin_info.txt', 'w').write(str(x))
        # exit()
        # for file in listdir(preset_directory):
        #     print(file)
        #     save_state(the_plugin, path.join(states_and_presets_path, 'Ample Guitar',  file[:file.find('.')]))
        # exit()

        # ##########################################################
        # ############ TURN PRESETS TO STATES MANUALLY #############
        # ##########################################################

        for midi_file in midi_files:

            filename = midi_file.split('\\')[-1]
            name, bpm, key, id = filename.split(' - ')

            int_bpm = int((bpm.split(' ')[0]).strip())
            print(int_bpm)
            
            current_preset_or_state = path.join(preset_directory, random.choice(listdir(preset_directory)))
            the_plugin.load_midi(midi_file, beats=True)
            engine.set_bpm(int_bpm)
            pprint(midi_file)

            graph = [
                (the_plugin, []),
                (limiter, [the_plugin.get_name()])
            ]

            if use_states:

                # load the selected plugin state
                the_plugin.load_state(current_preset_or_state)

                # load specific customizes for the plugin
                for counter in range(int(len(customizables)/3)):
                    current_index = ((counter+1)*3)-1
                    if random.randint(1, customizables[current_index]) == 1:
                        the_plugin.set_parameter(customizables[current_index-2], customizables[current_index-1])

            else:

                # load the selected preset
                the_plugin.load_preset(current_preset_or_state)
                sleep(5)

            if plugin == ample_guitar:
                if str(the_plugin.get_parameter(90)).strip() == '0.0':
                    the_plugin.set_parameter(91, 0.0)
                
                # setup guitar to be played
                the_plugin.set_parameter(120, 0.5)
                the_plugin.set_parameter(118, 1)
                the_plugin.set_parameter(122, 1)

            limiter.load_state(path.join(states_and_presets_path, "Limiter", "limiter_state_2"))
            engine.load_graph(graph)
        
            if plugin == vital:
                engine.render(48, beats=True)
            elif plugin == ample_guitar:
                engine.render(48, beats=True)
            else:
                engine.render(32, beats=True)

            audio = engine.get_audio()
            wav_filename = path.join(sample_pack_samples_path, (filename.split('.')[0])+'.wav')
            wavfile.write(wav_filename, SAMPLE_RATE, audio.transpose())

            if plugin == vital:
                audio_segment = AudioSegment.from_wav(wav_filename)
                audio_segment = audio_segment[((60000/int_bpm) * 16):]     
                peak_audio = int(audio_segment.max_dBFS)
                desired_audio_loudness = -5
                if peak_audio != desired_audio_loudness:
                    audio_segment = audio_segment - (peak_audio - desired_audio_loudness)
                audio_segment.export(wav_filename, format='wav')
            if plugin == ample_guitar:
                audio_segment = AudioSegment.from_wav(wav_filename)
                audio_segment = audio_segment[((60000/int_bpm) * 16):]
                
                audio_segment.export(wav_filename, format='wav')
                audio_segment.export(wav_filename[:wav_filename.find('.')]+'_pre.wav', format='wav')
                
                if randint(1,3) == 1:

                    playback_processor = engine.make_playbackwarp_processor("melody_"+(str(time()).replace('.','')), load_audio_file(wav_filename))
                    
                    semitones = randint(-6, 3) #-4, 2
                    pitch_shift_ratio = 2 ** (semitones / 12)
                    time_stretch_ratio = 1 / pitch_shift_ratio
                    
                    playback_processor.time_ratio = time_stretch_ratio  # Play back in twice the amount of time (i.e., slowed down).
                    playback_processor.transpose = semitones  # Down 5 semitones.

                    playback_processor.set_options(
                        # daw.PlaybackWarpProcessor.option.OptionTransientsSmooth |
                        daw.PlaybackWarpProcessor.option.OptionPitchHighQuality# |
                        # daw.PlaybackWarpProcessor.option.OptionChannelsTogether # remove maybe
                    )

                    graph = [
                        (playback_processor, []),
                    ]

                    engine.load_graph(graph)
                    engine.render(32, beats=True)
                    audio = engine.get_audio()
                    wavfile.write(wav_filename, SAMPLE_RATE, audio.transpose())

                    engine = daw.RenderEngine(SAMPLE_RATE, BUFFER_SIZE)
                    the_plugin = engine.make_plugin_processor("my_synth", plugin)
                    print("Re-loading plugin....")
                    sleep(20)
                    limiter = engine.make_plugin_processor("limiter", the_limiter)

            if (beat_generating):
                return wav_filename, midi_file, original_chord_prog[midi_file], int_bpm, key, major_style, beatstars_tags

        print("Samples rendered.")

        # generate video
        sample_clips = []
        time_counter = 0
        time_stamp = {}
        free_version = []
        free_samples = random.sample(listdir(sample_pack_samples_path), 7) 

        for file in free_samples:
            the_file = path.join(sample_pack_samples_path, file)

            free_version.append(file)
            audio_file_clip = AudioFileClip(the_file)
            
            sample_clips.append(audio_file_clip)
            old_time_counter = time_counter
            time_counter += audio_file_clip.duration
            time_stamp[file] = [old_time_counter, time_counter]
            
        sample_audio_clip = concatenate_audioclips(sample_clips)

        keywords = open(path.join(keywords_path, plugin_name+' - '+preset_style+'.txt'), 'r').readlines()
        script_response = client.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=[
            {"role": "system", "content": "You will be turning a list of tags into an extremely long and detailed paragraph using as many of the tags as possible, so that it describes a pack of samples and loops. IMPORTANT: Provide the text only, with no added commentary, as the output will be fed directly into a program."},
            {"role": "user", "content": "The tags for this sample pack are: "+keywords[0].strip()}
            ]
        )
        keywords[0] = script_response.choices[0].message.content
            
        # generate background_and_thumbnail using stable diffusion FROM NOW ON
        image_ideas = ((keywords[2].strip()).split(','))
        print(image_ideas)
        generated_image = client.images.generate(
            model="dall-e-3",
            prompt="Make art of: "+image_ideas[randint(0,len(image_ideas)-1)]+". The art should be an aerial view and in the style of a painting and have one main subject. IMPORTANT: Do not put any words on the picture.",
            n=1,
            size="1024x1024"
        )
        response = requests.get(generated_image.data[0].url)
        background_and_thumbnail = os.path.join(main_directory, 'thumbnail.png')
        payhip_picture = os.path.join(main_directory, 'payhip_picture.png')
        with open(background_and_thumbnail, "wb") as file:
            file.write(response.content)
        with open(payhip_picture, "wb") as file:
            file.write(response.content)

        original_image = Image.open(background_and_thumbnail)
        aspect_ratio = original_image.width / original_image.height
        new_width = int(aspect_ratio * 1080)
        resized_image = original_image.resize((new_width, 1080), Image.LANCZOS)
        canvas = Image.new('RGB', (1920, 1080), (0, 0, 0))
        canvas.paste(resized_image, ((1920 - new_width) // 2, 0))
        canvas.save(background_and_thumbnail)

        background_and_thumbnail_clip = ImageClip(background_and_thumbnail)
        background_and_thumbnail_clip = background_and_thumbnail_clip.with_audio(sample_audio_clip)
        background_and_thumbnail_clip = background_and_thumbnail_clip.with_duration(sample_audio_clip.duration)
        video_name = minor_styles.replace(',', '')+'.mp4'
        background_and_thumbnail_clip.write_videofile(video_name, fps=30)

        print("Video rendered.")

        full_read_me = '''License: You are granted a non-exclusive, worldwide, royalty-free license to use, modify, and incorporate these samples into any of your projects, including commercial ones.
Restrictions: You may not claim the original samples as your own, sell them as standalone files, or include them in another sample pack for sale or distribution.
Ownership: The samples remain the intellectual property of prod.ohsamuel. Using them does not give you ownership rights.
        '''

        free_read_me = '''Royalty-Free Use for Songs: You are granted a non-exclusive, worldwide, royalty-free license to use these samples in your own songs. You may keep 100% of the ad-revenue earnings from songs that you make using these samples.
Beat Sales on BeatStars: If you use these samples in beats you intend to sell on BeatStars, you are required to split the earnings 50/50 with me. Set up the revenue share on BeatStars through the collaboration feature, and send 50% of earnings from sales of these beats to my BeatStars account (username: prodohsamuel, email: ohsamuelofficial@gmail.com).
Restrictions: You cannot claim the original samples as your own, sell them as standalone files, or include them in another sample pack.
Ownership: The samples remain my intellectual property. Using them does not transfer ownership rights to you.
Liability: The samples are provided 'as is' without warranties. I am not liable for any damages arising from their use.
Termination: This agreement can be terminated if you fail to adhere to its terms, requiring you to cease using the samples and delete them.
        '''

        # make free zipped using mp3 and 7 random files
        for file in free_samples:
            copy(path.join(sample_pack_samples_path, file), free_sample_pack_zip_folder)
            free_wav = path.join(free_sample_pack_zip_folder, file)
            wav_audio = AudioSegment.from_wav(free_wav)
            wav_audio.export(free_wav[:free_wav.find('.')-1]+'.mp3', format="mp3")
            remove(path.join(free_sample_pack_zip_folder, file))
        open(path.join(free_sample_pack_zip_folder, '!README.txt'), 'w').write(free_read_me)
        make_archive(free_sample_pack_zip_folder, 'zip', free_sample_pack_zip_folder)

        # make full version using wav and all files
        for file in listdir(sample_pack_samples_path):
            copy(path.join(sample_pack_samples_path, file), full_sample_pack_zip_folder)
        for midi_file in listdir(sample_pack_midi_path):
            copy(path.join(sample_pack_midi_path, midi_file), full_sample_pack_zip_folder)
        open(path.join(full_sample_pack_zip_folder, '!README.txt'), 'w').write(full_read_me)
        make_archive(full_sample_pack_zip_folder, 'zip', full_sample_pack_zip_folder)

        # sample pack name
        sample_pack_name = '12345678910'
        while(len(sample_pack_name) > 10):
            sample_pack_name = RandomWords().get_random_word()
            sample_pack_name = sample_pack_name.upper()

        # free pack upload
        email = "casio.cdp.240r@gmail.com"
        password = "BDDu3j0dM1mr6!MMa92O"
        free_title = sample_pack_name+' - Free Version'
        free_pack_link = upload_to_website(notification, email, password, free_sample_pack_zip_folder+'.zip', free_title, '0.00', payhip_picture, "7 MP3 Samples. Terms and Conditions inside ZIP file. Listen to the pack on my YouTube channel.")
        full_pack_link = upload_to_website(notification, email, password, full_sample_pack_zip_folder+'.zip', sample_pack_name+' - Full Version', '4.95', payhip_picture, "10 High Quality WAV Samples and 10 MIDI files. Terms and Conditions inside ZIP file. Listen to the pack on my YouTube channel.")

        print("Samples uploaded to Payhip")

        # shortened_link_to_free_pack = turn_into_shorturl(notification, email, 't3hwwPhY$-2a.HV', free_pack_link, free_title[0:24])

        video_title = '[FREE FOR PROFIT] '+major_style+' Sample Pack - '+minor_styles+' "'+sample_pack_name+'" Royalty Free'

        video_sample_time_stamps = ''
        for sample in time_stamp.keys():
            video_sample_time_stamps += str(seconds_to_timestamp((time_stamp[sample])[0]))+' - '+(sample.split(' - ')[0]).strip()+'\n'

        video_description = open(path.join(main_directory, 'description.txt'), encoding='utf-8').read()
        video_description = video_description.replace("THE_TIMESTAMPS", video_sample_time_stamps)
        video_description = video_description.replace("PACK_NAME", sample_pack_name)
        video_description = video_description.replace("THE_KEYWORDS", keywords[0].strip())
        video_description = video_description.replace("THE_TAGS", keywords[1].strip())

        print(video_title)
        print(video_description)

        youtube = load_or_authenticate_channel('prodohsamuel', path.join(main_directory, "client_secret_643590692955-v30jg61vqaue6odc2km5vipni0aopnej.apps.googleusercontent.com.json"), main_directory)

        body = {
            "snippet": {
                "categoryId": "10",
                "description": video_description,
                "title": video_title[0:99]
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False,
            }
        }

        insert_request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=googleapiclient.http.MediaFileUpload(path.join(main_directory, video_name), chunksize=-1, resumable=True)
        )

        status, response = insert_request.next_chunk()

        playlist_item = { 'snippet': { 'playlistId': 'PLhq4WA4lOWb5pTZU1rzoVbD3Ok2C_rJDt', 'resourceId': { 'kind': 'youtube#video', 'videoId': response['id'] } } }
        playlist_item = youtube.playlistItems().insert( part='snippet', body=playlist_item ).execute()

        send_notification(notification, 'SAMPLE PACK UPLOADED', 'Sample pack succesfully uploaded.')
        open(r"C:\Users\samlb\OneDrive\Projects\main_log.txt", 'a+', encoding='utf-8').write(str(datetime.now())+'\n'+str(locals())+'\n\n\n\n')

    except Exception as e:
        open(r"C:\Users\samlb\OneDrive\Projects\main_log.txt", 'a+', encoding='utf-8').write(str(datetime.now())+'\n'+traceback.format_exc()+'\n\n'+str(locals())+'\n\n\n\n')
        send_notification(notification, 'SAMPLE PACK ERROR', traceback.format_exc())
        # print(traceback.format_exc())
        traceback.print_exc()
        raise e

try:
    if sys.argv[1] == 'True':
        generate_sample_pack()
except Exception:
    pass