'''
Beat Sync Transport

@author: Ben Adey
@year: 2020
'''

from MachineBeatDetector import MachineBeatDetector
from InputBeatDetector import InputBeatDetector
from Controller import Controller
from timeit import default_timer as timer
import time # used for sleep
import mido
from midi_utils import midiTrack2OnsetTimes
from mido import MidiFile
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# Change matplotlib font to latex font
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": ["Computer Modern Roman"],
})
#plt.ioff()


# 1. User Parameters
Nb = 4
beat_div = 2
T_tempo = 0.3

# 2. Create Objects
IBD = InputBeatDetector(Nb=Nb, beat_div=beat_div)
MBD = MachineBeatDetector(Nb=Nb)
controller = Controller(Nb=Nb)

# 3. Setup MIDI ports
#controller_out = mido.open_output('IAC Driver Bus 2')#mido.open_output('BeatSync Tempo Out', virtual=True) # tempo and start to MS
controller_out = mido.open_output('BeatSync Control Out', virtual=True) # tempo and start to MS
machine_in = mido.open_input('BeatSync MainStage In', virtual=True) # MS MIDI click and messages in
#input_in = mido.open_input('BeatSync Bonk In', virtual=True) # input onsets
input_in = mido.open_input('IAC Driver Bus 3')
#input_in = mido.open_input('SAMSON Carbon49 ') # input onsets
test_messages_in = mido.open_input('BeatSync Test Messages In', virtual=True) # Messages for test procedure

def changeNbMIDIMessage(Nb):
    '''
    Returns a control change message to change the patch in MainStage to one at the correct time signature
    '''
    resolution = 4  # number of possible Nb values

    cc_value = int(round((Nb-1)*128/resolution + 128/(2*resolution)))
    cc = mido.Message('control_change', control=14, value=cc_value)
    return cc


def changeTempoMIDIMessage(tempo_change:float):
    '''
    Returns a mido.Message object to be sent to MainStage to change
    the tempo to tempo_change.

    Params
    ------
    tempo_change: a tempo in beats per second.
    '''
    tempo = tempo_change*60 # convert tempo to beats per minute
    assert((tempo>=30) and (tempo<=357.66)), "tempo must be in the range 30-300 bpm"
    
    tempo_MIN = 30
    res = 0.02 # resolution
    
    # create a pitchwheel MIDI message to send to MainStage. When MainStage
    # receives this MIDI message, it will change its tempo to the value set here.
    pitch_val = int((tempo - tempo_MIN)/res - 8192)
    pitch_msg = mido.Message('pitchwheel', pitch=pitch_val)

    return pitch_msg


# 4. Initialise algorithm variables
# machine parameters
machine_beat_div = MBD.getBeatDivision() # must match the beat_div set in MainStage
tau_m_delay = 0 # TODO: Calculate this by experimentation
# algorithm state variables
t_tempo_NEXT = timer() + T_tempo
controller_set = False
controller_on = True
tempo_m_NEW = (120)/60
#tempo_m_NEW = -1 # new tempo to be set. -1 if no change should happen.
tempo_new_MIDI_MESSAGE = changeTempoMIDIMessage(tempo_m_NEW)


# send new tempo if available
# if tempo_m_NEW != -1:
#     controller_out.send(tempo_new_MIDI_MESSAGE)
#     MBD.tempoChange(timer(), tempo_m_NEW)

# Define MIDI messages
START = mido.Message('start')
STOP = mido.Message('stop')

# time.sleep(1)   # Necessary for MainStage to pick up MIDI port
# controller_out.send(changeNbMIDIMessage(4))



# 5. Main Loop

    # initial values
controller_on = False

machine_playing=False
start_scheduled = False
t_start = 0

    # onset detector latency correction
delta_latency = 0.03
#tau_c_delay = 0.03
# tau_m_delay = 0 # add to machine onset times
tau_c_exec = 0.01 # controller samples earlier by this amount
tau_c_delay = 0.008
delta_start = 0.09
 

testing_on = True


