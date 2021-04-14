import time
import sys
import signal
from configparser import ConfigParser
import threading
import socket
from amcrest import Http
from datetime import datetime
import pytz
import os
import urllib


class ThreadExited(Exception):
    pass


def signal_handler(signal, frame):
    raise ThreadExited()


def lines(ret, monitor):
    global tz
    line = ''
    try:
        for char in ret.iter_content(decode_unicode=True):
            line = line + char
            if line.endswith('\r\n'):
                yield line.strip()
                line = ''
    except:
        print(str(datetime.now(tz)) + f" - ERROR - Issue with {monitor}. Hopefully recovering...")
        line = ''
        yield line
        # os.kill(os.getpid(), signal.SIGUSR1)


def startrec(monid):
    global host, port
    # print("start")
    zmip = host
    zmport = int(port)
    onvifmid = monid
    onvifcause = 'Motion'
    onviftext1 = 'CamTriggered'
    onvifscore = '1'

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((zmip, zmport))
        triggeron = onvifmid + '|on|' + onvifscore + '|' + onvifcause + '|' + onviftext1
        s.sendall(triggeron.encode('utf-8'))
        s.close()
    except socket.error as exc:
        print(" - ERROR - There was an error sending Start-Recording to zoneminder.")
        print(f" - socket error: {exc}")
        return
    except:
        print(" - ERROR - There was an error sending Start-Recording to zoneminder.")
        return


def stoprec(monid):
    global host, port
    # print("Stop")
    zmip = host
    zmport = int(port)
    onvifmid = monid

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((zmip, zmport))
        triggeron = onvifmid + '|cancel|0||'
        s.sendall(triggeron.encode('utf-8'))
        s.close()
    except socket.error as exc:
        print(" - ERROR - There was an error sending Stop-Recording to zoneminder.")
        print(f" - socket error: {exc}")
        return
    except:
        print(" - ERROR - There was an error sending Stop-Recording to zoneminder.")
        return


def camtrigger(monitor, ip, monid, moncodes):
    global host, port, username, password, tz
    if moncodes != 'VideoMotion':
        print(f" - Subscribing to event codes: {moncodes}")
    moncodes = urllib.parse.quote_plus(moncodes)
    cam = Http(ip, 80, username, password, retries_connection=3, timeout_protocol=3.05)
    try:
        ret = cam.command('eventManager.cgi?action=attach&codes=[' + moncodes + ']', timeout_cmd=(3.05, None), stream=True)
        ret.encoding = 'utf-8'
    except:
        print(f" - ERROR - There was an error starting {monitor}.\n")
        # time.sleep(30)
        return

    print(str(datetime.now(tz)) + f" - Firing up: {monitor}")

    try:
        for line in lines(ret, monitor):
            timenow = datetime.now(tz)
            if line.lower().startswith('content-length:'):
                chunk_size = int(line.split(':')[1])
                action = repr(next(ret.iter_content(chunk_size=chunk_size, decode_unicode=True)))
                if "Start" in action:
                    startrec(monid)
                    print(str(timenow) + f" - {monitor} - Start")
                elif "Stop" in action:
                    stoprec(monid)
                    print(str(timenow) + f" - {monitor} - Stop")
                else:
                    continue
    except KeyboardInterrupt:
        ret.close()


def camthread(monitor):
    global parser
    print(str(datetime.now(tz)) + f" - Starting thread for {monitor}")
    # Get cam config items
    try:
        ip = parser.get(monitor, "ip")
        if debug: print(f" - IP address: {ip}")
    except:
        print(f" - ERROR - IP address is required")
        return
    try:
        monid = parser.get(monitor, "monid")
        if debug: print(f" - ZM monid: {monid}")
    except:
        print(f" - ERROR - ZM monid is required")
        return
    moncodes = parser.get(monitor, "moncodes", fallback="VideoMotion")
    # Init cam thread
    t = threading.Thread(target=camtrigger, args=(monitor, ip, monid, moncodes))
    t.name = monitor
    t.setDaemon(True)
    t.start()


def main():
    global parser
    main_thread = threading.current_thread()
    # Register the signal handlers
    signal.signal(signal.SIGUSR1, signal_handler)
    # signal.signal(signal.SIGTERM, service_shutdown)
    # signal.signal(signal.SIGINT, service_shutdown)

    # Generate set of defined cameras
    camera_set = set()
    for section in parser.sections():
        if (str(section) == 'zm' or str(section) == 'zmat'):
            continue
        else:
            camera_set.add(section)
    while True:
        # Check defined cameras against current threads
        current_threads = set()
        for thread in threading.enumerate():
            if thread is main_thread:
                continue
            current_threads.add(thread.getName())
        for camera in camera_set:
            if debug: print(str(datetime.now(tz)) + f" - Checking for {camera}.")
            if camera in current_threads:
                if debug: print(f" - thread found.")
                # Check for more than it just existing?
            else:
                if debug: print(" - thread not found!")
                # Try to start a thread for this camera
                camthread(camera)
        time.sleep(int(retry))


if __name__ == '__main__':
    global parser, debug, retry, host, port, username, password, tz
    parser = ConfigParser()
    parser.read("zm-amcrest-trigger.conf")
    timezone = parser.get("zm", "tz")
    tz = pytz.timezone(timezone)
    print(str(datetime.now(tz)) + f" - Start Up.")
    debug = parser.getboolean("zmat", "debug", fallback="false")
    retry = parser.get("zmat", "retry", fallback="30")
    host = parser.get("zm", "host")
    port = parser.get("zm", "port")
    if debug: print(f" - Zoneminder IP: {host}:{port}")
    username = parser.get("zm", "defusername")
    password = parser.get("zm", "defpassword")

    main()
