# Notes:
# This is very much just a prototype/demo, I threw the vibrator part of this together in an afternoon
# It's mainly to give people in Furi's server something to play with
# And also I guess to demonstrate an example of integrating with my OW2 CV project

# Known Issues:
# Resolutions other than 1920x1080 probably don't work (templates/masks need to be scaled)
# Detecting resurrect in Kiriko ult probably won't work

#Debug options
BEEP_ENABLED = False
USING_INTIFACE = True
USING_DEVICE = True

#Intensities
SAVED_VIBE_INTENSITY = 1
ELIM_VIBE_INTENSITY = 0.3
ASSIST_VIBE_INTENSITY = 0.1
RESURRECT_VIBE_INTENSITY = 1
HEAL_BEAM_VIBE_INTENSITY = 0.1
DAMAGE_BEAM_VIBE_INTENSITY = 0.2

#Durations
RESURRECT_VIBE_DURATION = 4
SAVED_VIBE_DURATION = 4
ELIM_VIBE_DURATION = 6
ASSIST_VIBE_DURATION = 3

#Toggles
VIBE_FOR_ELIM = True
VIBE_FOR_ASSIST = True
VIBE_FOR_SAVE = False
PLAYING_MERCY = True
VIBE_FOR_RESURRECT = True
VIBE_FOR_MERCY_BEAM = True