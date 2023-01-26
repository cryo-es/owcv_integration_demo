import buttplug.client as bp
import asyncio
import time
import winsound
import PySimpleGUI as sg
import configparser
import ow_state
import ow_cv_class


#Global variables
config = configparser.ConfigParser()
config.read(ow_cv_class.resource_path('config.ini'))
BEEP_ENABLED = config["demo"].getboolean("BEEP_ENABLED")
KEEP_ALIVE = float(config["demo"]["KEEP_ALIVE"])
devices = []
current_intensity = 0
intensity_tracker = {}
last_command_time = 0

def device_added(emitter, dev: bp.ButtplugClientDevice):
    devices.append(dev)
    print("Device added: ", dev)

def device_removed(emitter, dev: bp.ButtplugClientDevice):
    print("Device removed: ", dev)

def limit_intensity(intensity):
    if intensity > 1:
        print(f"Intensity was {intensity} but it cannot be higher than 1. Setting it to 1.")
        intensity = 1
    elif intensity < 0:
        print(f"Intensity was {intensity} but it cannot be lower than 0. Setting it to 0.")
        intensity = 0
    return intensity

async def stop_all_devices():
    for device in devices:
        try:
            await device.send_stop_device_cmd()
            print("Stopped all devices.")
        except Exception as err:
            #Add code to retry the command later
            print("A device experienced an error while being stopped. Is it disconnected?")
            print(err)

async def prevent_disconnection(time):
    if time >= (last_command_time + KEEP_ALIVE):
        await alter_intensity(0)

async def alter_intensity(amount):
    global current_intensity
    global last_command_time
    current_intensity = round(current_intensity + amount, 1)
    print(f"Current intensity: {current_intensity}")
    real_intensity = limit_intensity(current_intensity)
    print(f"Real intensity:    {real_intensity}")
    for device in devices:
        try:
            await device.send_vibrate_cmd(real_intensity)
        except Exception as err:
            #Add code to retry the command later
            print("A device experienced an error while having its vibration altered. Is it disconnected?")
            print(err)
    last_command_time = time.time()
    if BEEP_ENABLED:
        winsound.Beep(int(1000 + (real_intensity*5000)), 20)

async def alter_intensity_for_duration(amount, duration, key="None"):
    current_time = time.time()
    if key == "None":
        intensity_tracker[current_time] = [current_time + duration, amount]
    else:
        intensity_tracker[key] = [current_time + duration, amount]
    await alter_intensity(amount)

async def update_intensity():
    current_time = time.time()
    for key in list(intensity_tracker):
        pair = intensity_tracker[key]
        if pair[0] <= current_time:
            del intensity_tracker[key]
            await alter_intensity(-pair[1])

