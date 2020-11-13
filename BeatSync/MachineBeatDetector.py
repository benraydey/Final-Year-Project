'''
Machine Beat Detector

@author: Ben Adey
@year: 2020
'''

import numpy as np

class MachineBeatDetector:

    def __init__(self, Nb=4, beat_div=2, tempo_init=-1):
        '''
        Create new MachineBeatDetector.
        Either initialise with default parameters or set your own.
        '''
        self.Nb = Nb    # Num beats per bar
        self.beat_div = beat_div # beat division
        self.BP_window = 6      # window width for line of best fit

        self.tempo_INIT = tempo_init # initial tempo
        self.tempo_INIT_ORIGINAL = tempo_init
        self.BP_BBP1 = 1    # Known BP where BBP is 1
        self.n = 0          # number of onsets received
        self.TempoDefinite = False    # True once 1st tempo change is made
        self.knownTempo = -1  # becomes greater than 0 once tempo change is made
        self.i_w_MIN = -1    # index of lower window limit. Set whenever tempo change received.
        self.isAlreadyShifted = False # becomes True when controller initiates shift

        # intialise lists
        self.t_ons = []
        self.BP_ons = []
        self.tempo = []
        self.BP_0 = []
        self.t_beats = []  # list of machine beat times (beats occur when BP is an integer)
        self.tempo_change_indices = []  # array of indices of onsets representing a tempo change

    def onset(self, tOns, BBP_ons):
        if self.n > 0:     # True if 2nd or later onset
            # We assume that there are no missing machine onsets
            # Therefore, this machine onset will have a BP one subbeat
            # higher than the previous machine onset.
            self.BP_ons.append(self.BP_ons[-1]+1/self.beat_div)
            self.t_ons.append(tOns)
            self.n = self.n + 1

            if self.TempoDefinite:
                # Plot line of best fit to calculate the machine beat position
                # - tempo is calculated based on the intervals of the onsets.
                tempo_new, BP_0_new = self.__lineOfBestFit(tempo_calc=False)
            else:   # Machine tempo is definite - True if tempo change has been sent
                # Plot line of best fit - but don't calculate new Tempo
                tempo_new, BP_0_new = self.__lineOfBestFit(tempo_calc=True)
            
            self.tempo.append(tempo_new)
            self.BP_0.append(BP_0_new)

        else: # True if first onset
            # first onset
            self.t_ons.append(tOns)
            self.BP_ons.append(BBP_ons)

            self.tempo.append(self.tempo_INIT)  # Assume tempo is the initial tempo
            self.BP_0.append(BBP_ons - self.tempo_INIT*tOns)

            self.n = self.n + 1   # increment n
        
        # Finally, if onset is an integer, we store it to keep track of machine beat times
        if self.BP_ons[-1] - int(self.BP_ons[-1]) < 0.00001:
            self.t_beats.append(self.t_ons[-1])
    
    def tempoChange(self, t_tempo, tempo_m_new):
        '''
        Make a machine tempo change. This function should be called
        every time a tempo change is sent to MainStage.
        '''

        if self.n == 0: # no onsets have been received yet
            self.tempo_INIT = tempo_m_new
            self.knownTempo = tempo_m_new
            self.TempoDefinite = True

        elif self.n == 1 and not self.TempoDefinite:   # one onset has been received
                                                        # and tempo not known
            # Tempo is not definite and only one onset received.
            # therefore we have no way of knowing the beat position at t_tempo,
            # the time of this tempoChange. Therefore we reset because at the
            #  very next machine onset we will know the beat position and tempo.
            self.__tempoChangeReset()
            self.tempo_INIT = tempo_m_new
            self.knownTempo = tempo_m_new
            self.TempoDefinite = True

        else:   # two or more onsets have already been received
                # (or one onset but tempo is known)

            # Tempo is either definite (known) or enough onsets have
            # been received to estimate the tempo. Therefore our estimate of 
            # machine BP at t_tempo should be fairly accurate.

            self.knownTempo = tempo_m_new
            self.TempoDefinite = True
            self.i_w_MIN = self.n

            # # 1. Find machine BP at t_tempo based on current estimate
            # BP_ons_est = self.getBeatPosition(t_tempo)
            #     # process tempo change as if it were an onset
            # self.BP_ons.append(BP_ons_est)
            # self.t_ons.append(t_tempo)
            # self.tempo_change_indices.append(self.n)

            # # 2. Set tempo_m and BP_m0
            # self.tempo.append(tempo_m_new)

            # self.BP_0.append(self.BP_ons[-1] - self.tempo[-1]*self.t_ons[-1])

            # # 3. Set i_w_MIN
            # self.i_w_MIN = self.n
            # self.TempoDefinite = True
            # self.n = self.n + 1



    def __tempoChangeReset(self):
        '''
        Resets MBD but keeps beat counting
        '''

        self.tempo_INIT = self.tempo_INIT_ORIGINAL # initial tempo
        self.BP_BBP1 = 1    # Known BP where BBP is 1
        self.n = 0          # number of onsets
        self.TempoDefinite = False    # True once 1st tempo change is made
        self.knownTempo = -1  # becomes greater than 0 once tempo change is made
        self.i_w_MIN = -1    # index of lower window limit. Set whenever tempo change received.
        self.isAlreadyShifted = False # becomes True when controller initiates shift

        # intialise lists
        self.t_ons = []
        self.BP_ons = []
        self.tempo = []
        self.BP_0 = []
        self.tempo_change_indices = []  # array of indices of onsets representing a tempo change
                
    
    
    def __lineOfBestFit(self, tempo_calc=False):
        '''
        Returns values of m and b for the equation of a line of best fit
        through the onsets

        If tempo_calc is True, the full line calculation is done.
        If tempo_calc is False, just the y intercept is calculated.
        '''
        
        # 1. make a list containing all onsets within evaluation window
        i_window = 0
        BP_current = self.BP_ons[-1]
        for i in range(self.n-1, -1, -1):
            if (i == self.i_w_MIN) or (BP_current-self.BP_ons[i] > self.BP_window):
                i_window = i
                break  # onset is outside of window
        x = np.array(self.t_ons[i_window:])     # list of times
        y = np.array(self.BP_ons[i_window:])    # list of BPs
        
        # 2. Calculate tempo as average of tempos within window
        if tempo_calc:  # True when tempo not definite
            tempo_new = 1/(np.mean(x[1:] - x[0:-1])*self.beat_div)    # average tempo   
        else:   # True when tempo is definite
            tempo_new = self.knownTempo  # set the tempo to the known machine tempo
         
        # 3. calculate the "y-intercept" to go through the centre of mass
        BP_0_new = (np.sum(y) - tempo_new*np.sum(x))/len(x)
        # return new tempo and BP estimate
        return tempo_new, BP_0_new
    
    def getBeatPosition(self, t):
        '''
        Returns an estimate of machine beat position at input time t.
        '''
        if self.n == 0: # return -1 if no estimate of machine BP yet.
            return -1

        return self.tempo[-1]*t + self.BP_0[-1]


    def getBarBeatPosition(self, t):
        '''
        Returns an estimate of machine bar beat position at time t
        '''

        if self.n == 0: # return -1 if no estimate of machine BP yet.
            return -1

        # 1. Find the machine BP at time t
        BP = self.getBeatPosition(t)

        # 2. Calculate the machine BBP at time t
        BBP = ((BP-self.BP_BBP1)%self.Nb) + 1

        return BBP
    
    def getBarBeatPositionOfLastOnset(self):
        '''
        Returns bar beat position of most recent onset
        '''
        if self.n == 0: # return -1 if no estimate of machine BP yet.
            return -1

        BBP = ((self.BP_ons[-1]-self.BP_BBP1)%self.Nb) + 1
        return BBP

    def getBeatPositionFunction(self):
        '''
        Returns the variables tempo_m and BP_m0, representing the
        MPE's current estimate of perceptual Beat Position
        
        Returns
        -------
        tempo_m, BP_m0
        '''
        if self.n == 0: # return -1 if no estimate of machine BP yet.
            return -1, -1

        return self.tempo[-1], self.BP_0[-1]
    
    def getTempo(self):
        '''
        Returns the machine tempo at the moment.
        '''
        if self.n == 0: # return -1 if no estimate of machine BP yet.
            return -1   # also means that machine is not yet playing

        return self.tempo[-1]

    def reset(self):
        '''
        Resets all MBE variables
        '''

        self.tempo_INIT = self.tempo_INIT_ORIGINAL # initial tempo
        self.BP_BBP1 = 1    # Known BP where BBP is 1
        self.n = 0          # number of onsets
        self.TempoDefinite = False    # True once 1st tempo change is made
        self.knownTempo = -1  # becomes greater than 0 once tempo change is made
        self.i_w_MIN = -1    # index of lower window limit. Set whenever tempo change received.
        self.isAlreadyShifted = False # becomes True when controller initiates shift

        # intialise lists
        self.t_ons = []
        self.BP_ons = []
        self.tempo = []
        self.BP_0 = []
        self.t_beats = []
        self.tempo_change_indices = []  # array of indices of onsets representing a tempo change
        
    
    def getOnsets(self, include_tempo_changes=True):
        '''
        Returns arrays of onset times and beat position corresponding to each onset
        
        Parameters
        ----------
        include_tempo_change: if False, onsets representing a tempo change are excluded.

        Returns
        -------
        t_ons[], BP_ons[]
        '''
        
        if include_tempo_changes:   
            return self.t_ons, self.BP_ons  # return arrays as they are, incl. tempo change onsets
        
        # otherwise, remove tempo changes from onset arrays and return
        t_ons_output = []
        BP_ons_output = []
        for i in range(self.n):
            if i in self.tempo_change_indices:
                continue
            t_ons_output.append(self.t_ons[i])
            BP_ons_output.append(self.BP_ons[i])

        return self.t_ons, self.BP_ons

    
    def getTempoChangeOnsets(self):
        '''
        Return arrays of onsets representing tempo change messages sent to machine

        Returns
        -------
        t_ons[], BP_ons[]
        '''

        t_ons_output = []
        BP_ons_output = []
        for i in range(self.n):
            if i in self.tempo_change_indices:
                t_ons_output.append(self.t_ons[i])
                BP_ons_output.append(self.BP_ons[i])
            
        return self.t_ons, self.BP_ons
    
    def getEstimates(self):
        '''
        Returns arrays of tempo and beat position intercept containing the machine beat estimate
        made upon reception of each machine onset.

        Returns
        -------
        tempo: list
        BP_0: list
        '''
        return self.tempo, self.BP_0

    def shiftBeatPosition(self, BP_shift:float):
        '''
        Shift machine beat position by an integer amount, BP_shift.
        
        Usually performed by the BeatSyncController to position machine and perceptual BP within one bar relative to each other
        '''

        if BP_shift != 0:   # if shift required is 0, do nothing
            # shift the BP of each onset by the amount [BP_shift]
            self.BP_ons = (np.array(self.BP_ons) + BP_shift).tolist()
            self.BP_0 = (np.array(self.BP_0) + BP_shift).tolist()
            self.isAlreadyShifted = True
    
    def getBeatDivision(self):
        '''
        Returns machine beat division
        '''
        return self.beat_div
    
    def getBeatTimes(self):
        '''
        Returns a list of machine beat times.
        Beats occur at integer values of Beat Position.

        Returns
        -------
        t_beats: list
        '''
        return self.t_beats