#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 18 12:59:30 2020

@author: benadey
"""
from PerceptualBeatEstimator import PerceptualBeatEstimator
from midi_utils import midi2times
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import style
style.use('ggplot')


#-----------------------------------------------------------------------
#                       Generate onsets with BP noise
#-----------------------------------------------------------------------

# song parameters
tempo_bpm = 120
tempo_bps = tempo_bpm/60    # tempo in beats/second.
t_start = 0         # time of first beat

# set perceptual beat positions and times
bp_p = np.arange(1, 30, 1)
t_p = (1/(tempo_bps))*(bp_p - bp_p[0])

# Beat position noise parameters
sigma_noise = (0.2)**2   # variance of noise
mu_noise = 0        # mean of noise

# Add BP noise
noise = sigma_noise*np.random.randn(len(bp_p)) + mu_noise
t_ons = (1/(tempo_bps))*(bp_p - bp_p[0]) + t_start + noise

# Plot
plt.figure()
plt.scatter(t_p, bp_p, label='Perceptual Beats')
plt.plot(t_ons, bp_p, 'o', color='blue', label='Onsets')
plt.title('Beat Position versus Onset Time')
plt.xlabel('t [s]')
plt.ylabel(r'$\theta_p(t)$ [beats]')
plt.legend(loc=4)
plt.show()

#-----------------------------------------------------------------------
pbe = PerceptualBeatEstimator()

BP_ons = []
for i in range(len(t_ons)):
    input("Press enter for next onset: ")
    pbe.onset(t_ons[i])
    BP_ons.append(pbe.getBeatPositionOfLastOnset())
    
    # plot onsets received so far and line of best fit through them
    plt.figure()
    plt.title('Beat Position versus Onset Time')
    plt.xlabel('t [s]')
    plt.ylabel(r'$\theta_p(t)$ [beats]')
    
    plt.scatter(t_ons[0:i+1], BP_ons, color='tab:blue', label='onsets')
    
    
    
    if i == 0: # first onset
        #plt.plot(t_ons[i], pbe.getBeatPositionOfLastOnset(), color='blue')
        plt.legend(loc=4)
        plt.show()
        print(f"({t_ons[i]:<.5f} s, {pbe.getBeatPositionOfLastOnset():<.2f} beats)")
        continue
    else:
        #plt.plot(t_ons[i], pbe.getBeatPositionOfLastOnset(), color='blue')
        
        
        t_next = pbe.getTimeOfNextBeat()
        bp_next = pbe.getBeatPositionOfNextBeat()
        
        # prediction
        m, b = pbe.getBeatPositionFunction()
        x_p = np.array([pbe.getTime(BP_ons[-1] - pbe.getWindowWidth())-1, pbe.getTimeOfNextBeat()+0.5])
        
        plt.axvline(x=(pbe.getTime(BP_ons[-1] - pbe.getWindowWidth())), color='tab:green', linestyle='--', label='window')
        plt.axvline(x=t_ons[i], color='tab:green', linestyle='--')
        plt.plot(x_p, m*x_p+b, color='tab:green')
        #plt.scatter(pbe.getTimeOfNextBeat(), m*pbe.getTimeOfNextBeat()+b, color='tab:purple')
        plt.axvline(x=pbe.getTimeOfNextBeat(), color='tab:purple', label='Predicted time of next beat')
        
        if bp_next <= len(t_p):
            plt.axvline(x=t_p[bp_next-1], color='tab:red', label='Actual time of next beat')
            error = t_next - t_p[bp_next-1]
            plt.legend(loc=4)
            plt.show()
            print(f"({t_ons[i]:<.5f} s, {pbe.getBeatPositionOfLastOnset():<.2f} beats)")
            print(f"  Time of next perceptual beat={t_next:<.4f} s")
            print(f"  Error={error*1000:<.2f} ms")
            
        else:
            plt.legend(loc=4)
            plt.show()
            print(f"({t_ons[i]:<.5f} s, {pbe.getBeatPositionOfLastOnset():<.2f} beats)")
           
    
    
    
    
    
        
        
