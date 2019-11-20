FROM cccs/assemblyline-v4-service-base:latest

ENV SERVICE_PATH torrentslicer.TorrentSlicer

RUN pip install \
  bencode.py \
  bitmath

# Switch to assemblyline user
USER assemblyline

# Copy TorrentSlicer service code
WORKDIR /opt/al_service
COPY . .