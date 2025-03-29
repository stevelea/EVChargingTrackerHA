ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.11

FROM ${BUILD_FROM}

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install requirements for add-on
RUN \
    apk add --no-cache --virtual .build-dependencies \
        build-base \
        python3-dev \
        py3-pip \
        jpeg-dev \
        zlib-dev \
        libffi-dev \
        tesseract-ocr-dev \
    && apk add --no-cache \
        tesseract-ocr \
        poppler-utils \
        jq \
        cairo-dev \
        pango-dev \
        gdk-pixbuf-dev \
    && pip3 install --upgrade pip wheel

# Copy requirements file
COPY requirements.txt /tmp/

# Install Python requirements
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Copy root file system
COPY rootfs /

# Copy app files
WORKDIR /app
COPY app/ .

# Make run script executable
RUN chmod a+x /etc/services.d/evcharging_tracker/run

# Build arguments
ARG BUILD_ARCH
ARG BUILD_DATE
ARG BUILD_DESCRIPTION
ARG BUILD_NAME
ARG BUILD_REF
ARG BUILD_REPOSITORY
ARG BUILD_VERSION

# Labels
LABEL \
    io.hass.name="${BUILD_NAME}" \
    io.hass.description="${BUILD_DESCRIPTION}" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version=${BUILD_VERSION} \
    maintainer="EV Charging Tracker Team" \
    org.opencontainers.image.title="${BUILD_NAME}" \
    org.opencontainers.image.description="${BUILD_DESCRIPTION}" \
    org.opencontainers.image.vendor="Home Assistant Add-ons" \
    org.opencontainers.image.authors="EV Charging Tracker Team" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.url="https://github.com/basnijholt/addon-ev-charging-tracker" \
    org.opencontainers.image.source="https://github.com/${BUILD_REPOSITORY}" \
    org.opencontainers.image.documentation="https://github.com/${BUILD_REPOSITORY}/blob/main/README.md" \
    org.opencontainers.image.created=${BUILD_DATE} \
    org.opencontainers.image.revision=${BUILD_REF} \
    org.opencontainers.image.version=${BUILD_VERSION}