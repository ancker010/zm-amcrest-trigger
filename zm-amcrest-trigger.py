import time
import sys
import signal
from configparser import ConfigParser
from threading import Thread, Lock
import socket
from amcrest import Http
from datetime import datetime
import pytz
import os


class ThreadExited(Exception):
    pass


def signal_handler(signal, frame):
    raise ThreadExited()


def lines(ret, monitor):
    line = ''
    try:
        for char in ret.iter_content(decode_unicode=True):
            line = line + char
            if line.endswith('\r\n'):
                yield line.strip()
                line = ''
    except:
        print(f"Something went wrong with {monitor}. Hopefully recovering...")
        line = ''
        yield line
        os.kill(os.getpid(), signal.SIGUSR1)


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
    except:
        print("There was an error sending Start-Recording to zoneminder.")
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
        triggeron = onvifmid + '|cancel|||'
        s.sendall(triggeron.encode('utf-8'))
        s.close()
    except:
        print("There was an error sending Stop-Recording to zoneminder.")
        return


def camtrigger(monitor, ip, monid):
    global host, port, username, password, tz
    print(f"Starting thread for {monitor}:{ip}:{monid}")
    # print(f"ZM:{host}:{port}")
    # print("0")

    cam = Http(ip, 80, username, password, retries_connection=3, timeout_protocol=3.05)

    try:
        ret = cam.command('eventManager.cgi?action=attach&codes=[VideoMotion]', timeout_cmd=(3.05, None), stream=True)
        ret.encoding = 'utf-8'
    except:
        print(f"There was an error starting {monitor}.\n")
        # time.sleep(30)
        sys.exit()

    # print("1")
    print(f"Firing up: {monitor}")

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



def main():
    global parser
    timenow = datetime.now(tz)
    print(str(timenow) + f" - Start Up.")
    # Register the signal handlers
    signal.signal(signal.SIGUSR1, signal_handler)
    # signal.signal(signal.SIGTERM, service_shutdown)
    # signal.signal(signal.SIGINT, service_shutdown)

    for section in parser.sections():
        if str(section) == 'zm':
            continue
        else:
            monitor = str(section)
            ip = parser.get(section, "ip")
            monid = parser.get(section, "monid")
            t = Thread(target=camtrigger, args=(monitor, ip, monid))
            t.setDaemon(True)
            t.start()
    t.join()
    print("All Monitors Started.\n")
    #try:
    #    while True:
    #        print("Running...\n")
    #        time.sleep(1)
    #except KeyboardInterrupt:
    #    os.exit(1)



if __name__ == '__main__':
    global host, port, username, password, parser, tz
    parser = ConfigParser()
    parser.read("zm-amcrest-trigger.conf")
    host = parser.get("zm", "host")
    port = parser.get("zm", "port")
    username = parser.get("zm", "defusername")
    password = parser.get("zm", "defpassword")
    timezone = parser.get("zm", "tz")
    tz = pytz.timezone(timezone)

    main()

