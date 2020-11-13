#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 18 22:53:58 2020

@author: benadey
"""
from PerceptualBeatEstimator import PerceptualBeatEstimator
from midi_utils import midi2times
from mido import MidiFile
from statistics import mean
import matplotlib.pyplot as plt
import numpy as np
from timeit import default_timer as timer # for calculating exec time
from matplotlib import style
style.use('ggplot')

# import onset and perceptual beat midi files
onsets_midi = MidiFile('test_sets/Relentless/t_ons.mid')
t_p_midi = MidiFile('test_sets/Relentless/t_p.mid')

# convert midi files to lists of times
t_ons = midi2times(onsets_midi)
t_p = np.array(midi2times(t_p_midi))

# create list of beat positions
bp_p = np.arange(1, len(t_p)+1, 1)


plt.figure()
n = len(t_p)
plt.plot(t_p[1:n-1], t_p[1:n-1]-t_p[0:n-2])
plt.title('Beat Intervals vs. Time')
plt.xlabel('Time [s]')
plt.ylabel('Beat Intervals')

plt.figure()
beat_int = t_p[1:n-1]-t_p[0:n-2]
fft = np.fft.fft(beat_int-np.mean(beat_int))
plt.plot(abs(fft))
plt.title('FFT')

plt.figure()
plt.plot(t_p[1:n-1]-t_p[0:n-2])

# Plot
plt.figure()
plt.plot(t_p, bp_p, '.', label='Perceptual Beats')

#plt.plot(bp_p[1:n-1], t_p[1:n-1]-t_p[0:n-2])
#plt.plot(t_ons, bp_p, 'o', color='blue', label='Onsets')
plt.title('Beat Position versus Onset Time')
plt.xlabel('t [s]')
plt.ylabel(r'$\theta_ p(t)$ [beats]')
plt.legend(loc=4)
plt.show()

#-----------------------------------------------------------------------
pbe = PerceptualBeatEstimator()
BP_ons = []
errors = []
t_start = timer()
for i in range(len(t_ons)):
    pbe.onset(t_ons[i])
    BP_ons.append(pbe.getBeatPositionOfLastOnset())
    
    if i == 0:
        errors.append(0)
    else:
        bp_next = pbe.getBeatPositionOfNextBeat()
        if bp_next <= len(t_p):
            t_next = pbe.getTimeOfNextBeat()
            errors.append(t_next - t_p[bp_next-1])
        else:
            errors.append(0)
t_exec = timer() - t_start


s_errors = ''
for i in range(len(errors)):
    s_errors = s_errors + f"{i}. {errors[i]*1000:>7.2f} ms @ t = {t_ons[i]:<7.4} s\n"

with open('errors.txt', 'w') as text:
    text.write(s_errors)

# plot histogram of errors
plt.figure()
num_bins = 5
n, bins, patches = plt.hist(x=np.array(errors)*1000, bins='auto', facecolor='blue', color='#0504aa', alpha=0.5)
plt.grid(axis='y', alpha=0.75)
plt.xlabel('error [ms]')
plt.ylabel('frequency')
plt.title('Perceptual beat estimator prediction error histogram')
maxfreq = n.max()
# Set a clean upper y-axis limit.
plt.ylim(ymax=np.ceil(maxfreq / 10) * 10 if maxfreq % 10 else maxfreq + 10)
plt.show()

# print error stats
print('\n Execution time:')
print(f'  * Total exec time: {t_exec*1000:<7.4} ms')
print(f'  * average exec time per onset: {t_exec/len(t_ons)*1000000:<7.4} \u03bcs')
print(f'\nError in predictions:')
print(f'  * highest error: {errors[np.argmax(np.abs(np.array(errors)))]*1000:<5.4} ms @ t={t_ons[np.argmax(np.abs(np.array(errors)))]:<7.4} s')
print(f'  * standard deviation: {np.std(errors)*1000:<5.4} ms')
print(f'  * abs. mean: {np.mean(np.abs(np.array(errors)))*1000:<5.4} ms')

# BP_ons = []
# for i in range(len(t_ons)):
#     input("Press enter for next onset: ")
#     pbe.onset(t_ons[i])
#     BP_ons.append(pbe.getBeatPositionOfLastOnset())
    
#     # plot onsets received so far and line of best fit through them
#     plt.figure()
#     plt.title('Beat Position versus Onset Time')
#     plt.xlabel('t [s]')
#     plt.ylabel(r'$\theta_p(t)$ [beats]')
    
#     plt.scatter(t_ons[0:i+1], BP_ons, color='tab:blue', label='onsets')
    
    
    
#     if i == 0: # first onset
#         #plt.plot(t_ons[i], pbe.getBeatPositionOfLastOnset(), color='blue')
#         plt.legend(loc=4)
#         plt.show()
#         print(f"({t_ons[i]:<.5f} s, {pbe.getBeatPositionOfLastOnset():<.2f} beats)")
#         continue
#     else:
#         #plt.plot(t_ons[i], pbe.getBeatPositionOfLastOnset(), color='blue')
        
        
#         t_next = pbe.getTimeOfNextBeat()
#         bp_next = pbe.getBeatPositionOfNextBeat()
        
#         # prediction
#         m, b = pbe.getBeatPositionFunction()
#         x_p = np.array([pbe.getTime(BP_ons[-1] - pbe.getWindowWidth())-1, pbe.getTimeOfNextBeat()+0.5])
        
#         plt.axvline(x=(pbe.getTime(BP_ons[-1] - pbe.getWindowWidth())), color='tab:green', linestyle='--', label='window')
#         plt.axvline(x=t_ons[i], color='tab:green', linestyle='--')
#         plt.plot(x_p, m*x_p+b, color='tab:green')
#         #plt.scatter(pbe.getTimeOfNextBeat(), m*pbe.getTimeOfNextBeat()+b, color='tab:purple')
#         plt.axvline(x=pbe.getTimeOfNextBeat(), color='tab:purple', label='Predicted time of next beat')
        
#         if bp_next <= len(t_p):
#             plt.axvline(x=t_p[bp_next-1], color='tab:red', label='Actual time of next beat')
#             error = t_next - t_p[bp_next-1]
#             plt.legend(loc=4)
#             plt.show()
#             print(f"({t_ons[i]:<.5f} s, {pbe.getBeatPositionOfLastOnset():<.2f} beats)")
#             print(f"  Time of next perceptual beat={t_next:<.4f} s")
#             print(f"  Error={error*1000:<.2f} ms")
            
#         else:
#             plt.legend(loc=4)
#             plt.show()
#             print(f"({t_ons[i]:<.5f} s, {pbe.getBeatPositionOfLastOnset():<.2f} beats)")
