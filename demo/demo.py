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
OUTPUT_WINDOW_ENABLED = config["demo"].getboolean("OUTPUT_WINDOW_ENABLED")
BEEP_ENABLED = config["demo"].getboolean("BEEP_ENABLED")
KEEP_ALIVE = config["demo"].getfloat("KEEP_ALIVE")
MIN_INTENSITY_STEP = config["demo"].getfloat("MIN_INTENSITY_STEP")
devices = []
current_intensity = 0
intensity_tracker = {}
last_command_time = 0


#Set up GUI
sg.theme("DarkAmber")
layout = [
    [sg.Text("Devices connected:"), sg.Text("0", size=(4,1), key="-DEVICE_COUNT-")],
    [sg.Text("Current intensity:"), sg.Text("0%", size=(17,1), key="-CURRENT_INTENSITY-")],
    [sg.Text("Program status:"), sg.Text("READY", size=(15,1), key="-PROGRAM_STATUS-")],
    [sg.Button("Start"), sg.Button("Stop", disabled=True), sg.Button("Quit")]]

if OUTPUT_WINDOW_ENABLED:
    layout.insert(0, [sg.Multiline(size=(60,15), disabled=True, reroute_stdout=True, autoscroll=True)])
window = sg.Window("Demo", layout, finalize=True)

def device_added(emitter, dev: bp.ButtplugClientDevice):
    devices.append(dev)
    print("Device added: ", dev)
    window["-DEVICE_COUNT-"].update(str(len(devices)))

def device_removed(emitter, dev: bp.ButtplugClientDevice):
    print("Device removed: ", dev)
    window["-DEVICE_COUNT-"].update(str(len(devices)))

def limit_intensity(intensity):
    if intensity > 1:
        #print(f"Intensity was {intensity} but it cannot be higher than 1. Setting it to 1.")
        intensity = 1
    elif intensity < 0:
        print(f"Intensity was {intensity} but it cannot be lower than 0. Setting it to 0.")
        intensity = 0
    return intensity

async def stop_all_devices():
    for device in devices:
        try:
            await device.send_stop_device_cmd()
        except Exception as err:
            print("A device experienced an error while being stopped. Is it disconnected?")
            print(err)
            devices.remove(device)
    window["-DEVICE_COUNT-"].update(len(devices))
    print("Stopped all devices.")

async def prevent_disconnection(time):
    if time >= (last_command_time + KEEP_ALIVE):
        await alter_intensity(0)

