from midi_utils import midi2string, tick2second
from PerceptualBeatEstimator import PerceptualBeatEstimator
from mido import MidiFile
import os
import numpy as np
import matplotlib.pyplot as plt
from PbeTester import PbeTester

test_dir = 'test_sets/set_1/'

for file in os.listdir(os.fsencode(test_dir)): # loop through all midi files in the test set folder
    filename = os.fsdecode(file)
    
    if filename.endswith('.mid'):
        test = MidiFile(test_dir + filename)

        for i, track in enumerate(test.tracks):  # loop through each track in the midi file
            BP_window_params = range(2,13)

            for BP_window in BP_window_params:
                # 1. create a new PbeTester object
                pbeTester = PbeTester(track, ticks_per_beat = test.ticks_per_beat, BP_window=BP_window)

                # 2. get useful stats about the PBE's performance
                test_info = pbeTester.getTestInfo()