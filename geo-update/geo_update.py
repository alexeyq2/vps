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
from typing import Iterator

import docker
import requests

# Configuration
WORKDIR = Path("/app/geo")     # Persistent volume mounted from host
APPDIR = Path("/app/bin")      # Target directory in 3x-ui container
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
logging.basicConfig(level=numeric_level, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(numeric_level)

log = logger
docker_client = None

def iter_geo_files() -> Iterator[tuple[str, str]]:
    """Generator yielding (url, filename) tuples from GEO_FILES."""
    for geo_file in GEO_FILES:
        yield geo_file["url"], geo_file["filename"]


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
        for chunk in response.iter_content(chunk_size=1024*1024):
            f.write(chunk)

    if get_file_size(filepath) == 0:
        raise RuntimeError(f"Downloaded file {filepath.name} is empty")

    log.debug(f"Downloaded {filepath.name} ({get_file_size(filepath)} bytes)")


def copy_file_to_container(container, local_file, remote_path):
    """Copy file to container using Docker API"""
    target_dir = os.path.dirname(remote_path)
    tar_path = None
    try:
        # Create tar archive        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.tar') as tar_file:
            tar_path = tar_file.name
            with tarfile.open(name=tar_path, mode='w') as tar:
                tar.add(local_file, arcname=os.path.basename(remote_path))

        # Put the archive into container
        with open(tar_path, 'rb') as f:
            container.exec_run(f"mkdir -p {target_dir}", user="root")
            result = container.put_archive(target_dir, f)
            if not result:
                raise RuntimeError(f"Failed to copy to container: {local_file.name}")
            log.debug(f"Copied {local_file.name} to {remote_path} in container")
    finally:
        try:
            if tar_path:
                os.unlink(tar_path)
        except Exception:
            pass


def restart_xray(container):
    """Restart xray process by sending SIGTERM"""
    
    r = container.exec_run(f"sh -c 'kill $(pgrep {PROCESS_NAME})'", user="root")
    if not r.exit_code == 0:
        raise RuntimeError(f"Error sending restart signal to {PROCESS_NAME}: {r.output.decode()}")
    else:
        log.info(f"Signaled {PROCESS_NAME} to restart")

def get_container_file_size(container, path):
    """Return file size in bytes for a path inside container, or 0 if missing."""
    cmd = f"stat -c %s {path}"
    r = container.exec_run(cmd, user="root")
    if r.exit_code != 0:
        return 0
    out = r.output.decode().strip()
    return int(out)


def geo_update():
    """Main update function: find container by name, download and copy files."""

    for url, filename in iter_geo_files():
        local_file = WORKDIR / filename
        if need_download(url, local_file):
            download_file(url, local_file)
        else:
            log.info(f"{filename} is up-to-date ({local_file})")

    copied_any = False
    container = get_container(XRAY_CONTAINER_NAME)

    # Always check all files to handle the case when some files were downloaded but 
    # not copied for some reason (e.g. xray container was stopped)
    for url, filename in iter_geo_files():
        local_file = WORKDIR / filename
        local_size = get_file_size(local_file)
        
        container_file = APPDIR / filename;
        container_size = get_container_file_size(container, container_file)
        
        if local_size != container_size:
            log.info(f"Copy {filename} to container. sizes: local={local_size} container={container_size}")
            copy_file_to_container(container, local_file, container_file)
            copied_any = True
        else:
            log.debug(f"{filename} in container is up-to-date (size {local_size})")

    if copied_any:
        restart_xray(container)
        return True

    return False


def get_container(container_name):
    """Get container by name using module-level `docker_client`"""
    assert docker_client is not None
    containers = docker_client.containers.list(filters={"name": container_name})
    if not containers:
        raise RuntimeError(f"Container '{container_name}' not found")

    return containers[0]


def get_update_delay():
    """Return update delay in seconds: base UPDATE_INTERVAL plus random jitter up to MAX_JITTER_SECONDS."""
    jitter = random.randint(0, MAX_JITTER_SECONDS)
    total = UPDATE_INTERVAL + jitter
    log.debug(f"Computed next update delay: base={UPDATE_INTERVAL}s + jitter={jitter}s => {total}s")
    return total


def initial_delay():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--delay", nargs='?', type=int, const=-1,
                        help="sleep before first run; provide a number in seconds or omit to sleep a random 10-60s")
    args, _ = parser.parse_known_args()

    if args.delay is None:
        log.info("Begin geofiles update")
    else:
        if args.delay == -1:
            delay = random.randint(10, 60)
        else:
            delay = max(0, args.delay)

        log.info(f"Begin geofiles update in {delay} seconds")
        time.sleep(delay)
    
def main():
    """Main loop"""
    log.info("START")
    signal.signal(signal.SIGTERM, _handle_termination)
    signal.signal(signal.SIGINT, _handle_termination)
    WORKDIR.mkdir(parents=True, exist_ok=True)

    global docker_client
    docker_client = docker.from_env()

    initial_delay()

    while True:
        start_time = time.time()
        try:
            geo_update()
            elapsed = int(time.time() - start_time)
            log.info(f"Geofiles update OK in {elapsed} sec")
        except Exception as e:
            log.exception("Error during update", exc_info=e)
        
        update_interval = get_update_delay()
        log.info(f"Next update in {update_interval // 3600} hours")
        time.sleep(update_interval)

def _handle_termination(signum, frame):
  os._exit(2)

if __name__ == "__main__":
    main()

