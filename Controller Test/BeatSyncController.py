'''
Beat Sync Controller

@author: Ben Adey
@year: 2020
'''

from MachineBeatEstimator import MachineBeatEstimator
from PerceptualBeatEstimator import PerceptualBeatEstimator
from math import ceil

class BeatSyncController:

    def __init__(self, Nb=4):
        # initialise user parameters
        self.Nb = Nb

        # 1. Max tempo change rate
        self.T_tempo_MIN = 1

        # 2. Max tempo slope
        # delta_BP_sync = 0.1 # [beats]
        # delta_t_sync = 2 # [seconds]
        # self.delta_tempo_max = delta_BP_sync/delta_t_sync
        self.delta_tempo_max = 0.0005
    
        # 3. Acceptable BP error
        # acceptable time error
        self.epsilon_t = 0.01 # [seconds]

        # 4. Arrays for stats
        self.BP_errors = []     # array of BP errors at each tempo change
    
    def sample(self, t_tempo, PBE:PerceptualBeatEstimator, MBE:MachineBeatEstimator):
        '''
        Calculates the new machine tempo to be set at tempo change time t_tempo
        for the machine to keep in time with the perceptual beat.
        
        Returns
        -------
        tempo_m_NEW: float [beats per second]
            New machine tempo to be set at time t_tempo
        '''

        # Get parameters from PerceptualBeatEstimator and MachineBeatEstimator
        tempo_p, BP_p0 = PBE.getBeatPositionFunction()
        tempo_m, BP_m0 = MBE.getBeatPositionFunction()

        # Check if input is playing
        if tempo_p == -1:   # True when input not playing
            return -1

        # Check if machine not playing
        if tempo_m == -1:  # True when machine is stopped
            # Input is playing, but machine is not
            # Return input tempo to be sent to machine
            return tempo_p
        
        if not MBE.isAlreadyShifted:
            # Shift has not yet taken place -> controller must calculate appropriate shift
            # so that machine BP is close to perceptual BP (the error in BP must be the same as
            # the error in BBP)

            # Calculate error in BBP at tempo change time t_tempo
            error = MBE.getBarBeatPosition(t_tempo) - PBE.getBarBeatPosition(t_tempo)
            self.BP_errors.append(error)
            if (0 < error < self.Nb/2) or (-self.Nb/2 <= error < 0):
                BP_m0_d = PBE.getBeatPosition(t_tempo) + error - tempo_m*t_tempo
            elif error >= self.Nb/2:
                BP_m0_d = PBE.getBeatPosition(t_tempo) + error - self.Nb - tempo_m*t_tempo
            else:   # error < -Nb/2
                BP_m0_d = PBE.getBeatPosition(t_tempo) + error + self.Nb - tempo_m*t_tempo
            
            BP_shift = BP_m0_d - BP_m0  # shift required for machine and perceptual BP to be within one bar
            if BP_shift != 0:   # True when no shift required - we expect this if machine starts with input (e.g drummer)
                MBE.shiftBeatPosition(BP_shift)
            tempo_m, BP_m0 = MBE.getBeatPositionFunction()            

        

        # 1. Check if ahead or behind or within acceptable error
        BP_error = MBE.getBeatPosition(t_tempo) - PBE.getBeatPosition(t_tempo)
        self.BP_errors.append(BP_error)
        # TODO: determine an appropriate delta_tempo_max based on how out of sync the machine is
        self.delta_tempo_max = self.__deltaTempoMax(BP_error)

        if abs(BP_error) <= tempo_p*self.epsilon_t:
            tempo_m_NEW = tempo_p   # machine is close enough to perceptual beat, therefore match perceptual tempo
            return tempo_m_NEW
        elif BP_error > 0:
            # Machine is ahead -> slow down
            delta_tempo_max = -self.delta_tempo_max    # machine tempo must be greater than perceptual tempo
        else:
            # Machine is behind -> speed up
            delta_tempo_max = self.delta_tempo_max  # machine tempo must be greater than perceptual tempo

        # 2. Find minimum interception time given control parameter delta_tempo_max
        t_int_MIN = (BP_p0 - BP_m0 + (tempo_p - tempo_m + delta_tempo_max)*t_tempo)/delta_tempo_max

        # 3. Calculate tempo change time soonest after t_int_MIN
        t_int = t_tempo + ceil((t_int_MIN-t_tempo)/self.T_tempo_MIN)*self.T_tempo_MIN
        
        # 4. Calculate new machine tempo to be set at time t_tempo
        tempo_m_NEW = (tempo_p*t_int + BP_p0 - (tempo_m*t_tempo + BP_m0))/(t_int - t_tempo)

        return tempo_m_NEW
    
    def __deltaTempoMax(self, BP_error):
        '''
        Returns the appropriate max tempo slope for the given BP error
        '''
        return 0.3
        
        BP_error = abs(BP_error)

        if BP_error > 0.3:
            delta_tempo_max = 0.5
        elif BP_error > 0.2:
            delta_tempo_max = 0.38
        elif BP_error > 0.1:
            delta_tempo_max = 0.3
        elif BP_error > 0.08:
            delta_tempo_max = 0.2
        elif BP_error > 0.06:
            delta_tempo_max = 0.1
        elif BP_error > 0.04:
            delta_tempo_max = 0.05
        else:
            delta_tempo_max = 0.04
        
        return delta_tempo_max
        
        delta_tempo_max_MIN = 0.0005
        
        # we will make an assumption that we want to synchronise over a certain amount of time

        delta_t_sync = 8 # [seconds]


        

        # delta_BP_sync = 0.1 # [beats]
        # delta_t_sync = 2 # [seconds]
        # self.delta_tempo_max = delta_BP_sync/delta_t_sync
    
    def getErrors(self):
        '''
        returns a list of BP errors measured at each tempo change
        '''
        return self.BP_errors

    def reset(self):
        '''
        Resets all controller parameters
        ''' 
        self.BP_errors = []     # array of BP errors at each tempo change