async def main():
    #Read constants from config.ini
    SCREEN_WIDTH = int(config["demo"]["SCREEN_WIDTH"])
    SCREEN_HEIGHT = int(config["demo"]["SCREEN_HEIGHT"])
    USING_INTIFACE = config["demo"].getboolean("USING_INTIFACE")
    PLAYING_MERCY = config["demo"].getboolean("PLAYING_MERCY")
    VIBE_FOR_ELIM = config["demo"].getboolean("VIBE_FOR_ELIM")
    VIBE_FOR_ASSIST = config["demo"].getboolean("VIBE_FOR_ASSIST")
    VIBE_FOR_SAVE = config["demo"].getboolean("VIBE_FOR_SAVE")
    VIBE_FOR_BEING_BEAMED = config["demo"].getboolean("VIBE_FOR_BEING_BEAMED")
    VIBE_FOR_RESURRECT = config["demo"].getboolean("VIBE_FOR_RESURRECT")
    VIBE_FOR_MERCY_BEAM = config["demo"].getboolean("VIBE_FOR_MERCY_BEAM")
    SAVED_VIBE_INTENSITY = float(config["demo"]["SAVED_VIBE_INTENSITY"])
    ELIM_VIBE_INTENSITY = float(config["demo"]["ELIM_VIBE_INTENSITY"])
    ASSIST_VIBE_INTENSITY = float(config["demo"]["ASSIST_VIBE_INTENSITY"])
    BEING_BEAMED_VIBE_INTENSITY =float(config["demo"]["BEING_BEAMED_VIBE_INTENSITY"])
    RESURRECT_VIBE_INTENSITY = float(config["demo"]["RESURRECT_VIBE_INTENSITY"])
    HEAL_BEAM_VIBE_INTENSITY = float(config["demo"]["HEAL_BEAM_VIBE_INTENSITY"])
    DAMAGE_BEAM_VIBE_INTENSITY = float(config["demo"]["DAMAGE_BEAM_VIBE_INTENSITY"])
    RESURRECT_VIBE_DURATION = float(config["demo"]["RESURRECT_VIBE_DURATION"])
    SAVED_VIBE_DURATION = float(config["demo"]["SAVED_VIBE_DURATION"])
    ELIM_VIBE_DURATION = float(config["demo"]["ELIM_VIBE_DURATION"])
    ASSIST_VIBE_DURATION = float(config["demo"]["ASSIST_VIBE_DURATION"])
    DEAD_REFRESH_DELAY = float(config["demo"]["DEAD_REFRESH_DELAY"])
    MAX_REFRESH_RATE = int(config["demo"]["MAX_REFRESH_RATE"])
    
    FINAL_RESOLUTION = {"width":SCREEN_WIDTH, "height":SCREEN_HEIGHT}

    #Set up GUI
    sg.theme("DarkAmber")
    layout = [
        [sg.Text("Status:"), sg.Text("STOPPED", size=(8,1), key="-OUTPUT-")],
        [sg.Button("Start"), sg.Button("Stop"), sg.Button("Quit")]]
    window = sg.Window("Demo", layout)

    #Initialize some variables
    heal_beam_vibe_active = False
    damage_beam_vibe_active = False
    being_beamed_vibe_active = False
    current_elim_count = 0
    current_assist_count = 0
    last_refresh = 0
    player = ow_state.Player(FINAL_RESOLUTION, isMercy=PLAYING_MERCY)

    if USING_INTIFACE:
        client = bp.ButtplugClient("Integration_Demo")

        connector = bp.websocket_connector.ButtplugClientWebsocketConnector("ws://127.0.0.1:12345")

        client.device_added_handler += device_added
        client.device_removed_handler += device_removed

        try:
            await client.connect(connector)
        except Exception as ex:
            print(f"Could not connect to server, exiting: {ex}")
            return

        await client.start_scanning()

    try:
        while True:
            await prevent_disconnection(time.time())
            event, values = window.read(100)
            if event == sg.WIN_CLOSED or event == "Quit":
                print("Window closed.")
                window.close()
                break
            elif event == "Start":
                window["-OUTPUT-"].update("RUNNING")
                print("Running...")

                #Shouldn't need to be calling owcv functions from outside ow_state, should find a better way
                player.owcv.start_capturing(capture_fps=MAX_REFRESH_RATE)
                
                counter = 0
                start_time = time.time()

                while True:
                    await update_intensity()
                    current_time = time.time()
                    await prevent_disconnection(current_time)

                    counter += 1
                    if player.in_killcam or player.death_spectating:
                        if current_time >= last_refresh + DEAD_REFRESH_DELAY:
                            last_refresh = current_time
                            player.refresh()
                    else:
                        last_refresh = current_time
                        player.refresh()

                        if VIBE_FOR_ELIM:
                            if player.elim_notifs > current_elim_count:
                                #New elim appeared
                                difference = player.elim_notifs - current_elim_count
                                current_elim_count = player.elim_notifs
                                await alter_intensity_for_duration(difference*ELIM_VIBE_INTENSITY, ELIM_VIBE_DURATION)

                            elif player.elim_notifs < current_elim_count:
                                #Old elim disappeared
                                current_elim_count = player.elim_notifs

                        if VIBE_FOR_ASSIST:
                            if player.assist_notifs > current_assist_count:
                                #New assist appeared
                                difference = player.assist_notifs - current_assist_count
                                current_assist_count = player.assist_notifs
                                await alter_intensity_for_duration(difference*ASSIST_VIBE_INTENSITY, ASSIST_VIBE_DURATION)

                            elif player.assist_notifs < current_assist_count:
                                #Old assist disappeared
                                current_assist_count = player.assist_notifs
                        
                        if VIBE_FOR_SAVE:
                            if player.saved_notifs > 0 and "saved" not in intensity_tracker:
                                await alter_intensity_for_duration(SAVED_VIBE_INTENSITY, SAVED_VIBE_DURATION, key="saved")

                        if VIBE_FOR_BEING_BEAMED:
                            if being_beamed_vibe_active:
                                if not player.being_beamed:
                                    await alter_intensity(-BEING_BEAMED_VIBE_INTENSITY)
                                    being_beamed_vibe_active = False
                            else:
                                if player.being_beamed:
                                    await alter_intensity(BEING_BEAMED_VIBE_INTENSITY)
                                    being_beamed_vibe_active = True

                        if PLAYING_MERCY:
                            if VIBE_FOR_RESURRECT:
                                if player.resurrecting and "resurrect" not in intensity_tracker:
                                    await alter_intensity_for_duration(RESURRECT_VIBE_INTENSITY, RESURRECT_VIBE_DURATION, key="resurrect")
                            
                            if VIBE_FOR_MERCY_BEAM:
                                if player.heal_beam:
                                    if not heal_beam_vibe_active:
                                        if damage_beam_vibe_active:
                                            await alter_intensity(HEAL_BEAM_VIBE_INTENSITY-DAMAGE_BEAM_VIBE_INTENSITY)
                                            heal_beam_vibe_active = True
                                            damage_beam_vibe_active = False
                                        else:
                                            await alter_intensity(HEAL_BEAM_VIBE_INTENSITY)
                                            heal_beam_vibe_active = True
                                elif player.damage_beam:
                                    if not damage_beam_vibe_active:
                                        if heal_beam_vibe_active:
                                            await alter_intensity(DAMAGE_BEAM_VIBE_INTENSITY-HEAL_BEAM_VIBE_INTENSITY)
                                            damage_beam_vibe_active = True
                                            heal_beam_vibe_active = False
                                        else:
                                            await alter_intensity(DAMAGE_BEAM_VIBE_INTENSITY)
                                            damage_beam_vibe_active = True
                                elif heal_beam_vibe_active:
                                        await alter_intensity(-HEAL_BEAM_VIBE_INTENSITY)
                                        heal_beam_vibe_active = False
                                elif damage_beam_vibe_active:
                                    await alter_intensity(-DAMAGE_BEAM_VIBE_INTENSITY)
                                    damage_beam_vibe_active = False

                    event, values = window.read(timeout=1)
                    if event == sg.WIN_CLOSED or event == "Quit":
                        window.close()
                        break
                    if event == "Stop":
                        window["-OUTPUT-"].update("STOPPED")
                        await stop_all_devices()
                        print("Stopped.")
                        break

                #Shouldn't need to be calling owcv functions from outside ow_state, should find a better way
                player.owcv.stop_capturing()

                duration = time.time() - start_time
                print(f"Loops per second: {counter/(duration)}")
                print(f"Average time: {round(1000 * (duration/counter), 4)}ms")

    except Exception as ex:
        await stop_all_devices()
        print(ex)
        if BEEP_ENABLED:
            winsound.Beep(1000, 500)

    await stop_all_devices()
    print("Quitting.")
    
    if USING_INTIFACE:
        await client.stop_scanning()
        await client.disconnect()
        print("Disconnected.")

asyncio.run(main(), debug=False)
