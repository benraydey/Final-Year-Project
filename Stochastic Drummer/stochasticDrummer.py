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