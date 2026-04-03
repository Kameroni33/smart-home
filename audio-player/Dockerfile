FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsdl2-2.0-0 \
    libsdl2-mixer-2.0-0 \
    libglib2.0-0 \
    alsa-utils \
    libasound2 \
    libpulse0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .
COPY ui/ /ui/

ENV SDL_AUDIODRIVER=pulseaudio
ENV SDL_VIDEODRIVER=dummy
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
