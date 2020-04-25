FROM cccs/assemblyline-v4-service-base:latest

ENV SERVICE_PATH torrentslicer.TorrentSlicer

# Switch to assemblyline user
USER assemblyline

RUN pip install --no-cache-dir --user \
  bencode.py \
  bitmath  && rm -rf ~/.cache/pip

# Copy TorrentSlicer service code
WORKDIR /opt/al_service
COPY . .