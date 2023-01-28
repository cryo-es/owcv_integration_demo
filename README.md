# owcv_integration_demo
[Download](https://github.com/cryo-es/owcv_integration_demo/releases)

Controls your vibrator/vibrating toy based on what's happening in Overwatch 2, using computer vision.

This started out as a prototype/demo that I threw together in an afternoon, but I've been sucked into it so it's becoming a fully-fledged project now. Open to name ideas!

Requires [Intiface Central](https://intiface.com/central/)  if you want to use it with a toy.

Default settings:
- **Elimination:** +30% intensity for 6 seconds
- **Assist:** +10% intensity for 3 seconds
- **Resurrect:** +100% intensity for 4 seconds
- **Heal beam:** +10% intensity while active
- **Damage boost beam:** +20% intensity while active

Known Issues:
- Some users have reported bugginess at resolutions other than 1920x1080. I'm looking into it.
- Fails to launch if Intiface's server isn't running
- Crashes shortly after launch if you don't have a device connected to Intiface (probably)
- Detecting resurrect in Kiriko ult probably won't work
- High latency to the game server causes Mercy's beam to reconnect to targets slower. This can cause temporary gaps in vibration.
- Only works on Windows
