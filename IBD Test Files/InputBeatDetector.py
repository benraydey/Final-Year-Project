#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 18 11:31:07 2020

@author: benadey
"""

import numpy as np
from math import ceil

class InputBeatDetector:
    
    def __init__(self, Nb=4, beat_div=2, BP_window=5):
        '''
        Create new InputBeatDetector.
        Either initialise with default parameters or set your own.
        '''
        self.Nb = Nb
        self.beat_div=beat_div
        
        # IBD parameters
        self.BP_window = BP_window      # onsets within last [BP_window] beats considered.
        self.t_ons = []
        self.BP_ons = []
        self.n = 0   # number of onsets received.
        self.tempo = []   # tempo (in bps) estimations
        self.BP_0 = []      # BP intercept estimations
        self.BP_next_beat = []      # predicted BP of next beat made at each onset
        self.t_next_beat = []       # predicted times of next beat made at each onset
        self.BP_BBP1 = 1
        self.W = []
        
        self.kick_weight = 3
        self.snare_weight = 0.5
        
    def onset(self, tOns, note=36):
        '''
        For an onset at tOns, estimate the perceptual beat.

        Parameters
        ----------
        tOns : float
            CPU time of onset (latency corrected).
        note: int. MIDI note number of onset.

        Returns
        -------
        None.

        '''
        
        
        if self.n == 0:   # True if first onset
            # onset is first onset.
            # add first point
            self.t_ons.append(tOns)
            self.BP_ons.append(1)   # we assume first onset is at BP = 1
            self.BP_BBP1 = 1
            
            tempo_new = -1
            BP_0_new = self.BP_ons[-1]
            
            # Decide on weighting
            self.W.append(1)

        else:       # True if second onset or later
            if self.n == 1:
                # onset is second onset
                # therefore, we assume it is at BP 2
                self.t_ons.append(tOns)
                self.BP_ons.append(2)
                acc = 1
            else:
                # onset is third or later
                # therefore, quantise based on new BP estimate
                self.t_ons.append(tOns)
                BP_ons, acc = self.__beatPositionQuantised(tOns)
                self.BP_ons.append(BP_ons)
            
            # Decide on weighting
            self.W.append(self.__weighting(note,acc))
            
            # Plot a line of best fit through onsets within window
            tempo_new, BP_0_new = self.__lineOfBestFit()
            
            self.tempo.append(tempo_new)
            self.BP_0.append(BP_0_new)
        
        # Add the new perceptual beat estimate and record the predictions of the beat made at this moment
        self.tempo.append(tempo_new)
        self.BP_0.append(BP_0_new)
        self.t_next_beat.append(self.getTimeOfNextBeat())
        self.BP_next_beat.append(self.getBeatPositionOfNextBeat())

        
        
        
        self.n = self.n + 1     # increment number of onsets recorded
    
    def __weighting(self, note, accuracy):
        '''
        Returns weighting parameter given note type (kick or snare) and Bar Beat Position
        '''
        w = accuracy
        
        bsbp = self.getBarSubBeatPositionofLastOnset()
        #print(bsbp)
        # if on the beat, weight higher
        if self.Nb == 4:
            if bsbp in [1,5,9,13]:
                w = w*2
            elif bsbp in [3,7,11,15]:
                w = w*0.8
            else:
                w = 0.1
        elif self.Nb == 3:
            if bsbp in [1,4,7,10]:
                w = w*2.5
            else:
                w = w*0.5
        elif self.Nb == 2:
            if bsbp in [1,3,5,7]:
                w = w*2
            else:
                pass

        
        if note==36:    # kick
            w = w*self.kick_weight
        else:
            w = w*self.snare_weight
            
        return w
        
        
        
    
    def __lineOfBestFit(self):
        '''
        Returns values of m and b for the equation of a line of best fit
        through the onsets
        '''
        # 1. make a list containing all onsets within evaluation window
        i_window = 0
        BP_current = self.BP_ons[-1]
        for i in range(self.n-1, -1, -1):
            if BP_current-self.BP_ons[i] > self.BP_window:
                i_window = i
                break # onset is outside of window. 
        x = np.array(self.t_ons[i_window:])
        y = np.array(self.BP_ons[i_window:])
        w = np.array(self.W[i_window:])

        # check if list has only one value
        if len(x) == 1:
            # list is empty indicating no onsets within window
            # this could happen if input (e.g drummer) hasn't played in
            # a while. Therefore, we change the BP but not the tempo
            tempo_new = self.tempo[-1]  # keep tempo the same
            BP_0_new = self.BP_ons[-1] - tempo_new*self.t_ons[-1]
        else:
            # Calculate line of best fit, changing tempo and BP
            
            # set weights
            #w = np.ones(len(x)) # TODO: improve weighting function if necessary
            
            n=sum(w)

            sum_x = sum(w*x)
            sum_x_2 = sum(w*x**2)
            sum_y = sum(w*y)
            sum_xy = sum(w*x*y)

            # n = len(x)
            # sum_x = np.sum(x)
            # sum_x_2 = np.sum(x**2)
            # sum_y = np.sum(y)
            # sum_xy = np.sum(x*y)
            
            tempo_new = (n*sum_xy-sum_x*sum_y)/(n*sum_x_2-sum_x**2)
            BP_0_new = (sum_y - tempo_new*sum_x)/n
        
        # return new tempo and BP estimate
        return tempo_new, BP_0_new
        
    
    def __beatPositionQuantised(self, tOns):
        '''
        Returns the quantised beat position at tOns given
        the IBD's new estimate of perceptual beat.
        
        Also returns accuracy as a percentage
        '''
        
        # Calculate the BP at tOns - given IBD's estimate
        BP_ons_est = self.tempo[-1]*tOns + self.BP_0[-1]
        
        # Calculate the BP of the nearest sub beat
        BP_ons_Q = round((BP_ons_est-int(BP_ons_est))*self.beat_div)*1/self.beat_div + int(BP_ons_est) 
        
        # Calculate accuracy
        acc = 1 - 2*self.beat_div*abs(BP_ons_est-BP_ons_Q)*0.5
        
        # return quantised beat position
        return BP_ons_Q, acc
    
    def __barBeatPosition(self, BP):
        '''
        Returns the BBP at the given BP
        '''
        BBP = ((BP-self.BP_BBP1)%self.Nb) + 1

        return BBP

    def getBeatPositionFunction(self):
        '''
        Returns the variables tempo and BP_p0, representing the
        BPE's current estimate of perceptual Beat Position
        
        Returns
        -------
        tempo, BP_p0
        '''
        if self.n == 0: # return -1 if no estimate of perceptual BP yet.
            return -1, -1
        return self.tempo[-1], self.BP_0[-1]

    
    def getBeatPosition(self, t):
        '''
        Returns an estimate of perceptual beat position at input time t.
        '''
        return self.tempo[-1]*t + self.BP_0[-1]
    
    def getBarSubBeatPositionofLastOnset(self):
        return self.beat_div*(self.getBarBeatPositionOfLastOnset()-1)+1
        
    
    def getBarBeatPosition(self, t):
        '''
        Returns an estimate of perceptual bar beat position at time t
        '''
        if self.n == 0: # return -1 if no estimate of perceptual BP yet.
            return -1
        # 1. Find the perceptual BP at time t
        BP = self.getBeatPosition(t)
        # 2. Calculate the perceptual BBP at time t
        BBP = ((BP-self.BP_BBP1)%self.Nb) + 1
        
        return BBP
    
    def getBarBeatPositionOfLastOnset(self):
        '''
        Returns bar beat position of most recent onset
        '''

        BBP = ((self.BP_ons[-1]-self.BP_BBP1)%self.Nb) + 1
        #print(f'BBP={BBP}')
        return BBP

    def getTime(self, BP):
        '''
        Returns an estimate of the time at the input beat position BP.
        '''
        if self.n == 0: # return -1 if no estimate of perceptual BP yet.
            return -1
        return 1/self.tempo[-1]*(BP - self.BP_0[-1])

    
    def getBeatPositionOfNextBeat(self):
        '''
        Returns BP of next estimated perceptual beat.
        Next beat occurs after the last recorded onset.
        '''
        if self.n == 0: # return -1 if no estimate of perceptual BP yet.
            return -1

        if int(self.BP_ons[-1]) == self.BP_ons[-1]:
            BP_next = int(self.BP_ons[-1] + 1)
        else:
            BP_next = int(ceil(self.BP_ons[-1]))
        
        return BP_next

    def getBarBeatPositionOfNextBeat(self):
        '''
        Returns BBP of next estimated perceptual beat.
        Next perceptual beat occurs after the last recorded onset
        '''
        if self.n == 0: # return -1 if no estimate of perceptual BP yet.
            return -1
        
        return self.__barBeatPosition(self.getBeatPositionOfNextBeat())

    def getTimeOfNextBeat(self):
        '''
        Returns time of next estimated perceptual beat.
        Next beat occurs after the last recorded onset
        '''
        if self.n == 0: # return -1 if no estimate of perceptual BP yet.
            return -1

        if int(self.BP_ons[-1]) == self.BP_ons[-1]:
            # last onset was on the beat
            # return time of next perceptual beat
            return 1/self.tempo[-1]*((self.BP_ons[-1]+1) - self.BP_0[-1])
        else:
            # last onset was between beats
            # return time of next perceptual beat
            return 1/self.tempo[-1]*(ceil((self.BP_ons[-1])) - self.BP_0[-1])
    
    def getBeatPositionOfLastOnset(self):
        if self.n == 0: # return -1 if no estimate of perceptual BP yet.
            return -1
        return self.BP_ons[-1]
    


    def getWindowWidth(self):
        '''
        Returns window width in beats
        '''
        return self.BP_window
    
    def getTempo(self):
        '''
        Returns the current estimated tempo in beats per second
        '''

        if self.n == 0: # return -1 if no estimate of perceptual BP yet.
            return -1
        return self.tempo[-1]
        

    def reset(self):
        '''
        Resets all IBD parameters
        '''
        self.t_ons = []
        self.BP_ons = []
        self.n = 0   # count of number of onsets recorded.
        self.tempo = []   # tempo (in bps) estimations
        self.BP_0 = []      # BP intercept estimations
        self.BP_next_beat = []      # predicted BP of next beat made at each onset
        self.t_next_beat = []       # predicted times of next beat made at each onset
        self.BP_BBP1 = 1
        

    def getOnsets(self):
        '''
        Returns arrays of onset time and onset beat position

        Returns
        -------
        t_ons[], BP_ons[]
        '''
        return self.t_ons, self.BP_ons
    
    def getEstimates(self):
        '''
        Returns arrays of tempo and beat position intercept containing the perceptual beat estimate
        made upon reception of each onset

        Returns
        -------
        tempo[], BP_0[]
        '''
        return self.tempo, self.BP_0
    
    def getPredictions(self):
        '''
        Returns arrays of [predicted time of next beat] and [predicted BP of next beat]
        made at each onset.
        
        Returns
        -------
        t_next_beat[], BP_next_beat[]
        '''
        return self.t_next_beat, self.BP_next_beat