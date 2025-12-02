#!/usr/bin/env python3

import os
import sys
import time
import random
import argparse
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path
import signal
import threading

import docker
import requests


# Configuration
WORKDIR = Path("/app/geo")  # Persistent volume mounted from host
APPDIR = "/app/bin"  # Target directory in 3x-ui container
XRAY_CONTAINER_NAME = "3x-ui"  # Docker compose service name
PROCESS_NAME = "xray-linux"  # Xray process name to signal

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


def log(message):
    """Log message with timestamp to stdout"""
    print(f"[{datetime.now()}] {message}", flush=True)

# shutdown event set by signal handler
stop_event = threading.Event()


def _handle_termination(signum, frame):
    log(f"Received signal {signum}, shutting down")
    stop_event.set()


def get_url_size(url):
    """Get file size from URL using HTTP HEAD request"""
    try:
        response = requests.head(url, allow_redirects=True, timeout=30)
        response.raise_for_status()
        content_length = response.headers.get('Content-Length')
        if content_length:
            return int(content_length)
        return None
    except Exception as e:
        log(f"Error getting size for {url}: {e}")
        return None


def get_file_size(filepath):
    """Get local file size"""
    if filepath.exists():
        return filepath.stat().st_size
    return 0


def need_download(url, local_file):
    """Check if file needs to be downloaded by comparing sizes"""
    if not local_file.exists():
        log(f"{local_file.name} has not been downloaded yet")
        return True
    
    latest_size = get_url_size(url)
    if latest_size is None:
        log(f"Could not determine remote size for {url}, skipping")
        return False
    
    existing_size = get_file_size(local_file)
    
    if latest_size != existing_size:
        log(f"{local_file.name} size has changed, '{latest_size}' != '{existing_size}'")
        return True
    
    return False