async def alter_intensity(amount):
    global current_intensity
    global last_command_time
    current_intensity = MIN_INTENSITY_STEP * round((current_intensity + amount) / MIN_INTENSITY_STEP, 0)
    print(f"Current intensity: {current_intensity}")
    real_intensity = limit_intensity(current_intensity)
    print(f"Real intensity:    {real_intensity}")
    for device in devices:
        try:
            await device.send_vibrate_cmd(real_intensity)
            window["-CURRENT_INTENSITY-"].update(str(int(current_intensity*100)) + ("%" if current_intensity == real_intensity else "% (max 100%)"))
        except Exception as err:
            device.send_stop_device_cmd()
            devices.remove(device)
            window["-DEVICE_COUNT-"].update(len(devices))
            print("A device experienced an error while having its vibration altered. Did it disconnect?")
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
    SCREEN_WIDTH = config["demo"].getint("SCREEN_WIDTH")
    SCREEN_HEIGHT = config["demo"].getint("SCREEN_HEIGHT")

    USING_INTIFACE = config["demo"].getboolean("USING_INTIFACE")
    PLAYING_MERCY = config["demo"].getboolean("PLAYING_MERCY")

    VIBE_FOR_ELIM = config["demo"].getboolean("VIBE_FOR_ELIM")
    ELIM_VIBE_INTENSITY = config["demo"].getfloat("ELIM_VIBE_INTENSITY")
    ELIM_VIBE_DURATION = config["demo"].getfloat("ELIM_VIBE_DURATION")

    VIBE_FOR_ASSIST = config["demo"].getboolean("VIBE_FOR_ASSIST")
    ASSIST_VIBE_INTENSITY = config["demo"].getfloat("ASSIST_VIBE_INTENSITY")
    ASSIST_VIBE_DURATION = config["demo"].getfloat("ASSIST_VIBE_DURATION")

    VIBE_FOR_SAVE = config["demo"].getboolean("VIBE_FOR_SAVE")
    SAVED_VIBE_INTENSITY = config["demo"].getfloat("SAVED_VIBE_INTENSITY")
    SAVED_VIBE_DURATION = config["demo"].getfloat("SAVED_VIBE_DURATION")

    VIBE_FOR_BEING_BEAMED = config["demo"].getboolean("VIBE_FOR_BEING_BEAMED")
    BEING_BEAMED_VIBE_INTENSITY =config["demo"].getfloat("BEING_BEAMED_VIBE_INTENSITY")

    VIBE_FOR_RESURRECT = config["demo"].getboolean("VIBE_FOR_RESURRECT")
    RESURRECT_VIBE_INTENSITY = config["demo"].getfloat("RESURRECT_VIBE_INTENSITY")
    RESURRECT_VIBE_DURATION = config["demo"].getfloat("RESURRECT_VIBE_DURATION")

    VIBE_FOR_MERCY_BEAM = config["demo"].getboolean("VIBE_FOR_MERCY_BEAM")
    HEAL_BEAM_VIBE_INTENSITY = config["demo"].getfloat("HEAL_BEAM_VIBE_INTENSITY")
    DAMAGE_BEAM_VIBE_INTENSITY = config["demo"].getfloat("DAMAGE_BEAM_VIBE_INTENSITY")

    DEAD_REFRESH_DELAY = config["demo"].getfloat("DEAD_REFRESH_DELAY")
    WEBSOCKET_ADDRESS = config["demo"]["WEBSOCKET_ADDRESS"]
    WEBSOCKET_PORT = config["demo"]["WEBSOCKET_PORT"]
    MAX_REFRESH_RATE = config["demo"].getint("MAX_REFRESH_RATE")


    #Initialize some variables
    scanning = False
    heal_beam_vibe_active = False
    damage_beam_vibe_active = False
    being_beamed_vibe_active = False
    current_elim_count = 0
    current_assist_count = 0
    last_refresh = 0
    player = ow_state.Player({"width":SCREEN_WIDTH, "height":SCREEN_HEIGHT}, isMercy=PLAYING_MERCY)

    if USING_INTIFACE:
        client = bp.ButtplugClient("Integration_Demo")

        connector = bp.websocket_connector.ButtplugClientWebsocketConnector(f"{WEBSOCKET_ADDRESS}:{WEBSOCKET_PORT}")

        client.device_added_handler += device_added
        client.device_removed_handler += device_removed

        try:
            await client.connect(connector)
        except Exception as ex:
            print(f"Could not connect to server: {ex}")
            window["-PROGRAM_STATUS-"].update("INTIFACE ERROR")
            window["Start"].update(disabled=True)

        try:
            await client.start_scanning()
            scanning = True
        except Exception as ex:
            print(f"Could not initiate scanning: {ex}")
            window["Start"].update(disabled=True)

    try:
        while True:
            event, values = window.read(timeout=100)
            if event == sg.WIN_CLOSED or event == "Quit":
                window.close()
                print("Window closed.")
                break

            if event == "Start":
                window["Stop"].update(disabled=False)
                window["Start"].update(disabled=True)
                window["-PROGRAM_STATUS-"].update("RUNNING")
                print("Running...")

                player.start_tracking(MAX_REFRESH_RATE)
                
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
                        await stop_all_devices()
                        window["-PROGRAM_STATUS-"].update("STOPPING")
                        window["Stop"].update(disabled=True)
                        window["Quit"].update(disabled=True)
                        print("Stopped.")
                        window.refresh()
                        break

                if event == sg.WIN_CLOSED or event == "Quit":
                    print("Window closed.")
                    break
                
                duration = time.time() - start_time
                print(f"Loops completed: {counter}")
                print(f"Loops per second: {round(counter/(duration), 2)}")
                print(f"Average time: {round(1000 * (duration/counter), 2)}ms")
                window.refresh()
                
                player.stop_tracking()
                
                window["-PROGRAM_STATUS-"].update("READY")
                window["Quit"].update(disabled=False)
                window["Start"].update(disabled=False)

    except Exception as ex:
        await stop_all_devices()
        if BEEP_ENABLED:
            winsound.Beep(1000, 500)
        window["-PROGRAM_STATUS-"].update("UNKNOWN ERROR")
        print(f"Error caught: {ex}")

    await stop_all_devices()
    
    if USING_INTIFACE:
        if scanning:
            await client.stop_scanning()
        await client.disconnect()
        print("Disconnected.")

    window.close()
    print("Quitting.")

asyncio.run(main(), debug=False)
