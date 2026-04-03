# Audio Player

A self-hosted white noise / audio player for a headless Raspberry Pi 4. Runs as a Docker container, plays audio through the aux jack, and exposes a web UI accessible over your local network.

---

## Requirements

- Raspberry Pi 4 (or any Linux machine with ALSA audio)
- Fresh Raspberry Pi OS (Bookworm recommended)
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

## 3. Start the Service

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

## 4. Access the Web UI

Find your Pi's IP address:
```bash
hostname -I
```

Then open a browser on any device on your network:
```
http://<pi-ip-address>:8000
```

---

## 5. Add Tracks from YouTube

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
| POST   | /stop       | —                             | Stop playback                |
| POST   | /volume     | `{"level": 80}`               | Set volume (0–100)           |
| GET    | /status     | —                             | Current playback state       |
| POST   | /download   | `{"url": "https://..."}`      | Download YouTube URL as MP3  |

---

## Troubleshooting

**No audio / wrong output device**

Raspberry Pi often has multiple ALSA devices (HDMI + headphone jack). If you're not hearing audio from the aux output, identify your card:

```bash
aplay -l
```

Then add `AUDIODEV=hw:<card>,0` to the `environment` section in `compose.yml`:

```yaml
environment:
  - SDL_AUDIODRIVER=alsa
  - SDL_VIDEODRIVER=dummy
  - AUDIODEV=hw:1,0   # adjust card number as needed
```

Restart the container after any change:
```bash
docker compose up -d
```

**Check container logs for errors:**
```bash
docker compose logs -f audio-player
```
