# Backend deployment

Auto-deploy via GitHub Actions on every push to `main`.

## One-time GitHub Secrets to add

Repo → **Settings → Secrets and variables → Actions → New repository secret**

### SSH connection

| Secret | Value |
|---|---|
| `EC2_HOST` | `ec2-13-204-235-21.ap-south-1.compute.amazonaws.com` |
| `EC2_USER` | `ubuntu` |
| `EC2_SSH_KEY` | Contents of `/Users/hifsul/ssh/certify-u` (full private key, including `-----BEGIN ... -----END ...` lines) |
| `EC2_PORT` *(optional)* | `22` |

### Application secrets (written to `.env` on the server each deploy)

| Secret | Notes |
|---|---|
| `DJANGO_SECRET_KEY` | Generate with `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DB_PASSWORD` | Postgres password for `certifyuuser` |
| `AWS_ACCESS_KEY_ID` | S3 access key for the `certifyu` bucket |
| `AWS_SECRET_ACCESS_KEY` | S3 secret key |

### Application variables (non-secret — set under "Variables", not "Secrets")

| Variable | Default if unset | Notes |
|---|---|---|
| `DJANGO_DEBUG` | `False` | Set to `True` only on staging |
| `DJANGO_ALLOWED_HOSTS` | *(empty)* | Comma-separated, e.g. `api.certify-u.com,13.204.235.21` |
| `DB_NAME` | `certifyu` | |
| `DB_USER` | `certifyuuser` | |
| `DB_HOST` | `localhost` | |
| `DB_PORT` | *(empty → 5432)* | |
| `AWS_STORAGE_BUCKET_NAME` | `certifyu` | |

To copy the private key:
```bash
pbcopy < /Users/hifsul/ssh/certify-u
```
Then paste into the `EC2_SSH_KEY` secret field.

## One-time EC2 prep

SSH in once and prepare the box:

```bash
ssh -i "/Users/hifsul/ssh/certify-u" ubuntu@ec2-13-204-235-21.ap-south-1.compute.amazonaws.com

# Install system deps
sudo apt update
sudo apt install -y python3-venv python3-pip git build-essential libpq-dev nginx

# Allow ubuntu to restart the service without a password (so the workflow can do it)
echo 'ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl restart gunicorn' | sudo tee /etc/sudoers.d/ubuntu-gunicorn
sudo chmod 440 /etc/sudoers.d/ubuntu-gunicorn

# Create the deploy directory (the workflow will clone into it on first run)
sudo mkdir -p /home/ubuntu/certify-u-backend
sudo chown ubuntu:ubuntu /home/ubuntu/certify-u-backend
```

Then create a systemd service file `/etc/systemd/system/gunicorn.service`:

```ini
[Unit]
Description=Certify-U Gunicorn
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/certify-u-backend
ExecStart=/home/ubuntu/certify-u-backend/env/bin/gunicorn \
          --workers 3 --bind 127.0.0.1:8000 certifyu.wsgi:application
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn
```

Add `gunicorn` to `requirements.txt` if it isn't there yet.

Front the service with nginx (proxy `127.0.0.1:8000` to public 80/443).

## Workflow tunables

The workflow respects these env vars on the server, defaulted in the script:

- `APP_DIR` — clone path (default `/home/ubuntu/certify-u-backend`)
- `BRANCH`  — branch to deploy (default `main`)
- `VENV_DIR` — virtualenv path (default `$APP_DIR/env`)
- `SERVICE_NAME` — systemd unit (default `gunicorn`)

Override them in `.github/workflows/deploy.yml` if your layout differs.

## Security notes (IMPORTANT)

`certifyu/settings.py` currently contains hardcoded:
- `SECRET_KEY`
- `DATABASES['default']['PASSWORD']`
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

These will be committed to the repo. **Rotate them and load from environment variables before pushing if this repo is or could become public.**
