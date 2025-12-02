#!/usr/bin/env python3

import os
import sys
import time
import random
import argparse
import tarfile
import tempfile
import logging
from datetime import datetime
from pathlib import Path
import signal
import threading

import docker
import requests

# Configuration
WORKDIR = Path("/app/geo")     # Persistent volume mounted from host
APPDIR = "/app/bin"            # Target directory in 3x-ui container
XRAY_CONTAINER_NAME = "3x-ui"  # Docker compose service name
PROCESS_NAME = "xray-linux"    # Xray process name to signal

# Update scheduling
UPDATE_INTERVAL_HOURS = 18  # base interval in hours
UPDATE_INTERVAL = UPDATE_INTERVAL_HOURS * 60 * 60  # seconds
MAX_JITTER_SECONDS = 5 * 60  # add up to 5 minutes random jitter

# Geo file URLs and target filenames
GEO_FILES = [
    {
        "url": "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geoip.dat",
        "filename": "geoip.dat"
    },
    {
        "url": "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geosite.dat",
        "filename": "geosite.dat"
    },
    {
        "url": "https://github.com/runetfreedom/russia-v2ray-rules-dat/releases/latest/download/geoip.dat",
        "filename": "geoip_RU.dat"
    },
    {
        "url": "https://github.com/runetfreedom/russia-v2ray-rules-dat/releases/latest/download/geosite.dat",
        "filename": "geosite_RU.dat"
    }
]

