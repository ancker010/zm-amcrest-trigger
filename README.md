### ZoneMinder Amcrest Trigger
This container will connect to configured Amcrest IP Cameras via their HTTP API and "subscribe" to the EventManager to listen for "VideoMotion" alarms.
Upon receiving a "Start", the container will connect to the specified ZoneMinder server to trigger the corresponding ZoneMinder camera to start recording.
ZoneMinder camera must be in the "nodect", "modect", "mocord", or "record" mode for this to operate.

This takes the effort of detecting motion off of Zoneminder and leaves it up to your camera. This is useful when you're running ZM on an underpowered system like a Raspberry Pi.

### NOTE:
I have no idea how robust this is at the moment. It appears to be working will for me, but there might be some issues that break things for you.
I will work to improve it over time.
Use at your own risk.

#### Usage
- Pull the image: `docker pull hardenrm/zm-amcrest-trigger`
- Create a file named `zm-amcrest-trigger.conf` paste in the example data below.
- Edit the `.conf` file with your Zoneminder config, the username and password for the cameras, and your timezone.
- The default ZM_TRIGGER port is `6802`. Unless you know better, don't change this.
- Add cameras using the examples given as a guide.
- Enable `OPT_TRIGGER` in your zoneminder config and restart it.
- Run the container: `docker run -v '/path/to/zm-amcrest-trigger.conf:/app/zm-amcrest-trigger.conf:z' --name zm-amcrest-trigger hardenrm/zm-amcrest-trigger`
- Check the logs for proper operation: `docker logs -f zm-amcrest-trigger`

#### Example Config File
```
[zmat]
debug = false
retry = 60

[zm]
host = zoneminder.example.com
port = 6802
defusername = admin
defpassword = <password>
tz = America/Chicago

[cam1]
ip = 10.1.5.10
monid = 1

[cam2]
ip = 10.1.5.11
monid = 2
```

#### Example Docker-Compose
```
version: '2'
services:
  zm-amcrest-trigger:
    image: hardenrm/zm-amcrest-trigger
    networks:
      - network
    container_name: zm-amcrest-trigger
    volumes:
      - /path/to/zm-amcrest-trigger/zm-amcrest-trigger.conf:/app/zm-amcrest-trigger.conf:z
    restart: unless-stopped

networks:
  network:
    external: true
```
- `docker-compose up -d`