from midi_utils import midi2string
from PerceptualBeatEstimator import PerceptualBeatEstimator
from mido import MidiFile

midi = MidiFile('test_sets/set_1/pattern_1.mid')

with open('test_sets/set_1/pattern_1_midi.txt', "w") as text:
    text.write(midi2string(midi))