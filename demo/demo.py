from buttplug.client import (ButtplugClientWebsocketConnector, ButtplugClient,
                             ButtplugClientDevice, ButtplugClientConnectorError)
from buttplug.core import ButtplugLogLevel
import numpy as np
import asyncio
import cv2
import time
import winsound
import PySimpleGUI as sg
import configparser
import ow_state
import ow_cv_class


#Read constants from config.ini
config = configparser.ConfigParser()
config.read(ow_cv_class.resource_path('config.ini'))

BEEP_ENABLED = config["demo"].getboolean("BEEP_ENABLED")
USING_INTIFACE = config["demo"].getboolean("USING_INTIFACE")
SAVED_VIBE_INTENSITY = float(config["demo"]["SAVED_VIBE_INTENSITY"])
ELIM_VIBE_INTENSITY = float(config["demo"]["ELIM_VIBE_INTENSITY"])
ASSIST_VIBE_INTENSITY = float(config["demo"]["ASSIST_VIBE_INTENSITY"])
RESURRECT_VIBE_INTENSITY = float(config["demo"]["RESURRECT_VIBE_INTENSITY"])
HEAL_BEAM_VIBE_INTENSITY = float(config["demo"]["HEAL_BEAM_VIBE_INTENSITY"])
DAMAGE_BEAM_VIBE_INTENSITY = float(config["demo"]["DAMAGE_BEAM_VIBE_INTENSITY"])
RESURRECT_VIBE_DURATION = float(config["demo"]["RESURRECT_VIBE_DURATION"])
SAVED_VIBE_DURATION = float(config["demo"]["SAVED_VIBE_DURATION"])
ELIM_VIBE_DURATION = float(config["demo"]["ELIM_VIBE_DURATION"])
ASSIST_VIBE_DURATION = float(config["demo"]["ASSIST_VIBE_DURATION"])
VIBE_FOR_ELIM = config["demo"].getboolean("VIBE_FOR_ELIM")
VIBE_FOR_ASSIST = config["demo"].getboolean("VIBE_FOR_ASSIST")
VIBE_FOR_SAVE = config["demo"].getboolean("VIBE_FOR_SAVE")
PLAYING_MERCY = config["demo"].getboolean("PLAYING_MERCY")
VIBE_FOR_RESURRECT = config["demo"].getboolean("VIBE_FOR_RESURRECT")
VIBE_FOR_MERCY_BEAM = config["demo"].getboolean("VIBE_FOR_MERCY_BEAM")


sg.theme("DarkAmber")
layout = [
    [sg.Text("Status:"), sg.Text("STOPPED", size=(8,1), key="-OUTPUT-")],
    [sg.Button("Start"), sg.Button("Stop"), sg.Button("Quit")]]
devices = []
intensity_tracker = {}
current_intensity = 0
player = ow_state.Player(isMercy=PLAYING_MERCY)


async def watch_overwatch():
    try:
        heal_beam_vibe_active = False
        damage_beam_vibe_active = False
        saved_notif_vibe_active = False
        current_elim_count = 0
        current_assist_count = 0
        window = sg.Window("Demo", layout)
        event = ''
        while True:
            event, values = window.read()
            if event == sg.WIN_CLOSED or event == "Quit":
                print("Window closed.")
                window.close()
                break
            elif event == "Start":
                window["-OUTPUT-"].update("RUNNING")
                print("Running...")
                while True:
                    await update_intensity()
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

                    if PLAYING_MERCY and VIBE_FOR_RESURRECT:
                        if player.resurrecting and "resurrect" not in intensity_tracker:
                            await alter_intensity_for_duration(RESURRECT_VIBE_INTENSITY, RESURRECT_VIBE_DURATION, key="resurrect")

                    if PLAYING_MERCY and VIBE_FOR_MERCY_BEAM:
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
                        print("Stopped.")
                        break
                await stop_all_devices()

    except Exception as ex:
        await stop_all_devices()
        print(ex)
        if BEEP_ENABLED:
            winsound.Beep(1000, 500)

    #cv2.destroyAllWindows()

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
            await device.send_stop_device_cmd()
    print("Stopped all devices.")

async def alter_intensity(amount):
    global current_intensity
    current_intensity = round(current_intensity + amount, 1)
    print(f"Current intensity: {current_intensity}")
    real_intensity = limit_intensity(current_intensity)
    print(f"Real intensity:    {real_intensity}")
    for device in devices:
        await device.send_vibrate_cmd(real_intensity)
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

def device_added(emitter, dev: ButtplugClientDevice):
    devices.append(dev)
    print("Device added: ", dev)

def device_removed(emitter, dev: ButtplugClientDevice):
    print("Device removed: ", dev)

async def main():
    if USING_INTIFACE:
        client = ButtplugClient("Test Client")

        connector = ButtplugClientWebsocketConnector("ws://127.0.0.1:12345")

        client.device_added_handler += device_added
        client.device_removed_handler += device_removed

        try:
            await client.connect(connector)
        except ButtplugClientConnectorError as ex:
            print("Could not connect to server, exiting: {}".format(ex.message))
            return

        await client.start_scanning()

    task = asyncio.create_task(watch_overwatch())
    await task

    print("Quitting.")
    
    if USING_INTIFACE:
        await client.stop_scanning()
        await client.disconnect()
        print("Disconnected.")

asyncio.run(main(), debug=True)
