#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep  5 10:37:56 2020

@author: benadey
"""
from mido import MidiFile, Message, MidiTrack, tick2second, bpm2tempo, \
second2tick, MetaMessage
import random
import numpy as np
import math
from operator import itemgetter
from PerceptualBeatEstimator import PerceptualBeatEstimator

def midi2string(midi: MidiFile):
    '''
    Return a string containing each midi message on a newline.
    Meta messages are indented.

    Parameters
    ----------
    midi : A MidiFile object

    Returns
    -------
    string : output string with each midi message on a new line

    '''
    
    string = ''

    # iterate through each track (up to 16 midi tracks)
    for i, track in enumerate(midi.tracks):
        string = string + 'Track {}: {}'.format(i, track.name) + '\n'
        
        # iterate through each message in track i
        for msg in track:
            if msg.is_meta:
                string = string + '\t' + str(msg) + '\n'
            else:
                string = string + str(msg) + '\n'
        string = string + '\n'
    
    return string

def midi2times(midi: MidiFile):
    '''
    Returns a list containing the times of each note_on message in
    the input MidiFile object.

    Parameters
    ----------
    midi : MidiFile
        A MidiFile object containing note_on messages

    Returns
    -------
    times : list
        A list of onset times.

    '''
    times = []
    time = 0  # world clock time
    tempo = 500000
    
    # iterate only through track 0
    for msg in midi.tracks[0]:
        time = time + tick2second(msg.time, midi.ticks_per_beat, tempo)
        if msg.type=='set_tempo':
            tempo = msg.tempo
        if msg.type=='note_on':
            if msg.velocity != 0:
                times.append(time)
    
    return times

def times2midi(times: list, tempo:float=120, note=37, note_length=167, track_name='track'):
    '''
    Returns a MidiFile object containing a single track with
    a note_on message at every time in the input times:list.

    Parameters
    ----------
    times : list
        List of absolute times of note onsets, where each time is
        measured from the start of the track.
    tempo : float, optional
        Tempo of output MIDI file in bpm. The default is 120.
    note : int, optional
        MIDI note number to play at each time. The default is 37.
    note_length : TYPE, optional
        Length of each output note in ticks. The default is 167.
    track_name : TYPE, optional
        Name of MIDI track. The default is 'track'.

    Returns
    -------
    midi : MidiFile
        A MidiFile object containing a note_on message for every time
        in times:list.

    '''
    midi = MidiFile()
    track = MidiTrack()
    midi.tracks.append(track)
    
    # calculate number of ticks per beat
    ppq = bpm2tempo(tempo)
    
    total_ticks = 0  # keeps track of number of ticks from start
    
    # write out the initial meta messages
    track.name = track_name
    track.append(MetaMessage('set_tempo', tempo=ppq, time=0))
    
    for t_onset in times:
        
        # calculate number of ticks from start of track to onset
        abs_ticks = round(second2tick(t_onset, midi.ticks_per_beat, ppq))
        
        # calculate number of ticks since previous message
        ticks_interval = abs_ticks - total_ticks
        
        # add a note on message, followed by a note off message
        track.append(Message('note_on', time=ticks_interval, note=note, \
                             velocity=98))
        track.append(Message('note_off', time=note_length, note=note, \
                             velocity=98))
        
        total_ticks = abs_ticks + 167
    
    # return a MidiFile object
    return midi

def accuracyOfClicks(observed:list, expected:list, num_silent_bars=0):
    
    # define standard deviation of click accuracy
    stdDev_click = 1
    
    arr_error = [None] * len(observed)
    i = 0
    for t_click in observed:
        if i < len(expected) :
            arr_error[i] = (t_click-expected[i])**2
            i=i+1
        else:
            # more clicks were generated than expected
            break
    
    # delete any None values
    arr_error = [x for x in arr_error if x is not None]
    
    error_rms = math.sqrt(sum(arr_error))
    accuracy = math.exp(-error_rms**2/stdDev_click)
    return accuracy\



def tempo2cc(tempo):
    '''
    Returns a Message object that can be sent to MainStage to change
    MainStage's tempo.

    Parameters
    ----------
    tempo : float
        tempo in bpm.

    Returns
    -------
    cc : mido Message
        Message object to be sent on output port to MainStage.

    '''
    assert((tempo>=30) and (tempo<=300)), "tempo must be in the range 30-300 bpm"
    
    # Convert tempo to control_change number
    cc_num = int(((tempo - 29.9999)*10) // 128 + 14)
    
    # Convert tempo to control change value
    cc_value = int(((tempo - 29.9999)*10) % 128)
    
    # Return cc message
    cc = Message('control_change', control=cc_num, value=cc_value)
    return cc

def stochasticDrummer(tempoInit=120, stdDev_TEMPO=0, stdDev_ERROR=0, pattern_KICK=[], pattern_SNARE=[], prob=[], \
    Nb = 4, beatDiv=2, NumBars=32, syncBeats=True, seperateFiles=False):
    '''
    Returns mido MidiFiles of step-sequenced drums playing the specified pattern.
    At each subbeat step (e.g. eighth note), onset error is added at the specified std. deviation (stdDev_ERROR)
    At each beat step (e.g. quarter note), tempo error is added at the specifed std. deviation (stdDev_TEMPO)

    Parameters
    ----------

    tempoInit: tempo in BPM.
    stdDev_TEMPO: std. deviation of beat interval change in ms.
    stdDev_ERROR: std. deviation of error in onset time in ms.
    '''

    # MIDI note numbers
    kick = 36
    snare = 38
    cb = 56#47  # cowbell

    # MIDI track parameters
    ticks_per_beat = 480

    # algorithm parameters
    IBI = 60/tempoInit  # Inter-beat interval in seconds
    tempo = bpm2tempo(tempoInit)  # tempo in microseconds per beat
    note_off_time = int(round(ticks_per_beat/(beatDiv*4)))

    # generate noise arrays
    IBI_noise = np.random.normal(0, stdDev_TEMPO/1000, NumBars*Nb)  # beat interval change at each beat in seconds
    onset_error = np.random.normal(0, stdDev_ERROR/1000, NumBars*Nb*beatDiv)  # onset errors at each sub beat in seconds

    if not pattern_KICK:    # if no kick pattern provided, use the default
        pattern_KICK = [1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0]
    if not pattern_SNARE:    # if no snare pattern provided, use the default
        pattern_SNARE = [0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1]
    if not prob:    # if no probability array provided, use the default
        #prob = [1, 0.4, 0.5, 0, 1, 0.6, 0.7, 0.2, 1, 0.5, 0.7, 0, 1, 0.7, 0.8, 0.4]
        prob = (np.ones(len(pattern_KICK))).tolist()
    

    track_o = MidiTrack()
    track_p = MidiTrack()
    if seperateFiles:
        onsets = MidiFile()     # onsets
        p_beats = MidiFile()    # perceptual beats
        onsets.tracks.append(track_o)
        p_beats.tracks.append(track_p)
    else:
        midi = MidiFile()
        midi.tracks.append(track_o)
        midi.tracks.append(track_p)
    


    # 1. Initial Meta Messages
    track_o.name = f'tempoInit={tempoInit}bpm, stdDev_TEMPO={stdDev_TEMPO}ms, stdDev_ERROR={stdDev_ERROR} ONSETS'
    track_o.append(MetaMessage('set_tempo', tempo=tempo, time=0))
    #track_o.append(MetaMessage('instrument_name', name='808 Flex', time=0))
    track_o.append(MetaMessage('time_signature', numerator=Nb, denominator=4, clocks_per_click=24, notated_32nd_notes_per_beat=8, time=0))

    track_p.name = f'tempoInit={tempoInit}bpm, stdDev_TEMPO={stdDev_TEMPO}ms, stdDev_ERROR={stdDev_ERROR} PERCEPTUAL BEATS'
    track_p.append(MetaMessage('set_tempo', tempo=tempo, time=0))
    #track_p.append(MetaMessage('instrument_name', name='808 Flex', time=0))
    track_p.append(MetaMessage('time_signature', numerator=Nb, denominator=4, clocks_per_click=24, notated_32nd_notes_per_beat=8, time=0))

    # 2. [Nb x ] Constant tempo beats - Only do this if syncBeats is True
    o_ticks_accum = 0
    p_ticks_accum = 0
    if syncBeats:
        track_o.append(Message('note_on', time=0, note=kick, velocity=127))
        track_o.append(Message('note_off', time=note_off_time, note=kick, velocity=127))
        track_p.append(Message('note_on', time=0, note=cb, velocity=127))
        track_p.append(Message('note_off', time=note_off_time, note=cb, velocity=127))
        p_ticks_accum = p_ticks_accum + note_off_time
        o_ticks_accum = o_ticks_accum + note_off_time
        for i in range(Nb-1):
            # kick note
            track_o.append(Message('note_on', time=ticks_per_beat-note_off_time, note=kick, velocity=127))
            track_o.append(Message('note_off', time=note_off_time, note=kick, velocity=127))
            o_ticks_accum = o_ticks_accum + ticks_per_beat

    # 3. Make an array of tempo change times (and tempos)
        # at the same time, produce the perceptual beat track
    array_o = []
    for bp in range(0, Nb*NumBars): # loop through beats in whole performance
        # Add Tempo Noise ---------------------------------------------------------------------
        # 1. Adjust the current IBI by a noise amount
        IBI = IBI + IBI_noise[bp]
        # 2. Calculate the new tempo in microseconds per beat
        new_tempo = bpm2tempo(60/IBI)
        # -------------------------------------------------------------------------------------

        # PERCEPTUAL BEAT TRACK ---------------------------------------------------------------

        # 1. Calculate time in ticks from start of file to this perceptual beat
        p_ticks_since_start = Nb*ticks_per_beat*int(syncBeats) + bp*ticks_per_beat

        # 2. Subtract accumulated ticks
        p_ticks_since_last_pb = int(round(p_ticks_since_start - p_ticks_accum))

        # 3. Add tempo change and perceptual beat
        if new_tempo != tempo:  # if tempo has changed, create a new tempo message, otherwise ignore
            tempo = new_tempo
            track_p.append(MetaMessage('set_tempo', tempo=tempo, time=p_ticks_since_last_pb))
            track_p.append(Message('note_on', time=0, note=cb, velocity=127))
            track_p.append(Message('note_off', time=note_off_time, note=cb, velocity=127))
            array_o.append((int(round(p_ticks_since_start)), 1, 'set_tempo', tempo))  # key: 0=note_off, 1=tempo, 2=note_on
        else:
            track_p.append(Message('note_on', time=p_ticks_since_last_pb, note=cb, velocity=127))
            track_p.append(Message('note_off', time=note_off_time, note=cb, velocity=127))

        # add to accumulated total
        p_ticks_accum = p_ticks_accum + p_ticks_since_last_pb + note_off_time

        # -------------------------------------------------------------------------------------

        # Add final perceptual beat
        # 1. Calculate time in ticks from start of file to this perceptual beat
    p_ticks_since_start =  Nb*ticks_per_beat*int(syncBeats) + Nb*NumBars*ticks_per_beat
        # 2. Subtract accumulated ticks
    p_ticks_since_last_pb = int(round(p_ticks_since_start - p_ticks_accum))
        # 3. Add note indicating perceptual beat and add to accumulated total
    track_p.append(Message('note_on', time=p_ticks_since_last_pb, note=cb, velocity=127))
    track_p.append(Message('note_off', time=note_off_time, note=cb, velocity=127))
    p_ticks_accum = p_ticks_accum + p_ticks_since_last_pb + note_off_time



    # 4. Make an array of step numbers and times in ticks
    step = 0    # step number (always in range: 1 - [len(pattern_KICK)])
    tempo = tempoInit  # restore tempo to intial for this run
    for bp in range(0, Nb*NumBars): # loop through beats in whole performance
        # Add Tempo Noise ---------------------------------------------------------------------
        # 1. Adjust the current IBI by a noise amount
        IBI = IBI + IBI_noise[bp]
        # 2. Calculate the new tempo in microseconds per beat
        tempo = bpm2tempo(60/IBI)
        # -------------------------------------------------------------------------------------

        # ONSET TRACK -------------------------------------------------------------------------
        for sb in range(0, beatDiv):    # loop through subbeats within beat
            # 1. Calculate time in ticks from start of file to this step
            o_ticks_since_start = Nb*ticks_per_beat*int(syncBeats) + bp*ticks_per_beat\
                 + sb*ticks_per_beat/beatDiv + second2tick(onset_error[bp*beatDiv + sb], ticks_per_beat, tempo)
            if o_ticks_since_start < 0:   # may occur at first step if error is negative and no sync beats
                o_ticks_since_start = 0
            
            
            # 2. add time and step number to array_steps
            if stepShouldPlay(prob[step]):
                array_o.append((int(round(o_ticks_since_start)), 2, 'note_on', step))
                array_o.append((int(round(o_ticks_since_start+note_off_time)), 0, 'note_off', step))

            # 3. increment step
            step = step + 1
            if step == len(pattern_KICK):   # step count wraps around
                step = 0

        # -------------------------------------------------------------------------------------


    # 5. Finally, sort list of onset messages by time and add to onset track
    array_o = sorted(array_o,key=itemgetter(1))
    array_o = sorted(array_o,key=itemgetter(0))  # sort first by time in ticks then by precedence in order: note_off, tempo, note_on


    for msg in array_o:
        # Calculate accumulated total
        ticks_since_last_msg = msg[0] - o_ticks_accum
        # Add to accumulated total ticks
        o_ticks_prev = o_ticks_accum    # in case we need to undo
        o_ticks_accum = msg[0]
        if msg[1] == 0: # note_off message
            step = msg[3]
            if pattern_KICK[step] and pattern_SNARE[step]:  # True if kick and snare at step
                track_o.append(Message('note_off', time=ticks_since_last_msg, note=kick, velocity=127))
                track_o.append(Message('note_off', time=0, note=snare, velocity=127))
            elif pattern_KICK[step]:   # True if just kick at step
                track_o.append(Message('note_off', time=ticks_since_last_msg, note=kick, velocity=127))
            elif pattern_SNARE[step]: # True if just snare at step
                track_o.append(Message('note_off', time=ticks_since_last_msg, note=snare, velocity=127))
            else: # otherwise, subtract from cumulative total
                o_ticks_accum = o_ticks_prev
        elif msg[1] == 2:   # note_on message
            step = msg[3]
            if pattern_KICK[step] and pattern_SNARE[step]:  # True if kick and snare at step
                track_o.append(Message('note_on', time=ticks_since_last_msg, note=kick, velocity=127))
                track_o.append(Message('note_on', time=0, note=snare, velocity=127))
            elif pattern_KICK[step]:   # True if just kick at step
                track_o.append(Message('note_on', time=ticks_since_last_msg, note=kick, velocity=127))
            elif pattern_SNARE[step]: # True if just snare at step
                track_o.append(Message('note_on', time=ticks_since_last_msg, note=snare, velocity=127))
            else: # otherwise, subtract from cumulative total
                o_ticks_accum = o_ticks_prev
        else: # tempo message
            tempo = msg[3]
            track_o.append(MetaMessage('set_tempo', tempo=tempo, time=ticks_since_last_msg))

    if seperateFiles:
        return onsets, p_beats
    else:
        return midi

def stepShouldPlay(stepProbability):
    '''
    Returns true if a random number is less than or equal to the step probability

    Copied from a MainStage/Logic scripter script.

    Parameters
    ----------
    stepProbability: a probability in range 0-1
    '''

    randomNumber = random.random()

    if(randomNumber <= stepProbability):
       return True
    else:
       return False


def midiTrack2OnsetTimes(midi_track, ticks_per_beat=480, tempo=500000):
    '''
    Returns a list of onset times in seconds for the given midi track

    Onset times are the temporal locations of the beginning of a note (i.e. midi note on messages)
    '''

    times = []
    ticks_since_start = 0

    for msg in midi_track:
        if not msg.type=='channel_prefix' and msg.time != 0:
            ticks_since_start = ticks_since_start + msg.time # time since start in ticks
        
        if msg.type=='set_tempo':
            tempo = msg.tempo
        elif msg.type=='note_on' and msg.velocity != 0:
            time_in_seconds = tick2second(ticks_since_start, ticks_per_beat, tempo)
            times.append(time_in_seconds)

    return times

def pbeFromOnsets(onsets_track, ticks_per_beat=480, BP_window=4, Nb=4, beat_div=2, delta_latency=0.025):
    '''
    Iterates through each message in the midi track 'onsets_track' and sends eacb onset (note_on message) to a PBE object.

    Returns
    -------
    A PBE object, after the onsets have been recorded.
    '''

    pbe = PerceptualBeatEstimator(BP_window=BP_window, Nb=Nb, beat_div=beat_div)

    tempo = 500000
    ticks_since_start = 0
    for msg in onsets_track:
        if not msg.is_meta and msg.time != 0:
            ticks_since_start = ticks_since_start + msg.time
            
        if msg.type=='note_on' and msg.velocity != 0:   # velocity of 0 indicates a note_off
            time_in_seconds = tick2second(ticks_since_start, ticks_per_beat, tempo)
            time_in_seconds = time_in_seconds - delta_latency
            pbe.onset(time_in_seconds, note=msg.note)

        elif msg.type=='set_tempo':
            tempo = msg.tempo
    
    return pbe

def times2tempos(times, bpm=True, window=1):
    '''
    Returns a set of plottable points (t,tempo) of the tempo (in bpm or bps) between two beats.
    The tempo is constant between two beats, and is thus represented by a horizontal line between the times of two beats.

    Parameters
    ----------
    times: list
        a list of beat times, at least 2.
    bpm: Boolean
        if True, tempos returned in bpm, otherwise returned in bps.

    Returns
    -------
    ([list of times], [list of tempos])
    '''
    f = 60 if bpm else 1    # scaling factor for case of bpm/bps.

    arr_time=[]
    arr_tempo=[]

    if window==-1:
        for i in range(len(times)):
            if i != 0:
                time.append(times[i])
                tempo.append(f/(times[i]-times[i-1]))
            if i != len(times)-1:
                time.append(times[i])
                tempo.append(f/(times[i+1]-times[i]))
    else:
        i = 0
        while i < len(times)-1:
            if i+window < len(times):
                tempo = f*window/(times[i+window] - times[i])
                arr_time.extend([times[i], times[i+window]])
                arr_tempo.extend([tempo, tempo])
                i = i + window
            else:
                tempo = f*window/(times[-1] - times[max(0,len(times)-1-window)])
                arr_time.extend([times[i],times[-1]])
                arr_tempo.extend([tempo,tempo])
                i = len(times) - 1
        
    return arr_time, arr_tempo
    