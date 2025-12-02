# Update Geo Container

Python container for updating geo files (geoip.dat, geosite.dat) in the 3x-ui container.

## Overview

This container runs a Python script that:
- Downloads geo files from GitHub releases
- Compares file sizes to determine if updates are needed
- Copies updated files into the 3x-ui container using Docker API
- Restarts xray process when files are updated

## Files

- `main.py` - Main Python script
- `Dockerfile` - Container image definition
- `requirements.txt` - Runtime dependencies
- `test_main.py` - Unit tests
- `test-requirements.txt` - Test dependencies

## Running Tests

Install test dependencies:
```bash
pip install -r test-requirements.txt
```

Run tests:
```bash
pytest test_main.py -v
```

Run tests with coverage:
```bash
pytest test_main.py --cov=main --cov-report=html
```

## Configuration

The script is configured via constants in `main.py`:
- `WORKDIR` - Directory for storing downloaded geo files (mounted from host)
- `APPDIR` - Target directory in 3x-ui container (`/app/bin`)
- `CONTAINER_NAME` - Docker container name (`3x-ui`)
- `PROCESS_NAME` - Xray process name (`xray-linux`)

## Geo Files

The script downloads 4 geo files:
1. `geoip.dat` from Loyalsoldier/v2ray-rules-dat
2. `geosite.dat` from Loyalsoldier/v2ray-rules-dat
3. `geoip_RU.dat` from runetfreedom/russia-v2ray-rules-dat
4. `geosite_RU.dat` from runetfreedom/russia-v2ray-rules-dat

## Usage

The container runs continuously, checking for updates every 6 hours. To run immediately:
```bash
docker-compose exec update-geo python main.py now
```

