# owcv_integration_demo

This is very much just a prototype/demo, I threw the vibrator part of this together in an afternoon.
It's mainly to give people in Furi's server something to play with, and also I guess to demonstrate an example of integrating with my OW2 CV project.

Known Issues:
- Crashes shortly after launch if you don't have a device connected to Intiface (probably)
- Resolutions other than 1920x1080 probably don't work (templates/masks need to be scaled)
- Detecting resurrect in Kiriko ult probably won't work
- Might have a performance impact because I haven't capped how often it reads the screen
