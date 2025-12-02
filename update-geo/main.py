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

import docker
import requests


# Configuration
WORKDIR = Path("/app/geo")  # Persistent volume mounted from host
APPDIR = "/app/bin"  # Target directory in 3x-ui container
CONTAINER_NAME = "3x-ui"  # Docker compose service name
PROCESS_NAME = "xray-linux"  # Xray process name to signal

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


def update_geo(docker_client, container):
    """Main update function"""
    WORKDIR.mkdir(parents=True, exist_ok=True)
    
    n_downloads = 0
    updated_files = []
    
    # Download files that need updating
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
    
    # Copy updated files to container and restart xray if needed
    if n_downloads > 0:
        log(f"Geofiles are different, updating {n_downloads} file(s)")
        
        # Copy all updated files to container
        for local_file, filename in updated_files:
            remote_path = f"{APPDIR}/{filename}"
            if not copy_file_to_container(container, local_file, remote_path):
                log(f"Failed to copy {filename} to container")
                return False
        
        # Restart xray to pick up new geo files
        # Note: Xray-core does not automatically reload geo files,
        # so we need to restart the process
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


def main():
    """Main loop"""
    log("START")
    
    # Default: run immediately. Use --delay to sleep before first run.
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--delay", nargs='?', type=int, const=-1,
                        help="sleep before first run; provide a number in seconds or omit to sleep a random 10-60s")
    # parse known args only so other positional args are preserved if used elsewhere
    args, _ = parser.parse_known_args()

    if args.delay is None:
        log("Running immediately (default)")
    else:
        # If user provided --delay without value (const == -1), pick random 10-60
        if args.delay == -1:
            delay = random.randint(10, 60)
        else:
            # use provided numeric value, but clamp to sensible range (>=0)
            delay = max(0, args.delay)

        log(f"Begin geofiles update in {delay} seconds (delay requested)")
        time.sleep(delay)
    
    # Connect to Docker
    try:
        docker_client = docker.from_env()
    except Exception as e:
        log(f"Error connecting to Docker: {e}")
        sys.exit(1)
    
    # Main update loop - run every 6 hours
    seconds_in_hour = 60 * 60
    update_interval = 6 * seconds_in_hour
    
    while True:
        start_time = time.time()
        
        # Get 3x-ui container
        container = get_container(docker_client, CONTAINER_NAME)
        if container is None:
            log(f"Container '{CONTAINER_NAME}' not available, waiting...")
            time.sleep(60)  # Wait 1 minute before retrying
            continue
        
        # Update geo files
        try:
            update_geo(docker_client, container)
            elapsed = int(time.time() - start_time)
            log(f"Geofiles update OK in {elapsed} sec")
        except Exception as e:
            log(f"Error during update: {e}")
        
        # Wait for next update (6 hours)
        log(f"Next update in {update_interval // 3600} hours")
        time.sleep(update_interval)


if __name__ == "__main__":
    main()

