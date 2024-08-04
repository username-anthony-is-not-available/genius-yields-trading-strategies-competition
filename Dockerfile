# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.12.3
FROM python:${PYTHON_VERSION}-slim as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    dos2unix \
    --no-install-recommends

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

# Copy the source code into the container.
COPY *.py .
COPY strategies/* strategies/
COPY bot-api.yaml .
COPY requirements.txt .
COPY .flaskenv .

# Copy the bash scripts into the container.
COPY *.sh .
RUN dos2unix *.sh
RUN chmod +x *.sh

RUN /bin/bash -c /app/generate_client.sh

# Expose the port that the application listens on.
EXPOSE 8080

# Switch to the non-privileged user to run the application.
USER appuser

# Run the application.
ENTRYPOINT ["/bin/bash", "./start.sh"]