test_dir = 'test_sets/2/'


# STASTISTICS ARRAYS
beat_division = []
bar_length = []
num_beats = []
mean_tempo = []
error_RMS = []
error_mean = []
error_median = []

onset_error_RMS = []
onset_error_mean = []
onset_error_median = []

controller_error_RMS = []
controller_error_mean = []
controller_error_median = []

t_pb = []
test_num = 0

T_tempo = 0.2

if testing_on:
    Nb = -1
    beat_div = -1


try:
    while True: # loop until interrupted
        
        # 1. Check for input (drummer) onsets
        for ons in input_in.iter_pending ():     # non blocki ng MIDI input
            t = timer()
            if ons.type=='note_on' and ons.velocity>0: # filter out NoteOff messages
                #print(f'onset: {t}')
                IBD.onset(t - t_start - delta_latency, note=ons.note)      # send onset to IBD
                #print(IBD.getBarBeatPositionOfLastOnset()) 
                if not machine_playing:
                    if IBD.getBarBeatPositionOfNextBeat()==1:  # True if next beat is start of bar
                        t_send_start = IBD.getTimeOfNextBeat() # schedule a start time
                        start_scheduled = True
                        tempo_new_MIDI_MESSAGE = changeTempoMIDIMessage(IBD.getTempo()*0.7)
                        controller_out.send(tempo_new_MIDI_MESSAGE)

        # 2. Check for machine onsets
        for ons in machine_in.iter_pending():
            t = timer()
            if ons.type=='note_on':
                # The note value of machine onsets gives the BSBP
                # BSBP 1 is note=60, BSBP 2 is note=61 and so on
                # we convert BSBP into BBP and send to MBD
                MBD.onset(t-t_start+tau_m_delay, ((ons.note-59)-1)/machine_beat_div+1)
            elif ons.type=='stop':
                MBD.reset()
        
        # 3. Initiate controller sampling if controller on
        if controller_on:
            # if (timer()-t_start) > t_tempo_NEXT:
            #     tempo_m_NEW = controller.sample(timer()-t_start, IBD, MBD)
            #     if tempo_m_NEW != -1:
            #         tempo_new_MIDI_MESSAGE = changeTempoMIDIMessage(tempo_m_NEW)
            #         controller_out.send(tempo_new_MIDI_MESSAGE)
            #         MBD.tempoChange(timer()-t_start, tempo_m_NEW)
            #     t_tempo_NEXT = t_tempo_NEXT + T_tempo # set next sample time
            # TODO: calculate tau_m_delay
            # TODO: controller must have large delta_tempo_max if very out of sync
            if controller_set:  # True if controller has already sampled
                if (timer()-t_start) > (t_tempo_NEXT - tau_c_delay):  # True if it is time to send tempo change
                    # first, check that new tempo is not -1 indicating no change
                    if tempo_m_NEW != -1:  # True if tempo change must happen
                        controller_out.send(tempo_new_MIDI_MESSAGE)  # change MS tempo
                        MBD.tempoChange(timer()-t_start, tempo_m_NEW)   # send tempo change to MBD
                    t_tempo_NEXT = t_tempo_NEXT + T_tempo # set next sample time
                    controller_set = False
            elif (timer()-t_start) > (t_tempo_NEXT - tau_c_exec - tau_c_delay):
                # It is time for the controller to sample IBD and MBD
                t0 = timer() - t_start
                tempo_m_NEW = controller.sample(t_tempo_NEXT, IBD, MBD)
                t_c_exec = (timer()-t_start) - t0
                controller_set = True
                if tempo_m_NEW != -1:
                    tempo_new_MIDI_MESSAGE = changeTempoMIDIMessage(tempo_m_NEW)

        # 4. Check if a start is scheduled
        if start_scheduled:
            if (timer()-t_start) > (t_send_start - delta_start):    # True if time to start the bar
                controller_out.send(START)  # send start message
                controller_on = True
                t_tempo_NEXT = timer()-t_start+T_tempo
                machine_playing = True
                start_scheduled = False

        # 5. Check for test messages
        if testing_on:
            for msg in test_messages_in.iter_pending():
                t = timer()
                
                # Logic sends System Exclusive MIDI messages
                # so we want to filter those out
                if msg.type=='note_on' and msg.channel==3 and msg.note==56: # Perceptual Beat Message
                    t_pb.append(t - t_start)
                    #print(f'PB: {t_pb[-1]}')

                
                elif msg.type=='note_on' and msg.channel==1:    # Nb Message
                    Nb = msg.note
                    print(f'Nb = {Nb}')
                
                elif msg.type=='note_on' and msg.channel==2:    # Beat division Message
                    beat_div = msg.note
                    print(f'beat div = {beat_div}')
                
                # TODO: check for a new cycle message (which changes to parameters stored in a text file)
                elif msg.type=='note_on' and msg.channel==0 and msg.note==0:  # True if NEW TEST message
                    print(f'---- New Test ------------------')
                    if Nb==-1:
                        Nb = 4
                        print('  Nb = 4 (default)')
                    if beat_div==-1:
                        beat_div = 2
                        print('  beat_div = 2 (default')
                    # increment test number
                    test_num = test_num + 1

                    t_start = t     # t0 reference time

                    # 2. Send messages to MainStages to setup the test
                    controller_out.send(changeNbMIDIMessage(Nb))    # Change time signature
                    controller_out.send(STOP)  # Stop MainStage (whether playing or not)
                    
                    # 3. Setup system objects for test
                    machine_playing = False
                    start_scheduled = False
                    controller_on = False
                    controller_set = False
                    controller.reset()
                    IBD.reset()
                    MBD.reset()

                    controller = Controller(Nb=Nb)
                    IBD = InputBeatDetector(Nb=Nb, beat_div=beat_div)
                    MBD = MachineBeatDetector(Nb)
                    
                    t_pb = []

                    
                elif msg.type=='note_on' and msg.channel==0 and msg.note==1:  # True if END OF TEST message
                    print('-------------- End of Test ------')
                    # Stop MainStage
                    controller_out.send(STOP)
                    
                    # Reset parameters
                    
                    # Load annotated perceptual beat times (ground truth times)
                    #pb_midi = MidiFile(test_dir+'pb.mid')
                    #pb_track = pb_midi.tracks[test_num]
                    #t_pb = midiTrack2OnsetTimes(pb_track)
                    #t_pb  = t_pb2

                    # 1. WHOLE SYSTEM STATS
                    #    ------------------
                    # 1.1 Get machine beat times from MBD
                    t_mb = MBD.getBeatTimes()
                    # 1.2 Trim t_pb and t_mb to be the same length
                    min_length = min(len(t_pb),len(t_mb))
                    t_mb = np.array(t_mb[0:min_length])
                    t_pb = np.array(t_pb[0:min_length])
                    #print(f't_mb: {t_mb}\nt_pb: {t_pb}')
                    # 1.3 Calculate Errors
                    errors = t_mb-t_pb     # error in seconds
                    # 1.4 Record
                    beat_division.append(beat_div)
                    bar_length.append(Nb)
                    num_beats.append(min_length)
                    mean_tempo.append(60*(len(t_pb)-1)/(t_pb[-1]-t_pb[0]))
                    error_RMS.append(np.sqrt(np.mean((1000*errors)**2)))
                    error_mean.append(1000*np.mean(abs(errors)))
                    error_median.append(1000*np.median(abs(errors)))
                    # 1.5 Plot
                    f1 = plt.figure(figsize=(6.4,2.4))
                    plt.title(f'Track {test_num}: MainStage Beat Time Error vs Beat Position')
                    plt.xlabel(r'Beat Position $\theta_i$ \small{[beats]}')
                    plt.ylabel(r'Error \small{[ms]}')
                    plt.plot(errors*1000, color='midnightblue', linewidth=1)
                    plt.ylim([-100, 100])
                    ax = plt.gca()
                    ax.grid(False)

                    f2 = plt.figure(figsize=(6.4,2.4))
                    plt.title(f'Test {test_num}: MainStage Beat Time Error vs Beat Position')
                    plt.xlabel(r'Beat Position $\theta_i$ \small{[beats]}')
                    plt.ylabel(r'Error \small{[ms]}')
                    plt.plot(errors*1000, color='midnightblue', linewidth=1)
                    ax = plt.gca()
                    yabs_max = abs(max(ax.get_ylim(), key=abs))
                    ax.set_ylim(ymin=-yabs_max, ymax=yabs_max)
                    ax.grid(False)

                        # save figures to pdf
                    f1.savefig(test_dir + f'TRACK_{test_num}__' + "error_v_bp_fixed.pdf", bbox_inches='tight')
                    f2.savefig(test_dir + f'TRACK_{test_num}__' + "error_v_bp.pdf", bbox_inches='tight')
                    plt.close(f1)
                    plt.close(f2)
                    # 1.6 Print array to text file
                    with open(test_dir + f'TRACK_{test_num}__' + 'errors.txt', 'w') as textfile:
                        textfile.write(str(errors))

                    # 2. IBD STATS
                    #    ------------------
                    # 2.1 Get predicted beat times from IBD (made at each onset)
                    t_next_beat, bp_next_beat = IBD.getPredictions()
                    # 2.2 Calculate errors in predictions
                    #print(list(zip(t_next_beat,bp_next_beat)))
                    #print(t_pb)
                    
                    onset_errors = []  # list of error in prediction time at each onset (IN SECONDS)
                    for i in range(0, len(bp_next_beat)):
                        if bp_next_beat[i] <= Nb:
                            continue
                        if bp_next_beat[i] - Nb > len(t_pb):
                            break
                        bp_next = bp_next_beat[i] - Nb
                        error = t_next_beat[i] - t_pb[bp_next-1]
                        #print(error)
                        onset_errors.append(error)
                        
                    # 2.3 Record
                    onset_errors = np.array(onset_errors)
                    onset_error_RMS.append(np.sqrt(np.mean((1000*onset_errors)**2)))
                    onset_error_mean.append(1000*np.mean(abs(onset_errors)))
                    onset_error_median.append(1000*np.median(abs(onset_errors)))

                    # 2.4 Plot
                    f1 = plt.figure(figsize=(6.4,2.4))
                    plt.title(f'Track {test_num}: IBD Predicted Beat Time Error vs Onset Index')
                    plt.xlabel(r'Onset Index')
                    plt.ylabel(r'Error \small{[ms]}')
                    plt.plot(onset_errors*1000, color='darkslategray', linewidth=1)
                    plt.ylim([-100, 100])
                    ax = plt.gca()
                    ax.grid(False)

                    f2 = plt.figure(figsize=(6.4,2.4))
                    plt.title(f'Track {test_num}: IBD Predicted Beat Time Error vs Onset Index')
                    plt.xlabel(r'Onset Index')
                    plt.ylabel(r'Error \small{[ms]}')
                    plt.plot(onset_errors*1000, color='darkslategray', linewidth=1)
                    ax = plt.gca()
                    yabs_max = abs(max(ax.get_ylim(), key=abs))
                    ax.set_ylim(ymin=-yabs_max, ymax=yabs_max)
                    ax.grid(False)
                        # save figures to pdf
                    f1.savefig(test_dir + f'TRACK_{test_num}__' + "IBD_error_fixed.pdf", bbox_inches='tight')
                    f2.savefig(test_dir + f'TRACK_{test_num}__' + "IBD_error.pdf", bbox_inches='tight')
                    plt.close(f1)
                    plt.close(f2)
                    # 2.5 Print array to text file
                    with open(test_dir + f'TRACK_{test_num}__' + 'IBD_errors.txt', 'w') as textfile:
                        textfile.write(str(onset_errors))

                    # 3. CONTROLLER STATS
                    #    ----------------
                    # 3.1 Get list of errors from controller
                    controller_errors = np.array(controller.getErrors())
                    # 3.2 Record
                    controller_error_RMS.append(np.sqrt(np.mean(controller_errors**2)))
                    controller_error_mean.append(np.mean(abs(controller_errors)))
                    controller_error_median.append(np.median(abs(controller_errors)))
                    # 3.3 Plot
                    f1 = plt.figure(figsize=(6.4,2.4))
                    plt.title(f'Track {test_num}: Controller Beat Position Error vs Tempo Change Index')
                    plt.xlabel(r'Tempo Change Index')
                    plt.ylabel(r'Beat Position Error \small{[beats]}')
                    plt.plot(controller_errors, color='purple', linewidth=1)
                    plt.ylim([-3, 3])
                    ax = plt.gca()
                    ax.grid(False)

                    f2 = plt.figure(figsize=(6.4,2.4))
                    plt.title(f'Track {test_num}: Controller Beat Position Error vs Tempo Change Index')
                    plt.xlabel(r'Tempo Change Index')
                    plt.ylabel(r'Beat Position Error \small{[beats]}')
                    plt.plot(controller_errors, color='purple', linewidth=1)
                    ax = plt.gca()
                    yabs_max = abs(max(ax.get_ylim(), key=abs))
                    ax.set_ylim(ymin=-yabs_max, ymax=yabs_max)
                    ax.grid(False)

                        # save figures to pdf
                    f1.savefig(test_dir + f'TRACK_{test_num}__' + "controller_error_fixed.pdf", bbox_inches='tight')
                    f2.savefig(test_dir + f'TRACK_{test_num}__' + "controller_error.pdf", bbox_inches='tight')
                    plt.close(f1)
                    plt.close(f2)
                    # 3.4 Print array to text file
                    with open(test_dir + f'TRACK_{test_num}__' + 'controller_errors.txt', 'w') as textfile:
                        textfile.write(str(controller_errors))

                    
                    Nb = -1
                    beat_div = -1

                elif msg.type=='note_on' and msg.channel==0 and msg.note==2:  # True if END OF TEST message
                    # END OF ALL TESTS
                    print('- - - - - - - END - - - - - - - -')
                    # 1. Save arrays into an excel file
                    df = pd.DataFrame(list(zip(beat_division,bar_length,num_beats,mean_tempo,error_RMS,error_mean,error_median,
                        onset_error_RMS,onset_error_mean,onset_error_median,
                        controller_error_RMS,controller_error_mean,controller_error_median)),
                        columns=['Beat Division','Bar Length [beats]','Test Length [beats]', 'Mean Tempo [bpm]', 'RMS Error [ms]', 'Mean Error [ms]','Median Error [ms]',
                            'IBD RMS Error [ms]','IBD Mean Error [ms]', 'IBD Median Error [ms]',
                            'Controller RMS Error [beats]','Controller Mean Error [ms]','Controller Median Error [ms]'])
                    df.to_excel(test_dir + 'test_results.xlsx', index=False)


except KeyboardInterrupt:
    print("Keyboard Interrupt")
        
finally:
    # # store perceptual beat values
    # t_ons_P, BP_ons_P = IBD.getOnsets()
    # #tempo_P, BP_0_P = IBD.getEstimates()

    # # store machine beat values
    # t_ons_M, BP_ons_M = MBD.getOnsets()
    # #tempo_M, BP_0_M = MBD.getEstimates()
    
    # print(t_ons_P)
    # print(BP_ons_P)
    # print(t_ons_M)
    # print(BP_ons_M)
    
    # #print(f'Perceptual: tempo_p={tempo_P[-1]:4.1f} b/s, BP_0_P={BP_0_P[-1]:4.1f} b')
    # #print(f'Machine: tempo_m={tempo_M[-1]:4.1f} b/s, BP_0_M={BP_0_M[-1]:4.1f} b')
    # close ports
    controller_out.send(STOP)  # Stop MainStage (whether playing or not)
    controller_out.close()
    machine_in.close()
    input_in.close()
    test_messages_in.close()
    print("All ports closed")