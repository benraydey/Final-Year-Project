from mido import MidiFile
import stochasticDrummer

onsets, p_beats = stochasticDrummer.stochasticDrummer(NumBars=4, stdDev_TEMPO=4, stdDev_ERROR=28, seperateFiles=True)

onsets.save('sd_tests/onsets.mid')
p_beats.save('sd_tests/p_beats.mid')