def download_file(url, filepath):
    """Download file from URL"""
    try:
        log(f"Downloading {filepath.name} from {url}")
        response = requests.get(url, allow_redirects=True, timeout=60, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        if get_file_size(filepath) == 0:
            log(f"Error: Downloaded file {filepath.name} is empty")
            return False
        
        log(f"Downloaded {filepath.name} ({get_file_size(filepath)} bytes)")
        return True
    except Exception as e:
        log(f"Error downloading {url}: {e}")
        return False


def copy_file_to_container(container, local_file, remote_path):
    """Copy file to container using Docker API"""
    target_dir = os.path.dirname(remote_path)
    tar_path = None
    
    # Create a tar archive in a temporary file (file-based stream to minimize memory usage)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.tar') as tar_file:
        try:
            tar_path = tar_file.name
            
            # Ensure target directory exists
            container.exec_run(f"mkdir -p {target_dir}", user="root")
            
            # Create tar archive
            tar = tarfile.open(name=tar_path, mode='w')
            tar.add(local_file, arcname=os.path.basename(remote_path))
            tar.close()
            
            # Read the tar file and put archive into container
            with open(tar_path, 'rb') as f:
                container.put_archive(target_dir, f)
            
            log(f"Copied {local_file.name} to {remote_path} in container")
            return True
        except Exception as e:
            log(f"Error copying {local_file.name} to container: {e}")
            return False
        finally:
            # Clean up temporary tar file
            try:
                os.unlink(tar_path)
            except Exception:
                pass


def restart_xray(container):
    """Restart xray process by sending SIGTERM"""
    try:
        # Find xray-linux process in container
        exec_result = container.exec_run(
            f"pgrep {PROCESS_NAME}",
            user="root"
        )
        
        if exec_result.exit_code != 0:
            log(f"No {PROCESS_NAME} process found, skip restart")
            return False
        
        pid = exec_result.output.decode().strip()
        if not pid:
            log(f"No {PROCESS_NAME} process found, skip restart")
            return False
        
        log(f"Restarting xray pid={pid}")
        
        # Send SIGTERM to xray process
        exec_result = container.exec_run(
            f"kill {pid}",
            user="root"
        )
        
        if exec_result.exit_code == 0:
            log(f"Sent SIGTERM to xray process {pid}")
            return True
        else:
            log(f"Error sending signal to xray: {exec_result.output.decode()}")
            return False
            
    except Exception as e:
        log(f"Error restarting xray: {e}")
        return False


def update_geo(docker_client):
    """Main update function: find container by name, download and copy files."""
    WORKDIR.mkdir(parents=True, exist_ok=True)

    container = get_container(docker_client, XRAY_CONTAINER_NAME)
    if container is None:
        log(f"Container '{XRAY_CONTAINER_NAME}' not available")
        return None

    n_downloads = 0
    updated_files = []

    for geo_file in GEO_FILES:
        url = geo_file["url"]
        filename = geo_file["filename"]
        local_file = WORKDIR / filename

        if need_download(url, local_file):
            if download_file(url, local_file):
                n_downloads += 1
                updated_files.append((local_file, filename))
            else:
                log(f"Failed to download {filename}")
        else:
            log(f"{filename} is up-to-date")

    if n_downloads > 0:
        log(f"Geofiles are different, updating {n_downloads} file(s)")

        for local_file, filename in updated_files:
            remote_path = f"{APPDIR}/{filename}"
            if not copy_file_to_container(container, local_file, remote_path):
                log(f"Failed to copy {filename} to container")
                return False

        restart_xray(container)
        return True

    return False


def get_container(docker_client, container_name):
    """Get container by name"""
    try:
        containers = docker_client.containers.list(filters={"name": container_name})
        if containers:
            return containers[0]
        log(f"Container '{container_name}' not found")
        return None
    except Exception as e:
        log(f"Error finding container '{container_name}': {e}")
        return None


def get_update_delay():
    """Return update delay in seconds: base UPDATE_INTERVAL plus random jitter up to MAX_JITTER_SECONDS."""
    jitter = random.randint(0, MAX_JITTER_SECONDS)
    total = UPDATE_INTERVAL + jitter
    log(f"Computed next update delay: base={UPDATE_INTERVAL}s + jitter={jitter}s => {total}s")
    return total


def main():
    """Main loop"""
    log("START")
    signal.signal(signal.SIGTERM, _handle_termination)
    signal.signal(signal.SIGINT, _handle_termination)
    
    # Default: run immediately. Use --delay to sleep before first run.
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--delay", nargs='?', type=int, const=-1,
                        help="sleep before first run; provide a number in seconds or omit to sleep a random 10-60s")
    args, _ = parser.parse_known_args()

    if args.delay is None:
        log("Running immediately (default)")
    else:
        if args.delay == -1:
            delay = random.randint(10, 60)
        else:
            delay = max(0, args.delay)

        log(f"Begin geofiles update in {delay} seconds (delay requested)")
        if stop_event.wait(delay):
            log("Shutdown requested during initial delay")
            return
    
    # Connect to Docker
    try:
        docker_client = docker.from_env()
    except Exception as e:
        log(f"Error connecting to Docker: {e}")
        sys.exit(1)
    
    # Main update loop - run every UPDATE_INTERVAL (default 18 hours) plus small random jitter
    
    while True:
        start_time = time.time()
        
        # Get 3x-ui container
        container = get_container(docker_client, XRAY_CONTAINER_NAME)
        if container is None:
            log(f"Container '{XRAY_CONTAINER_NAME}' not available, waiting...")
            if stop_event.wait(60):
                log("Shutdown requested while waiting for container")
                break
            continue
        
        # Update geo files
        try:
            update_geo(docker_client, container)
            elapsed = int(time.time() - start_time)
            log(f"Geofiles update OK in {elapsed} sec")
        except Exception as e:
            log(f"Error during update: {e}")
        
        # Wait for next update (UPDATE_INTERVAL hours + jitter)
        update_interval = get_update_delay()
        log(f"Next update in {update_interval // 3600} hours (+ jitter)")
        if stop_event.wait(update_interval):
            log("Shutdown requested during update interval")
            break

    log("STOP")


if __name__ == "__main__":
    main()

