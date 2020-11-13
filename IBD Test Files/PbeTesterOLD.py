from midi_utils import midi2string, tick2second
from PerceptualBeatEstimator import PerceptualBeatEstimator
from mido import MidiFile
import numpy as np


class PbeTester:
    '''
    A PbeTester object iterates over each message in a given midi track and calculates useful information about the PBE's performance
    '''

    def __init__(self, track, ticks_per_beat=480, BP_window=4, delta_latency=0):
        '''
        Creates a new PerceptualBeatEstimator object with the given parameters
        and iterates over all the messages in the given track.
        '''

        # 1. Extract info about the performance stored in the track name
        trackInfo = (track.name).split(',')
        patternName = trackInfo[0]
        Nb = int(trackInfo[1][trackInfo[1].index('=')+1:])
        beat_div = int(trackInfo[2][trackInfo[2].index('=')+1:])

        s = f'Track: name={patternName}, Nb={Nb}, beat_div={beat_div}\n'
        s = s + '------------------------------------------------------------------\n\n'

        # 2. Create new PBE object, initialising with given parameters
        pbe = PerceptualBeatEstimator(Nb=Nb, beat_div=beat_div, BP_window=BP_window)

        # 3. Iterate over each message in midi track
        num_tests = 0  # counts the number of tests within this file
        self.arr_errors = []  # list of lists of prediction time errors
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
                    self.arr_errors.append(errors)

                    # Calculate error stats and append to string output
                    s = s + f'\t  * highest error: {errors[np.argmax(np.abs(np.array(errors)))]*1000:<5.4} ms @ t={t_ons[np.argmax(np.abs(np.array(errors)))]:<7.4} s\n'
                    s = s + f'\t  * standard deviation of errors: {np.std(errors)*1000:<5.4} ms\n'
                    s = s + f'\t  * abs. mean: {np.mean(np.abs(np.array(errors)))*1000:<5.4} ms\n'
                    s = s + '\n'
                        
                elif msg.note==56:      # => perceptual beat note number
                    pb_times.append(tick2second(time_since_start, ticks_per_beat, tempo))

                else:   # => onset
                    
                    time_in_seconds = tick2second(time_since_start, ticks_per_beat, tempo)
                    time_in_seconds = time_in_seconds - delta_latency
                    pbe.onset(time_in_seconds, note=msg.note)

            elif msg.type=='set_tempo':
                tempo = msg.tempo
        
        # store track info
        self.str_error_info = s
    
    def getErrors(self):
        '''
        Returns a list of lists of prediction time errors for each onset in each recording for the given track
        '''

        return self.arr_errors
    
    def getErrorsOfRecording(self, recording_num):
        '''
        Return a list of prediction time errors for each onset in the recording specified by [recording_num]

        Parameters
        ----------
        recording_num: int. 0 or higher.
        '''

        return self.arr_errors[recording_num]
    
    def getTestInfo(self):
        '''
        Returns a string containing information about the PBE's performance for each test recording.

        String includes formatted headings.
        '''

        return self.str_error_info