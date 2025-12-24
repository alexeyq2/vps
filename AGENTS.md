<!-- Copied/created for AI coding agents: concise, actionable, repository-specific guidance. -->

# Copilot instructions for this repository

Purpose: help an AI coding agent be productive quickly by describing architecture, important files, developer workflows, and project-specific conventions.

- Big picture: This repo provisions a small VPS stack using Docker Compose: `certbot`, `geo-update`, `3x-ui` (xray UI), `nginx`, and `filebrowser`. Persistent runtime state lives in `srv/` (copy from `srv-default/`). The repo includes provisioning scripts (`setup-*.sh`, `update-*.sh`, `up.sh`, `down.sh`).

- Key components and where to look:
  - `geo-update/geo_update.py` — background updater that downloads geoip/geosite files and copies them into the running `3x-ui` container using the Docker API. Important constants: `WORKDIR`, `APPDIR`, `XRAY_CONTAINER_NAME`, `PROCESS_NAME` and the `GEO_FILES` list.
  - `certbot/` — python script `main.py` builds a container that runs `certbot` in a loop; it renders `cli.ini.template` via `envsubst` and uses the webroot at `/nginx/www/http`.
  - `docker-compose` configuration: `compose.yml` (root) defines service mounts and important volume mappings (notably `/var/run/docker.sock` mounts for `certbot` and `geo-update`).
  - `nginx` templates: `srv-default/nginx/etc/templates/*.template` are the canonical templates — the container mounts `./srv/nginx/etc/templates` and generates `*.conf` in `/etc/nginx/conf.d` on start.
  - `srv/` vs `srv-default/`: `srv/` is the production runtime data (certs, site files, configs). Never overwrite `srv/` in a running system; use `srv-default/` as a safe template when provisioning.

- Developer workflows and exact commands (follow these):
  - Provision machine and dependencies: `./setup-all.sh`
  - Initialize env and data: `cp .env-default .env` → edit `.env` (`VPS_DOMAIN`, `VPS_EMAIL`, `ACME_SERVER`, `SUBSCRIPTION_URL`) → `cp -r srv-default srv`
  - Start stack: `./up.sh` (uses `docker compose` under the hood). Stop: `./down.sh`. Logs: `./log.sh`.
  - Build specific images (local debugging): `docker build -t geo-update ./geo-update` and `docker build -t certbot ./certbot`.
  - Rebuild images and restart (update flow): `./down.sh && ./update-images.sh && ./up.sh`.
  - Force certbot to use production ACME: edit `.env` and run `./update.sh`; check `docker compose logs -f certbot` for renew output.

- Project-specific patterns and conventions (do not assume defaults):
  - Containers may access the host Docker daemon (`/var/run/docker.sock`). Functions use the Docker API (see `geo_update.copy_file_to_container`) instead of relying solely on `docker cp` or shell `docker` calls.
  - Geo update logic uses HTTP HEAD `Content-Length` to decide whether to download and compares binary sizes inside the container to decide whether to copy and then signals the xray process (via `kill $(pgrep xray-linux)`). When modifying this flow, preserve size-check + safe-copy + restart sequence.
  - `certbot/main.py` intentionally sleep/retry loops to avoid rapid restarts and rate-limits. Changes to certbot flow should respect these backoff rules.
  - Nginx uses template files under `srv/*/nginx/etc/templates` and writes final confs into `/etc/nginx/conf.d`. Logs are intentionally routed to stdout/stderr in templates.
  - Persisted files live under `srv/` and `_work/` or `_work/*` are ephemeral developer artifacts.

- Integration & safety notes for automated edits:
  - Avoid touching files under `srv/` unless the change is explicitly about config templates or documented migration steps. `srv/` contains certificates and user data.
  - When changing Docker compose mounts or service names, update references in `geo-update/geo_update.py` (`XRAY_CONTAINER_NAME`, `APPDIR`) and `compose.yml` consistently.
  - Tests and quick checks: there are simple tests in `geo-update/` (`run_test.py`, `test_geo_update.py`). Run them with `python3 geo-update/run_test.py` or `pytest geo-update` when present.

- Examples to cite when making code changes:
  - Copy-to-container pattern (uses tar + `container.put_archive`): see `geo-update/geo_update.py` `copy_file_to_container()` implementation.
  - Certbot orchestration: `certbot/main.py` uses `envsubst` for `cli.ini.template` and loops/retries `certbot certonly` then `certbot renew` with multi-hour sleep.
  - Nginx template example: `srv-default/nginx/etc/templates/default.conf.template` shows logging, webroot path, and inclusion of `ssl_server*.conf`.

- What the agent should do first (prioritized):
  1. Read `README.md` and `compose.yml` to understand service boundaries and mounts.
 2. Inspect `geo-update/geo_update.py` to preserve its size-check, copy, restart pattern if touching geo updates.
 3. When modifying runtime templates, update `srv-default/*` and test via `./down.sh && ./update-code-and-build.sh && ./up.sh` locally.

Ask the repo owner for clarification if any change touches `srv/` data, secret files, or live certificate flows.

If anything here is unclear or you want more details (example runs, tests to execute, or expanded description of `geo_update` internals), tell me which area to expand.

- Code comments
Все комментарии пишутся по-русски. Скрипты выводят сообщения и вопросы по-русски.
