# owcv_integration_demo
Controls your vibrator/vibrating toy based on what's happening in Overwatch 2, using computer vision.

Requires [Intiface Central](https://intiface.com/central/)  if you want to use it with a toy.

Default settings:
- **Elimination:** +30% intensity for 6 seconds
- **Assist:** +10% intensity for 3 seconds
- **Resurrect:** +100% intensity for 4 seconds
- **Heal beam:** +10% intensity while active
- **Damage boost beam:** +20% intensity while active

This is very much just a prototype/demo, I threw the vibrator part of this together in an afternoon.
It's mainly to give people in Furi's server something to play with, and also I guess to demonstrate an example of integrating with my OW2 CV project.

Known Issues:
- Fails to launch if Intiface's server is not running
- Crashes shortly after launch if you don't have a device connected to Intiface (probably)
- Detecting resurrect in Kiriko ult probably won't work
- High latency to the game server causes Mercy's beam to reconnect to targets slower. This can cause temporary gaps in vibration.
