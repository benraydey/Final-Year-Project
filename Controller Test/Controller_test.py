#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 22 11:31:52 2020

@author: benadey
"""

from MachineBeatEstimator import MachineBeatEstimator
from PerceptualBeatEstimator import PerceptualBeatEstimator
from BeatSyncController import BeatSyncController
import matplotlib.pyplot as plt
from matplotlib import style
import numpy as np
style.use('ggplot')


t_ons_P = [482.261281495, 482.803842021, 483.395537781, 483.964923844, 484.532064384, 485.105317935, 485.678593535, 486.236940489, 486.805258031, 487.377341295, 487.935758928, 488.517700427]
BP_ons_P = [1, 2, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0]

t_ons_M = [478.564299345, 478.814364516, 479.064181075, 479.314170971, 479.56425888, 479.814499371, 480.064221581, 480.314238946, 480.564235266, 480.814217582, 481.0642796, 481.314252899, 481.56425529, 481.814182734, 482.064266284, 482.314251617, 482.563868076, 482.814516895, 483.064240854, 483.314316925, 483.564213295, 483.811954417, 484.064328812, 484.314221292, 484.56424905, 484.814435296, 485.06451559, 485.314382641, 485.564260768, 485.814453117, 486.064203645, 486.314297453, 486.564205619, 486.814365764, 487.064293036, 487.314242503, 487.569335445, 487.814400224, 488.064159598, 488.314263302, 488.564452567, 488.814210486, 489.059756555, 489.314261651]
BP_ons_M = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 14.5, 15.0, 15.5, 16.0, 16.5, 17.0, 17.5, 18.0, 18.5, 19.0, 19.5, 20.0, 20.5, 21.0, 21.5, 22.0, 22.5]

# Shift BP_ons_M
BP_ons_M = (np.array(BP_ons_M) + 1).tolist()

t_ons_M = t_ons_M[0:-3]
BP_ons_M = BP_ons_M[0:-3]

PBE = PerceptualBeatEstimator()
MBE = MachineBeatEstimator()
controller = BeatSyncController()

for i in range(len(t_ons_P)):
    PBE.onset(t_ons_P[i])

for i in range(len(t_ons_M)):
    MBE.onset(t_ons_M[i],BP_ons_M[i])

tempo_p, bp0_p = PBE.getBeatPositionFunction()
tempo_m, bp0_m = MBE.getBeatPositionFunction()

t_tempo = 489
t_later = 494

t = np.array([t_tempo, t_later])

plt.figure()
plt.title('Beat Position versus Time')
plt.xlabel('t [s]')
plt.ylabel(r'$\theta(t)$ [beats]')
plt.xlim(t)
#plt.ylim([10.5, 20])

plt.plot(t, tempo_p*t + bp0_p, color='tab:purple', label='Perceptual BP')
#plt.plot(t, tempo_m*t + bp0_m, label='Machine BP')

tempo_m_NEW = controller.sample(t_tempo, PBE, MBE)

plt.plot(t, tempo_m*t + MBE.getBeatPositionFunction()[1], color='tab:orange', label='Machine BP accor. to ctrl')
plt.plot(t, tempo_m*t_tempo + MBE.getBeatPositionFunction()[1] + tempo_m_NEW*(t-t[0]), color='red', label='controller decision')
plt.legend(loc=4)
plt.show()

print(f'tempo_p={tempo_p*60:5.1f} bpm\ntempo_m_NEW={tempo_m_NEW*60:5.1f} bpm')
