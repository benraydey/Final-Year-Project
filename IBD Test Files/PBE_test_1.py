from midi_utils import midi2string, tick2second
from PerceptualBeatEstimator import PerceptualBeatEstimator
from mido import MidiFile
import os
import numpy as np
import matplotlib.pyplot as plt

# midi = MidiFile('test_sets/set_1/pattern_1.mid')

# with open('test_sets/set_1/pattern_1_midi.txt', "w") as text:
#     text.write(midi2string(midi))

test_dir = 'test_sets/set_1/'


# loop through all midi files in the test set folder
for file in os.listdir(os.fsencode(test_dir)):
    filename = os.fsdecode(file)
    if filename.endswith('.mid'):
        test = MidiFile(test_dir + filename)
            # Uncomment code below to print every MIDI message to a text file of same name as midi file
            # - useful for debugging
        # with open(test_dir + filename[:filename.index('.')] + '.txt', "w") as text:
        #     text.write(midi2string(test))
        for i, track in enumerate(test.tracks):  # loop through each track in the midi file

            # 1. Extract info about the performance stored in the track name
            trackInfo = (track.name).split(',')
            patternName = trackInfo[0]
            Nb = int(trackInfo[1][trackInfo[1].index('=')+1:])
            beat_div = int(trackInfo[2][trackInfo[2].index('=')+1:])

            s = f'Track {i}: name={patternName}, Nb={Nb}, beat_div={beat_div}\n'
            s = s + '------------------------------------------------------------------\n\n'

            # TODO: create a new PbeTester object

            # 2. Create new PBE object, initialising with Nb and beat_div
            pbe = PerceptualBeatEstimator(Nb=Nb, beat_div=beat_div)

            # 3. Iterate over messages
            num_tests = 0  # counts the number of tests within this file
            arr_errors = []  # list of lists of prediction time errors
            for msg in track:
                if not msg.is_meta and msg.time != 0:
                    time_since_start = time_since_start + msg.time
                    
                if msg.type=='note_on' and msg.velocity != 0:   # velocity of 0 indicates a note_off
                    
                    if msg.note == 54:      # => new recording
                        # create test recording heading
                        s = s + f'\tTest {num_tests+1}\n\t--------\n'
                        num_tests = num_tests + 1
                        # reset all algorithm variables
                        pb_times = (np.zeros(Nb+1)).tolist()  # stores the times of each perceptual beat
                        time_since_start = 0    # time since start in ticks

                        # reset the PBE
                        pbe.reset()

                    elif msg.note == 53:    # => end of recording  -> determine the accuracy of the PBE
                        # get onset times and predictions made
                        t_ons, BP_ons = pbe.getOnsets()
                        t_next_beat, bp_next_beat = pbe.getPredictions()

                        # setup variables needed for error calculation
                        errors = []     # stores errors in seconds between predicted perceptual beat time and recorded pb time.

                        for j in range(1, len(t_ons)):  # loop through recorded onsets. skip the first onset
                            predicted_time = pb_times[bp_next_beat[j]]
                            # the first perceptual beat occurs adter the synchronising beats
                                # E.g. in the case of 4/4, first pb and therefore first comparision is at BP=5.
                            if predicted_time:    # True if a perceptual beat was recorded at BP = bp_next_beat[j] -> False if 0
                                errors.append(t_next_beat[j] - predicted_time)
                                #s = s + f'error = {errors[-1]*1000:<5.2f} ms\n'

                        arr_errors.append(errors)
                        # TODO: calculate stats and append to text file output
                        s = s + f'\t  * highest error: {errors[np.argmax(np.abs(np.array(errors)))]*1000:<5.4} ms @ t={t_ons[np.argmax(np.abs(np.array(errors)))]:<7.4} s\n'
                        s = s + f'\t  * standard deviation of errors: {np.std(errors)*1000:<5.4} ms\n'
                        s = s + f'\t  * abs. mean: {np.mean(np.abs(np.array(errors)))*1000:<5.4} ms\n'
                        s = s + '\n'
                        # TODO: save this histogram to a file or open in IPython
                        # n, bins, patches = plt.hist(x=np.array(errors)*1000, bins='auto', facecolor='blue', color='#0504aa', alpha=0.5)
                        # plt.grid(axis='y', alpha=0.75)
                        # plt.xlabel('error [ms]')
                        # plt.ylabel('frequency')
                        # plt.title('Perceptual beat estimator prediction error histogram')
                        # maxfreq = n.max()
                        # # Set a clean upper y-axis limit.
                        # plt.ylim(ymax=np.ceil(maxfreq / 10) * 10 if maxfreq % 10 else maxfreq + 10)
                        # plt.show()

                            
                    elif msg.note==56:      # => perceptual beat note number
                        pb_times.append(tick2second(time_since_start, test.ticks_per_beat, tempo))

                    else:
                        time_in_seconds = tick2second(time_since_start, test.ticks_per_beat, tempo)
                        # TODO: correct for latency
                        pbe.onset(time_in_seconds, note=msg.note)

                        #s = s + f'bar position of next beat = {bp_next_beat[-1]} time = {t_next_beat[-1]}\n'
                        #s = s + f'time: {time_in_seconds:<5.3f}s   note = {msg.note}   BBP: {pbe.getBarBeatPositionOfLastOnset()}  tempo = {pbe.getTempo()*60:<5.2f} bpm \n'
                elif msg.type=='set_tempo':
                    tempo = msg.tempo


            # Finally, write the output containing useful stats to a text file           
            with open(test_dir + filename[:filename.index('.')] + '_track_' + str(i) + '.txt', "w") as text:
                text.write(s)