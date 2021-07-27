ARG branch=latest
FROM cccs/assemblyline-v4-service-base:$branch

ENV SERVICE_PATH torrentslicer.TorrentSlicer

# Switch to assemblyline user
USER assemblyline

RUN pip install --no-cache-dir --user \
  bencode.py \
  bitmath  && rm -rf ~/.cache/pip

# Copy TorrentSlicer service code
WORKDIR /opt/al_service
COPY . .

# Patch version in manifest
ARG version=4.0.0.dev1
USER root
RUN sed -i -e "s/\$SERVICE_TAG/$version/g" service_manifest.yml

# Switch to assemblyline user
USER assemblyline