_env_level = os.environ.get('LOG_LEVEL' , 'INFO').upper()
numeric_level = getattr(logging, _env_level, logging.DEBUG)  # debug if invalid
# logging.basicConfig(level=numeric_level, format='[%(asctime)s] %(levelname)s: %(message)s')
logging.basicConfig(level=numeric_level, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(numeric_level)

log = logger
docker_client = None
stop_event = threading.Event()

def _handle_termination(signum, frame):
    log.debug(f"Received signal {signum}, shutting down")
    stop_event.set()


def get_url_size(url):
    """Get file size from URL using HTTP HEAD request"""
    response = requests.head(url, allow_redirects=True, timeout=30)
    response.raise_for_status()
    content_length = response.headers.get('Content-Length')
    if not content_length:
        raise RuntimeError(f"No Content-Length header for {url}")
    return int(content_length)


def get_file_size(filepath):
    """Get local file size"""
    if filepath.exists():
        return filepath.stat().st_size
    return 0


def need_download(url, local_file):
    """Check if file needs to be downloaded by comparing sizes"""
    if not local_file.exists():
        log.info(f"{local_file.name} has not been downloaded yet")
        return True
    latest_size = get_url_size(url)
    existing_size = get_file_size(local_file)

    if latest_size != existing_size:
        log.info(f"{local_file.name} size has changed, '{latest_size}' != '{existing_size}'")
        return True

    return False


def download_file(url, filepath):
    """Download file from URL"""
    log.info(f"Downloading {filepath.name} from {url}")
    response = requests.get(url, allow_redirects=True, timeout=20, stream=True)
    response.raise_for_status()

    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    if get_file_size(filepath) == 0:
        raise RuntimeError(f"Downloaded file {filepath.name} is empty")

    log.debug(f"Downloaded {filepath.name} ({get_file_size(filepath)} bytes)")
    return True


def copy_file_to_container(container, local_file, remote_path):
    """Copy file to container using Docker API"""
    target_dir = os.path.dirname(remote_path)
    tar_path = None
    # Create a tar archive in a temporary file (file-based stream to minimize memory usage)
    tar_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.tar') as tar_file:
            tar_path = tar_file.name

            # Ensure target directory exists
            container.exec_run(f"mkdir -p {target_dir}", user="root")

            # Create tar archive
            with tarfile.open(name=tar_path, mode='w') as tar:
                tar.add(local_file, arcname=os.path.basename(remote_path))

        # Read the tar file and put archive into container
        with open(tar_path, 'rb') as f:
            result = container.put_archive(target_dir, f)
            if not result:
                raise RuntimeError(f"Failed to put archive into container for {local_file.name}")
            log.info(f"Copied {local_file.name} to {remote_path} in container")
        return True
    finally:
        # Clean up temporary tar file
        try:
            if tar_path:
                os.unlink(tar_path)
        except Exception:
            pass


def restart_xray(container):
    """Restart xray process by sending SIGTERM"""
    # Find xray-linux process in container
    exec_result = container.exec_run(
        f"pgrep {PROCESS_NAME}",
        user="root"
    )

    if exec_result.exit_code != 0:
        raise RuntimeError(f"No {PROCESS_NAME} process found in container")

    pid = exec_result.output.decode().strip()
    if not pid:
        raise RuntimeError(f"No {PROCESS_NAME} process found in container")

    log.info(f"Restarting xray pid={pid}")

    # Send SIGTERM to xray process
    exec_result = container.exec_run(
        f"kill {pid}",
        user="root"
    )

    if exec_result.exit_code == 0:
        log.debug(f"Sent SIGTERM to xray process {pid}")
        return True
    else:
        raise RuntimeError(f"Error sending signal to xray: {exec_result.output.decode()}")


def update_geo():
    """Main update function: find container by name, download and copy files."""

    n_downloads = 0
    updated_files = []

    for geo_file in GEO_FILES:
        url = geo_file["url"]
        filename = geo_file["filename"]
        local_file = WORKDIR / filename

        if need_download(url, local_file):
            download_file(url, local_file)
            n_downloads += 1
            updated_files.append((local_file, filename))
        else:
            log.info(f"{filename} is up-to-date")

    if n_downloads > 0:
        log.info(f"Geofiles are different, updating {n_downloads} file(s)")

        container = get_container(XRAY_CONTAINER_NAME)
        for local_file, filename in updated_files:
            remote_path = f"{APPDIR}/{filename}"
            copy_file_to_container(container, local_file, remote_path)

        restart_xray(container)
        return True

    return False



def get_container(container_name):
    """Get container by name using module-level `docker_client`"""
    assert docker_client is not None
    containers = docker_client.containers.list(filters={"name": container_name})
    if not containers:
        # No matching container found — signal this as an error
        raise RuntimeError(f"Container '{container_name}' not found")

    return containers[0]


def get_update_delay():
    """Return update delay in seconds: base UPDATE_INTERVAL plus random jitter up to MAX_JITTER_SECONDS."""
    jitter = random.randint(0, MAX_JITTER_SECONDS)
    total = UPDATE_INTERVAL + jitter
    log.debug(f"Computed next update delay: base={UPDATE_INTERVAL}s + jitter={jitter}s => {total}s")
    return total


def main():
    """Main loop"""
    log.info("START")
    signal.signal(signal.SIGTERM, _handle_termination)
    signal.signal(signal.SIGINT, _handle_termination)
    
    # Default: run immediately. Use --delay to sleep before first run.
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--delay", nargs='?', type=int, const=-1,
                        help="sleep before first run; provide a number in seconds or omit to sleep a random 10-60s")
    args, _ = parser.parse_known_args()

    if args.delay is None:
        log.info("Running immediately (default)")
    else:
        if args.delay == -1:
            delay = random.randint(10, 60)
        else:
            delay = max(0, args.delay)

        log.info(f"Begin geofiles update in {delay} seconds (delay requested)")
        if stop_event.wait(delay):
            log.info("Shutdown requested during initial delay")
            return

    WORKDIR.mkdir(parents=True, exist_ok=True)

    # Connect to Docker
    try:
        global docker_client
        docker_client = docker.from_env()
    except Exception as e:
        log.error(f"Error connecting to Docker: {e}")
        sys.exit(1)
    
    # Main update loop - run every UPDATE_INTERVAL (default 18 hours) plus small random jitter
    
    while True:
        start_time = time.time()
        
        # Update geo files
        try:
            # update_geo will use the module-level docker_client
            result = update_geo()
            elapsed = int(time.time() - start_time)
            log.info(f"Geofiles update OK in {elapsed} sec")
        except Exception as e:
            log.exception("Error during update", exc_info=e)
        
        # Wait for next update (UPDATE_INTERVAL hours + jitter)
        update_interval = get_update_delay()
        log.debug(f"Next update in {update_interval // 3600} hours (+ jitter)")
        if stop_event.wait(update_interval):
            log.info("Shutdown requested during update interval")
            break

    log.info("STOP")


if __name__ == "__main__":
    main()

