from midi_utils import midi2string
from mido import MidiFile

pb = MidiFile('test_sets/set_2/onsets.mid')

with open('test_sets/set_2/onsets.txt', "w") as text:
    text.write(midi2string(pb))