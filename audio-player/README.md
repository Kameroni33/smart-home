# Audio Player

A self-hosted white noise / audio player for a headless Raspberry Pi. Runs as a Docker container and exposes a web UI accessible over your local network.

Supports Bluetooth speakers (default) and USB aux adapters.

---

## Requirements

- Raspberry Pi 4 or 5 (or any Linux machine with PipeWire or ALSA)
- Raspberry Pi OS Bookworm (recommended)
- Internet connection for initial setup

---

## 1. Clone the Repository

```bash
git clone git@github.com:Kameroni33/smart-home.git
cd smart-home/audio-player
```

---

## 2. Install Docker on a Fresh Raspberry Pi OS

```bash
# Download and run the official Docker install script
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Add your user to the docker group so you can run docker without sudo
sudo usermod -aG docker $USER

# Apply the group change (or log out and back in)
newgrp docker

# Verify
docker --version
docker compose version
```

---

## 3. Audio Output

The container routes audio through the host's PipeWire audio server (default on Pi OS Bookworm), which handles both Bluetooth and USB audio devices.

### Bluetooth Speaker

**3a. Install Bluetooth tools on the Pi (if not already present):**
```bash
sudo apt install -y bluez bluez-tools
```

**3b. Pair and trust your speaker:**
```bash
bluetoothctl
```

Inside the bluetoothctl prompt:
```
power on
agent on
scan on
# Wait for your speaker's MAC address to appear, e.g. AA:BB:CC:DD:EE:FF
pair AA:BB:CC:DD:EE:FF
trust AA:BB:CC:DD:EE:FF
connect AA:BB:CC:DD:EE:FF
exit
```

Once trusted, the speaker will reconnect automatically on boot.

**3c. Confirm PipeWire sees the device:**
```bash
pactl list sinks short
```

You should see your Bluetooth speaker listed. If not, check that PipeWire is running:
```bash
systemctl --user status pipewire pipewire-pulse
```

The compose.yml mounts the PipeWire PulseAudio socket (`/run/user/1000/pulse`) into the container. If your Pi user has a different UID than `1000`, update the socket path in `compose.yml` accordingly:
```bash
id -u  # check your UID
```

### USB Aux Adapter

When switching to a USB audio adapter, edit `compose.yml` — comment out the Bluetooth/PulseAudio block and uncomment the ALSA block at the bottom of the file. Then identify your card number:
```bash
aplay -l
```

---

## 4. Start the Service

```bash
# From inside audio-player/
docker compose up -d --build
```

The first build downloads dependencies — this may take a few minutes on a Pi.

To follow logs:
```bash
docker compose logs -f
```

To stop the service:
```bash
docker compose down
```

---

## 5. Access the Web UI

Find your Pi's IP address:
```bash
hostname -I
```

Then open a browser on any device on your network:
```
http://<pi-ip-address>:8000
```

---

## 6. Add Tracks from YouTube

The web UI has a built-in YouTube downloader. Paste any YouTube video or playlist URL into the **Add from YouTube** field and click **Download** (or press Enter). The track will be downloaded, converted to MP3, saved to the `tracks/` folder, and appear in the list automatically.

You can also drop `.mp3` files directly into the `audio-player/tracks/` folder — they'll appear in the UI without a restart.

### CLI alternative

`yt-dlp` is also available inside the running container if you prefer the command line:

```bash
docker compose exec audio-player yt-dlp \
  -x --audio-format mp3 \
  -o "/tracks/%(title)s.%(ext)s" \
  "https://www.youtube.com/watch?v=<VIDEO_ID>"
```

---

## API Endpoints

| Method | Path        | Body                          | Description                  |
|--------|-------------|-------------------------------|------------------------------|
| GET    | /tracks     | —                             | List available tracks        |
| POST   | /play       | `{"track": "file.mp3"}`       | Play a track (loops)         |
| POST   | /pause      | —                             | Toggle pause / resume        |
| POST   | /volume     | `{"level": 80}`               | Set volume (0–100)           |
| GET    | /status     | —                             | Current playback state       |
| POST   | /download   | `{"url": "https://..."}`      | Download YouTube URL as MP3  |

---

## Troubleshooting

**No audio over Bluetooth**

Make sure the speaker is connected on the host before starting the container:
```bash
bluetoothctl connect AA:BB:CC:DD:EE:FF
pactl list sinks short  # confirm it appears
```

Then restart the container:
```bash
docker compose restart
```

**PipeWire socket not found**

The container expects the socket at `/run/user/1000/pulse/native`. Verify yours:
```bash
ls /run/user/$(id -u)/pulse/
```

Update the volume mount and `PULSE_SERVER` in `compose.yml` if your UID differs.

**Check container logs for errors:**
```bash
docker compose logs -f audio-player
```
