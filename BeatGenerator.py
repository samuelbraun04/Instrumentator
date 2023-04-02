from audioread.exceptions import NoBackendError
from os import listdir, remove, mkdir
from platform import system
from random import randint
from scipy.io import wavfile
from shutil import make_archive, move
from time import time as epoch
import dawdreamer as daw
import librosa
import music21
import pydub

class BeatGenerator():
    
    def __init__(self, DIRECTORY_PATH, SAMPLE_RATE=44100, BUFFER_SIZE=512):
        
        self.SAMPLE_RATE = SAMPLE_RATE
        self.BUFFER_SIZE = BUFFER_SIZE

        self.engine = daw.RenderEngine(SAMPLE_RATE, BUFFER_SIZE)
        if system() == "Windows":
            self.conjoiner = "\\"
        else:
            self.conjoiner = "/"

        self.WORKSPACE_CONTAINER_PATH = DIRECTORY_PATH+self.conjoiner+'Workspace'
        self.OUTPUT_PATH = DIRECTORY_PATH+self.conjoiner+'Output'
        self.MIDI_PATH = DIRECTORY_PATH+self.conjoiner+'Ingredients'+self.conjoiner+'MIDI'
        self.SAMPLES_PATH = DIRECTORY_PATH+self.conjoiner+'Ingredients'+self.conjoiner+'Samples'
        self.PLUGINS_PATH = DIRECTORY_PATH+self.conjoiner+'Plugins'
        self.INFORMATION_TEXT_FILE = DIRECTORY_PATH+self.conjoiner+'information.txt'
        self.FONT_PATH = DIRECTORY_PATH+self.conjoiner+'Ingredients'+self.conjoiner+'RobotoSerifMedium.ttf'
        self.addToTextfile(self.INFORMATION_TEXT_FILE, "")

        self.shuffleFiles()
        self.tagPath = self.SAMPLES_PATH+self.conjoiner+'Tags'+self.conjoiner+'Tag.wav'

        self.hihatPatternPath = self.WORKSPACE_CONTAINER_PATH+self.conjoiner+'hihat.wav'
        self.snarePatternPath = self.WORKSPACE_CONTAINER_PATH+self.conjoiner+'snare.wav'
        self.perc1PatternPath = self.WORKSPACE_CONTAINER_PATH+self.conjoiner+'perc1.wav'
        self.perc2PatternPath = self.WORKSPACE_CONTAINER_PATH+self.conjoiner+'perc2.wav'
        self.clapPatternPath = self.WORKSPACE_CONTAINER_PATH+self.conjoiner+'clap.wav'
        self.kickPatternPath = self.WORKSPACE_CONTAINER_PATH+self.conjoiner+'kick.wav'
        self.eightOhEightPatternPath = self.WORKSPACE_CONTAINER_PATH+self.conjoiner+'eightOhEight.wav'
        self.uncompressedBeat = self.WORKSPACE_CONTAINER_PATH+self.conjoiner+'uncompressed beat.wav'
    
    def transposeMidiFiles(self, semitones, midiFolder):
        for directory in listdir(midiFolder):
            if directory == 'EightOhEight':
                tempDirectory1 = directory+self.conjoiner+'Not Used'+self.conjoiner
                self.sortThroughFiles(semitones, midiFolder, tempDirectory1)
                tempDirectory2 = directory+self.conjoiner+'Used'+self.conjoiner
                self.sortThroughFiles(semitones, midiFolder, tempDirectory2)
            else:
                self.sortThroughFiles(semitones, midiFolder, directory)

    def sortThroughFiles(self, semitones, midiFolder, directory):
        for file in listdir(midiFolder+self.conjoiner+directory):
            if 'TRANSPOSED' not in file:
                parsedFile = music21.converter.parse(midiFolder+self.conjoiner+directory+self.conjoiner+file)
                tranposedFile = parsedFile.transpose(semitones)
                tranposedFile.write('midi', midiFolder+self.conjoiner+directory+self.conjoiner+file[:-4]+'- TRANSPOSED.mid')
                remove(midiFolder+self.conjoiner+directory+self.conjoiner+file)
                print('Transposed: '+midiFolder+self.conjoiner+directory+self.conjoiner+file)

    def chooseRandomFile(self, folder):
        files = listdir(folder)
        index = randint(0, len(files)-1)
        chosenFile = files[index]
        return chosenFile
    
    def chooseRandomEightOhEight(self):
        files = listdir(self.MIDI_PATH+self.conjoiner+'EightOhEight'+self.conjoiner+'Not Used')
        if len(files) == 0:
            for file in listdir(self.MIDI_PATH+self.conjoiner+'EightOhEight'+self.conjoiner+'Used'):
                move(self.MIDI_PATH+self.conjoiner+'EightOhEight'+self.conjoiner+'Used'+self.conjoiner+file, self.MIDI_PATH+self.conjoiner+'EightOhEight'+self.conjoiner+'Not Used'+self.conjoiner+file)
        files = listdir(self.MIDI_PATH+self.conjoiner+'EightOhEight'+self.conjoiner+'Not Used')
        index = randint(0, len(files)-1)
        chosenFile = files[index]
        self.USED_808_FILE = chosenFile
        return chosenFile

    def addToTextfile(self, textfile, addedElement):
        with open(textfile, "a") as f:
            f.write("\n"+addedElement)
    
    def getParamIndex(self, desc, par_name):
        for parDict in desc:
            if parDict['name'] == par_name:
                return parDict['index']
        raise ValueError(f"Parameter '{par_name}' not found.")

    def convertAudioFile(self, file_path, duration=None):
        sig, rate = librosa.load(file_path, duration=duration, mono=False, sr=self.SAMPLE_RATE)
        assert(rate == self.SAMPLE_RATE)
        return sig
    
    def shuffleFiles(self):
        
        self.addToTextfile(self.INFORMATION_TEXT_FILE, "")

        self.chosenHiHatSamplePath = self.SAMPLES_PATH+self.conjoiner+'HiHat'+self.conjoiner+self.chooseRandomFile(self.SAMPLES_PATH+self.conjoiner+'HiHat')
        self.chosenHiHatMidiPath = self.MIDI_PATH+self.conjoiner+'HiHat'+self.conjoiner+self.chooseRandomFile(self.MIDI_PATH+self.conjoiner+'HiHat')
        self.addToTextfile(self.INFORMATION_TEXT_FILE, "hihat sample: "+self.chosenHiHatSamplePath)
        self.addToTextfile(self.INFORMATION_TEXT_FILE, "hihat midi: "+self.chosenHiHatMidiPath)

        self.chosenSnareSamplePath = self.SAMPLES_PATH+self.conjoiner+'Snare'+self.conjoiner+self.chooseRandomFile(self.SAMPLES_PATH+self.conjoiner+'Snare')
        self.chosenSnareMidiPath = self.MIDI_PATH+self.conjoiner+'Snare'+self.conjoiner+self.chooseRandomFile(self.MIDI_PATH+self.conjoiner+'Snare')
        self.addToTextfile(self.INFORMATION_TEXT_FILE, "snare sample: "+self.chosenSnareSamplePath)
        self.addToTextfile(self.INFORMATION_TEXT_FILE, "snare midi: "+self.chosenSnareMidiPath)
        
        self.chosenPerc1SamplePath = self.SAMPLES_PATH+self.conjoiner+'Perc1'+self.conjoiner+self.chooseRandomFile(self.SAMPLES_PATH+self.conjoiner+'Perc1')
        self.chosenPerc1MidiPath = self.MIDI_PATH+self.conjoiner+'Perc1'+self.conjoiner+self.chooseRandomFile(self.MIDI_PATH+self.conjoiner+'Perc1')
        self.addToTextfile(self.INFORMATION_TEXT_FILE, "perc1 sample: "+self.chosenPerc1SamplePath)
        self.addToTextfile(self.INFORMATION_TEXT_FILE, "perc1 midi: "+self.chosenPerc1MidiPath)

        self.chosenPerc2SamplePath = self.SAMPLES_PATH+self.conjoiner+'Perc2'+self.conjoiner+self.chooseRandomFile(self.SAMPLES_PATH+self.conjoiner+'Perc2')
        self.chosenPerc2MidiPath = self.MIDI_PATH+self.conjoiner+'Perc2'+self.conjoiner+self.chooseRandomFile(self.MIDI_PATH+self.conjoiner+'Perc2')
        self.addToTextfile(self.INFORMATION_TEXT_FILE, "perc2 sample: "+self.chosenPerc2SamplePath)
        self.addToTextfile(self.INFORMATION_TEXT_FILE, "perc2 midi: "+self.chosenPerc2MidiPath)

        self.chosenClapSamplePath = self.SAMPLES_PATH+self.conjoiner+'Clap'+self.conjoiner+self.chooseRandomFile(self.SAMPLES_PATH+self.conjoiner+'Clap')
        self.chosenClapMidiPath = self.MIDI_PATH+self.conjoiner+'Clap'+self.conjoiner+self.chooseRandomFile(self.MIDI_PATH+self.conjoiner+'Clap')
        self.addToTextfile(self.INFORMATION_TEXT_FILE, "clap sample: "+self.chosenClapSamplePath)
        self.addToTextfile(self.INFORMATION_TEXT_FILE, "clap midi: "+self.chosenClapMidiPath)

        self.chosenEightOhEightSamplePath = self.SAMPLES_PATH+self.conjoiner+'EightOhEight'+self.conjoiner+self.chooseRandomFile(self.SAMPLES_PATH+self.conjoiner+'EightOhEight')
        chosenFile = self.chooseRandomEightOhEight()
        self.chosenEightOhEightMidiPath, chosenKickMidiFile = self.MIDI_PATH+self.conjoiner+'EightOhEight'+self.conjoiner+'Not Used'+self.conjoiner+chosenFile, chosenFile
        self.addToTextfile(self.INFORMATION_TEXT_FILE, "808 sample: "+self.chosenEightOhEightSamplePath)
        self.addToTextfile(self.INFORMATION_TEXT_FILE, "808 midi: "+self.chosenEightOhEightMidiPath)

        self.chosenKickSamplePath = self.SAMPLES_PATH+self.conjoiner+'Kick'+self.conjoiner+self.chooseRandomFile(self.SAMPLES_PATH+self.conjoiner+'Kick')
        self.chosenKickMidiPath = self.MIDI_PATH+self.conjoiner+'Kick'+self.conjoiner+chosenKickMidiFile
        self.addToTextfile(self.INFORMATION_TEXT_FILE, "kick sample: "+self.chosenKickSamplePath)
        self.addToTextfile(self.INFORMATION_TEXT_FILE, "kick midi: "+self.chosenKickMidiPath)

    def makeSegment(self, samplePath, midiPath, patternPath, numberOfBeats, sampleLength, type):
        
        while(1):
            try:

                #convert the sample into a machine readable format
                convertedSample = self.convertAudioFile(samplePath)
                
                #load the sample and midi into the sampler
                sampler = self.engine.make_sampler_processor("sampler", convertedSample)
                break

            except IndexError as e:
                
                print(str(e) + ' | ' + samplePath + ' | Removed.')
                remove(samplePath)

                if type == 'hihat':
                    self.chosenHiHatSamplePath = self.SAMPLES_PATH+self.conjoiner+'HiHat'+self.conjoiner+self.chooseRandomFile(self.SAMPLES_PATH+self.conjoiner+'HiHat')
                    samplePath = self.chosenHiHatSamplePath
                if type == 'snare':
                    self.chosenSnareSamplePath = self.SAMPLES_PATH+self.conjoiner+'Snare'+self.conjoiner+self.chooseRandomFile(self.SAMPLES_PATH+self.conjoiner+'Snare')
                    samplePath = self.chosenSnareSamplePath
                if type == 'clap':
                    self.chosenClapSamplePath = self.SAMPLES_PATH+self.conjoiner+'Clap'+self.conjoiner+self.chooseRandomFile(self.SAMPLES_PATH+self.conjoiner+'Clap')
                    samplePath = self.chosenClapSamplePath
                if type == 'perc1':
                    self.chosenPerc1SamplePath = self.SAMPLES_PATH+self.conjoiner+'Perc1'+self.conjoiner+self.chooseRandomFile(self.SAMPLES_PATH+self.conjoiner+'Perc1')
                    samplePath = self.chosenPerc1SamplePath
                if type == 'perc2':
                    self.chosenPerc2SamplePath = self.SAMPLES_PATH+self.conjoiner+'Perc2'+self.conjoiner+self.chooseRandomFile(self.SAMPLES_PATH+self.conjoiner+'Perc2')
                    samplePath = self.chosenPerc2SamplePath
                if type == 'kick':
                    self.chosenKickSamplePath = self.SAMPLES_PATH+self.conjoiner+'Kick'+self.conjoiner+self.chooseRandomFile(self.SAMPLES_PATH+self.conjoiner+'Kick')
                    samplePath = self.chosenKickSamplePath
                if type == 'eightOhEight':
                    self.chosenEightOhEightSamplePath = self.SAMPLES_PATH+self.conjoiner+'EightOhEight'+self.conjoiner+self.chooseRandomFile(self.SAMPLES_PATH+self.conjoiner+'EightOhEight')
                    samplePath = self.chosenEightOhEightSamplePath
            
            except NoBackendError or FileNotFoundError as e:
                print(str(e) + '| Removed')
                remove(samplePath)

        sampler.set_data(convertedSample)
        sampler.load_midi(midiPath, beats = True)

        #if it's the 808, make sure there's no sample bleeding
        if type == 'eightOhEight':
            desc = sampler.get_parameters_description()

            sampler.set_parameter(self.getParamIndex(desc, 'Amp Env Attack'), 0.0)
            sampler.set_parameter(self.getParamIndex(desc, 'Amp Env Decay'), 0.0)
            sampler.set_parameter(self.getParamIndex(desc, 'Amp Env Sustain'), 100.0)
            sampler.set_parameter(self.getParamIndex(desc, 'Amp Env Release'), 100.0)
            
            amp_index = self.getParamIndex(desc, 'Amp Active')
            sampler.set_parameter(amp_index, 1.)
        
        #set the graph and export it to wav
        sampler_graph = [
            (sampler, [])
        ]
        self.engine.load_graph(sampler_graph)
        self.engine.render(numberOfBeats, beats=True)
        wavfile.write(patternPath, self.SAMPLE_RATE, (self.engine.get_audio()).transpose())

        audioSegment = pydub.AudioSegment.from_file(patternPath)
        audioSegment = audioSegment[0:sampleLength]
        if type == 'eightOhEight':
            audioSegment = audioSegment.fade_out(duration=int((sampleLength)/256))

        return audioSegment

    def run(self, template, bpm):

        #set the bpm
        self.engine.set_bpm(bpm)
        self.addToTextfile(self.INFORMATION_TEXT_FILE, "bpm: "+str(bpm))
        self.addToTextfile(self.INFORMATION_TEXT_FILE, "template: "+str(template))

        #eight bar length
        beatsPerBar = 32.
        eightBarLength = (60*1000/bpm)*beatsPerBar
        
        #make the segments
        hihatSegment = self.makeSegment(self.chosenHiHatSamplePath, self.chosenHiHatMidiPath, self.hihatPatternPath, beatsPerBar, eightBarLength, 'hihat')
        snareSegment = self.makeSegment(self.chosenSnareSamplePath, self.chosenSnareMidiPath, self.snarePatternPath, beatsPerBar, eightBarLength, 'snare')
        perc1Segment = self.makeSegment(self.chosenPerc1SamplePath, self.chosenPerc1MidiPath, self.perc1PatternPath, beatsPerBar, eightBarLength, 'perc1')
        perc2Segment = self.makeSegment(self.chosenPerc2SamplePath, self.chosenPerc2MidiPath, self.perc2PatternPath, beatsPerBar, eightBarLength, 'perc2')
        clapSegment = self.makeSegment(self.chosenClapSamplePath, self.chosenClapMidiPath, self.clapPatternPath, beatsPerBar, eightBarLength, 'clap')
        kickSegment = self.makeSegment(self.chosenKickSamplePath, self.chosenKickMidiPath, self.kickPatternPath, beatsPerBar, eightBarLength, 'kick')
        eightOhEightSegment = self.makeSegment(self.chosenEightOhEightSamplePath, self.chosenEightOhEightMidiPath, self.eightOhEightPatternPath, beatsPerBar, eightBarLength, 'eightOhEight')

        #make a 8 bar silent segment
        silentSegment = pydub.AudioSegment.silent(duration=((60*1000/bpm)*32))

        if template == 1: #80 bars (10 segments)
            hihatPlaylist = hihatSegment + hihatSegment + hihatSegment + silentSegment + hihatSegment + silentSegment + hihatSegment + hihatSegment + hihatSegment + hihatSegment
            snarePlaylist = silentSegment + silentSegment + snareSegment + snareSegment + silentSegment + silentSegment + snareSegment + snareSegment + silentSegment + silentSegment +snareSegment
            perc1Playlist = silentSegment + silentSegment + perc1Segment + silentSegment + silentSegment + perc1Segment + perc1Segment + silentSegment + silentSegment + perc1Segment
            perc2Playlist = silentSegment + perc2Segment + perc2Segment + silentSegment + perc2Segment + perc2Segment + perc2Segment + silentSegment + perc2Segment + perc2Segment
            clapPlaylist = clapSegment + clapSegment + clapSegment + clapSegment + clapSegment + clapSegment + clapSegment + clapSegment + clapSegment + clapSegment
            kickPlaylist = silentSegment + silentSegment + kickSegment + kickSegment + silentSegment + kickSegment + kickSegment + silentSegment + kickSegment + kickSegment
            eightOhEightPlaylist = eightOhEightSegment + eightOhEightSegment + eightOhEightSegment + silentSegment + eightOhEightSegment + eightOhEightSegment + eightOhEightSegment + silentSegment  + eightOhEightSegment  + eightOhEightSegment
            numberOfBeats = 4*80
        if template == 2: #72 bars (9 segments)
            hihatPlaylist = silentSegment + hihatSegment + hihatSegment + silentSegment + silentSegment + hihatSegment + silentSegment + hihatSegment + hihatSegment
            snarePlaylist = snareSegment + snareSegment + snareSegment + snareSegment + snareSegment + snareSegment + silentSegment + silentSegment + snareSegment
            perc1Playlist = silentSegment + silentSegment + perc1Segment + silentSegment + silentSegment + perc1Segment + silentSegment + silentSegment + perc1Segment
            perc2Playlist = silentSegment + silentSegment + perc2Segment + perc2Segment + perc2Segment + perc2Segment + silentSegment + silentSegment + perc2Segment
            clapPlaylist = clapSegment + clapSegment + clapSegment + clapSegment + clapSegment + clapSegment + clapSegment + silentSegment + clapSegment
            kickPlaylist = silentSegment + silentSegment + kickSegment + kickSegment + kickSegment + kickSegment + silentSegment + kickSegment + kickSegment
            eightOhEightPlaylist = eightOhEightSegment + eightOhEightSegment + eightOhEightSegment + silentSegment + eightOhEightSegment + eightOhEightSegment + eightOhEightSegment + eightOhEightSegment + eightOhEightSegment
            numberOfBeats = 4*72
        if template == 3: #64 bars (8 segments)
            hihatPlaylist = silentSegment + hihatSegment + hihatSegment + hihatSegment + hihatSegment + hihatSegment + silentSegment + hihatSegment
            snarePlaylist = silentSegment + silentSegment + snareSegment + silentSegment + snareSegment + snareSegment + silentSegment + snareSegment
            perc1Playlist = silentSegment + silentSegment + perc1Segment + perc1Segment + silentSegment + perc1Segment + silentSegment + perc1Segment
            perc2Playlist = silentSegment + silentSegment + perc2Segment + silentSegment + silentSegment + perc2Segment + silentSegment + perc2Segment
            clapPlaylist = clapSegment + clapSegment + clapSegment + clapSegment + clapSegment + clapSegment + clapSegment + clapSegment
            kickPlaylist = silentSegment + kickSegment + kickSegment + silentSegment + silentSegment + kickSegment + kickSegment + kickSegment
            eightOhEightPlaylist = eightOhEightSegment + silentSegment + eightOhEightSegment + silentSegment + eightOhEightSegment + eightOhEightSegment + eightOhEightSegment + eightOhEightSegment
            numberOfBeats = 4*64
        if template == 4: #72 bars (9 segments)
            hihatPlaylist = silentSegment + hihatSegment + hihatSegment + silentSegment + hihatSegment + silentSegment + hihatSegment + hihatSegment + hihatSegment
            snarePlaylist = silentSegment + snareSegment + snareSegment + snareSegment + snareSegment + snareSegment + snareSegment + snareSegment + snareSegment
            perc1Playlist = perc1Segment + silentSegment + perc1Segment + perc1Segment + perc1Segment + silentSegment + silentSegment + perc1Segment + perc1Segment
            perc2Playlist = perc2Segment + silentSegment + perc2Segment + perc2Segment + perc2Segment + silentSegment + silentSegment + perc2Segment + perc2Segment
            clapPlaylist = clapSegment + clapSegment + clapSegment + clapSegment + silentSegment + clapSegment + clapSegment + clapSegment + silentSegment
            kickPlaylist = silentSegment + silentSegment + kickSegment + silentSegment + kickSegment + kickSegment + kickSegment + kickSegment + kickSegment
            eightOhEightPlaylist = eightOhEightSegment + eightOhEightSegment + eightOhEightSegment + eightOhEightSegment + eightOhEightSegment + eightOhEightSegment + eightOhEightSegment + eightOhEightSegment + silentSegment
            numberOfBeats = 4*72
        if template == 5: #72 bars (9 segments)
            hihatPlaylist = hihatSegment + hihatSegment + hihatSegment + silentSegment + hihatSegment + hihatSegment + silentSegment + hihatSegment + hihatSegment
            snarePlaylist = silentSegment + silentSegment + snareSegment + snareSegment + silentSegment + snareSegment + snareSegment + snareSegment + snareSegment
            perc1Playlist = silentSegment + silentSegment + perc1Segment + silentSegment + perc1Segment + perc1Segment + silentSegment + perc1Segment + perc1Segment
            perc2Playlist = silentSegment + silentSegment + perc2Segment + silentSegment + perc2Segment + perc2Segment + silentSegment + perc2Segment + perc2Segment
            clapPlaylist = silentSegment + clapSegment + clapSegment + clapSegment + silentSegment + clapSegment + clapSegment + silentSegment + clapSegment
            kickPlaylist = silentSegment + kickSegment + kickSegment + kickSegment + kickSegment + kickSegment + silentSegment + silentSegment + kickSegment
            eightOhEightPlaylist = eightOhEightSegment + eightOhEightSegment + eightOhEightSegment + silentSegment + eightOhEightSegment + eightOhEightSegment + eightOhEightSegment + eightOhEightSegment + eightOhEightSegment
            numberOfBeats = 4*72
        if template == 6: #72 bars (9 segments)
            hihatPlaylist = hihatSegment + hihatSegment + hihatSegment + hihatSegment + hihatSegment + silentSegment + hihatSegment + silentSegment + hihatSegment
            snarePlaylist = silentSegment + silentSegment + snareSegment + silentSegment + snareSegment + snareSegment + snareSegment + silentSegment + silentSegment
            perc1Playlist = perc1Segment + silentSegment + perc1Segment + perc1Segment + perc1Segment + perc1Segment + perc1Segment + perc1Segment + perc1Segment
            perc2Playlist = perc2Segment + silentSegment + perc2Segment + perc2Segment + perc2Segment + perc2Segment + perc2Segment + perc2Segment + perc2Segment
            clapPlaylist = silentSegment + clapSegment + clapSegment + silentSegment + silentSegment + clapSegment + clapSegment + clapSegment + silentSegment
            kickPlaylist = silentSegment + kickSegment + kickSegment + kickSegment + kickSegment + kickSegment + kickSegment + kickSegment + silentSegment
            eightOhEightPlaylist = eightOhEightSegment + eightOhEightSegment + eightOhEightSegment + silentSegment + eightOhEightSegment + eightOhEightSegment + eightOhEightSegment + silentSegment + eightOhEightSegment
            numberOfBeats = 4*72
        if template == 7: #80 bars (10 segments)
            hihatPlaylist = silentSegment + hihatSegment + hihatSegment + silentSegment + hihatSegment + hihatSegment + hihatSegment + silentSegment + hihatSegment + hihatSegment
            snarePlaylist = snareSegment + snareSegment + snareSegment + snareSegment + snareSegment + silentSegment + snareSegment + snareSegment + snareSegment + snareSegment
            perc1Playlist = perc1Segment + perc1Segment + perc1Segment + perc1Segment + silentSegment + silentSegment + perc1Segment + perc1Segment + perc1Segment + perc1Segment
            perc2Playlist = perc2Segment + perc2Segment + perc2Segment + perc2Segment + silentSegment + silentSegment + perc2Segment + perc2Segment + perc2Segment + perc2Segment
            clapPlaylist = silentSegment + silentSegment + clapSegment + clapSegment + silentSegment + clapSegment + clapSegment + silentSegment + silentSegment + clapSegment
            kickPlaylist = silentSegment + kickSegment + kickSegment + kickSegment + silentSegment + kickSegment + kickSegment + silentSegment + kickSegment + kickSegment
            eightOhEightPlaylist = eightOhEightSegment + eightOhEightSegment + eightOhEightSegment + silentSegment + eightOhEightSegment + eightOhEightSegment + eightOhEightSegment + eightOhEightSegment + eightOhEightSegment + eightOhEightSegment
            numberOfBeats = 4*80

        #make directories
        directory, finalBeatDirectory, stemsDirectory = self.setUpDirectory(bpm)

        #move the used 808 MIDI
        move(self.MIDI_PATH+self.conjoiner+'EightOhEight'+self.conjoiner+'Not Used'+self.conjoiner+self.USED_808_FILE, self.MIDI_PATH+self.conjoiner+'EightOhEight'+self.conjoiner+'Used'+self.conjoiner+self.USED_808_FILE)

        #make stems
        hihatPlaylist.export(stemsDirectory+self.conjoiner+'HiHat Stem.wav', 'wav')
        snarePlaylist.export(stemsDirectory+self.conjoiner+'Snare Stem.wav', 'wav')
        perc1Playlist.export(stemsDirectory+self.conjoiner+'Perc1 Stem.wav', 'wav')
        perc2Playlist.export(stemsDirectory+self.conjoiner+'Perc2 Stem.wav', 'wav')
        clapPlaylist.export(stemsDirectory+self.conjoiner+'Clap Stem.wav', 'wav')
        kickPlaylist.export(stemsDirectory+self.conjoiner+'Kick Stem.wav', 'wav')
        eightOhEightPlaylist.export(stemsDirectory+self.conjoiner+'808 Stem.wav', 'wav')

        #make zip folder from stems and remove the old stems folder
        make_archive(stemsDirectory, 'zip', stemsDirectory)

        #merge all patterns together into a final beat
        middleMan1 = hihatPlaylist.overlay(snarePlaylist)
        middleMan2 = perc1Playlist.overlay(middleMan1)
        middleMan3 = perc2Playlist.overlay(middleMan2)
        middleMan4 = clapPlaylist.overlay(middleMan3)
        middleMan5 = kickPlaylist.overlay(middleMan4)
        finalUncompressed = eightOhEightPlaylist.overlay(middleMan5)
        
        #export compressed audio
        compressedFilePath = self.compressAudio(finalUncompressed, numberOfBeats, finalBeatDirectory, bpm)

        #tag audio
        self.tagAudio(compressedFilePath, finalBeatDirectory, bpm)

        return directory

    def compressAudio(self, pydubClip, numberOfBeats, finalBeatDirectory, bpm):
        
        pydubClip.export(self.uncompressedBeat, 'wav')
        playback_processor = self.engine.make_playback_processor("playback", self.convertAudioFile(self.uncompressedBeat))

        #soft clipper
        soft_clipper = self.engine.make_plugin_processor("my_soft_clipper", self.PLUGINS_PATH+self.conjoiner+'Initial Clipper.dll')
        soft_clipper.set_parameter(0, 1.0) #Threshold
        soft_clipper.set_parameter(1, 0.55) #Input gain
        soft_clipper.set_parameter(2, 0.5) #Positive saturation
        soft_clipper.set_parameter(4, 1.0) #Saturate (0.0==False, 1.0==True)

        #limiter
        limiter = self.engine.make_plugin_processor("my_limiter", self.PLUGINS_PATH+self.conjoiner+'Limiter6-x64.dll')
        limiter.set_parameter(6, 0) #turn compressor off
        limiter.set_parameter(8, 0.99) #turn the limiter threshold to -0.1
        
        graph = [
            (soft_clipper, []),
            (soft_clipper, ["playback"]),
            (limiter, ["my_soft_clipper"])
        ]

        self.engine.load_graph(graph)
        self.engine.render(numberOfBeats, beats=True)

        wavfile.write(finalBeatDirectory+self.conjoiner+str(bpm)+' BPM.wav', self.SAMPLE_RATE, (self.engine.get_audio()).transpose())

        return finalBeatDirectory+self.conjoiner+str(bpm)+' BPM.wav'

    def setUpDirectory(self, bpm):

        #make the paths
        directory = self.OUTPUT_PATH+self.conjoiner+str(epoch()).replace('.','')+' - '+str(bpm)+' BPM'
        finalBeatDirectory = directory+self.conjoiner+'Final Beat'
        stemsDirectory = directory+self.conjoiner+'Stems'

        #create the directories
        mkdir(directory)
        mkdir(finalBeatDirectory)
        mkdir(stemsDirectory)

        return directory, finalBeatDirectory, stemsDirectory

    def tagAudio(self, compressedFileUntagged, finalBeatDirectory, bpm):

        #add tag to beat
        taggedBeatSegment = pydub.AudioSegment.from_file(compressedFileUntagged)
        tag = pydub.AudioSegment.from_file(self.tagPath)
        taggedBeatSegment = taggedBeatSegment.overlay(tag, loop=True)
        taggedBeatSegment.export(finalBeatDirectory+self.conjoiner+'Tagged Final Beat '+str(bpm)+' BPM.mp3', 'mp3')