# Running the Django Dashboard Locally

This version uses Django templates. It runs the pages and JSON endpoints from one
Python server, so you only need one terminal.

The app requires an account. Every page and API endpoint is protected, and each
user's saved MySQL settings are private to that user.

## Install dependencies

Create and activate a virtual environment, then install the requirements:

```bash
cd "web-django"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The virtual environment and the install are one-time steps. Reactivate the
environment in each new terminal with `source .venv/bin/activate`, and reinstall
only when `requirements.txt` changes.

Confirm that the terminal is using the expected Python and Django installation:

```bash
which python
python --version
python -m django --version
```

## The credential encryption key

Saved MySQL credentials are encrypted before they are written to the local
database, so the database file on its own is not enough to steal them.

**In local development you do not have to do anything.** On first run the app
creates a key file at `web-django/.credential-key` and reuses it every time
afterwards, so a saved connection stays readable across restarts. The file is
git-ignored. Deleting it makes existing saved connections unreadable, and the
app says so plainly rather than failing silently.

Do not run `Fernet.generate_key()` on every start. A new key each session
orphans the credentials that were saved with the previous one.

For a real deployment, supply a stable key from a secret store instead. When
this variable is set it always wins over the local file:

```bash
export CREDENTIAL_ENCRYPTION_KEY='your-stored-fernet-key'
```

To mint a key once for that purpose:

```bash
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

## Create the local database

Run once, and again whenever models change:

```bash
python manage.py migrate
```

Create an administrator account for the Django admin site:

```bash
python manage.py createsuperuser
```

## Start the app

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000` in your browser. You are redirected to the login
page until you sign in.

## Sign in

1. Choose **Sign up** to create an account, or **Log in** if you already have one.
2. Passwords need at least 8 characters and cannot be all numbers.
3. After signing in you land on the Dashboard.
4. Use the top tabs for Dashboard, Auction, History, Inventory, and Model.
5. Use **Log out** in the header to end the session.

Passwords are stored as salted hashes, never as plain text.

## Connect to MySQL

1. Click **CONNECT TO DATABASE** inside the Most Profitable Products card.
2. Enter User, Password, Host, Port, and Database.
3. Click **SAVE AND VERIFY**.
4. The table loads after Django verifies the connection.

Settings are encrypted and stored against your account, so they are still there
after you log out and back in. Another user signing in to the same server cannot
read, overwrite, or delete them. The password is never sent back to the browser.
Use **REMOVE** to delete the saved connection.

When updating a saved connection, leave the password blank to keep the stored
one. This local prototype uses `mysql-connector-python` and does not require a
macOS ODBC driver.

## Django admin

Open `http://127.0.0.1:8000/admin/` and sign in with the superuser account to
manage users and sessions. Saved connections are listed for auditing and can be
deleted, but the stored credentials are never displayed in the admin.

## Run the tests

```bash
python manage.py test dashboard
```

## Deploying to the internal server

The client hosts this on their own machine on the internal network, reachable
over their VPN. Development defaults are deliberately convenient and are **not**
safe on that server, so configuration comes from a `.env` file there.

### 1. Configure

Copy the template and fill it in on the server:

```bash
cp .env.example .env
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Put that value in `DJANGO_SECRET_KEY`, set `DJANGO_DEBUG=false`, and put the
machine's internal address in `DJANGO_ALLOWED_HOSTS` and
`DJANGO_CSRF_TRUSTED_ORIGINS`. Keep `DJANGO_SECURE_COOKIES=false` while the site
is plain HTTP; turning it on without HTTPS stops logins from working.

Restrict the file, since it holds the key that unlocks saved credentials:

```bash
chmod 600 .env
```

### 2. Prepare

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
python manage.py check --deploy
```

`collectstatic` is required. With `DJANGO_DEBUG=false` Django stops serving
static files itself, and without this step the admin site loses all styling.

`check --deploy` should report only the four HTTPS warnings
(`W004`, `W008`, `W012`, `W016`). Those are expected on plain HTTP over a VPN.
Any other warning means something is misconfigured.

### 3. Run

Use gunicorn, not `runserver`. `runserver` is single-threaded, auto-reloads, and
is not built to stay up:

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 60
```

To keep it always on, run it under systemd with `Restart=always` so it comes
back after a crash or reboot.

### 4. Back up

Three things on the server matter. Losing either of the first two means every
saved database connection must be entered again:

- `.env` (or `.credential-key` if you did not set `CREDENTIAL_ENCRYPTION_KEY`)
- `db.sqlite3` — accounts and saved connections
- `logs/dashboard.log` — rotates automatically at 2 MB, five files kept

### What is still worth doing later

- **HTTPS.** Sessions and the database password travel in clear text over the
  VPN today. Putting a reverse proxy with TLS in front and then setting
  `DJANGO_SECURE_COOKIES=true` closes that.
- **SQLite limits.** Fine for a small purchasing team. If many people write at
  once, move Django's own storage to PostgreSQL. This is separate from the
  client MySQL database the dashboard reports on.

## Project layout

```
config/       Django project wiring: settings, root URLs, server entry points
dashboard/    the application
  urls.py       which URL runs which view
  views/        request handling (auth, pages, api) - no calculations
  services/     the work: saved connections, MySQL access, profitability, market
  models.py     database tables
  forms.py      input validation
  credentials.py  encryption of saved database credentials
  admin.py      Django admin configuration
  tests/        tests grouped by feature
templates/    the frontend HTML
```

Rule of thumb: `views/` decides what to send back, `services/` figures out the
answer, and `templates/` displays it.

## Check the project without starting the server

Run Django's configuration checks after changing Python, URL, or template files:

```bash
python manage.py check
```

Check that the main project files compile:

```bash
python -m compileall config dashboard manage.py
```

## Test the running endpoints

Start the server in one terminal:

```bash
python manage.py runserver 127.0.0.1:8000
```

In a second terminal, confirm that protected routes reject anonymous requests.
The dashboard redirects to the login page and the APIs return 401:

```bash
curl -i http://127.0.0.1:8000/
curl -i "http://127.0.0.1:8000/api/index-performance?start_date=2024-01-01&end_date=2024-01-31&ticker=SLX"
```

To call an endpoint as a signed-in user, log in with a cookie jar first. Replace
the placeholders with a test account, not a real client credential:

```bash
curl -s -c cookies.txt http://127.0.0.1:8000/login/ -o /dev/null
CSRF=$(awk '$6=="csrftoken" {print $7}' cookies.txt)
curl -s -b cookies.txt -c cookies.txt -X POST http://127.0.0.1:8000/login/ \
    -H "Referer: http://127.0.0.1:8000/login/" \
    -d "username=TEST_USER&password=TEST_PASSWORD&csrfmiddlewaretoken=$CSRF" -o /dev/null

curl -s -b cookies.txt "http://127.0.0.1:8000/api/index-performance?start_date=2024-01-01&end_date=2024-01-31&ticker=SLX"
curl -s -b cookies.txt http://127.0.0.1:8000/api/connection
curl -s -b cookies.txt http://127.0.0.1:8000/api/profitable-products
```

Delete the cookie jar when you are done, since it holds a live session:

```bash
rm -f cookies.txt
```

The database endpoints read the connection saved for the signed-in account, so
credentials no longer travel in each request body. Save them through the
dashboard UI rather than through a shell command, and never put real credentials
in this file, shell history, or a script.

Use `Ctrl+C` in the server terminal to stop the development server.

## Troubleshooting

If port 8000 is already in use, start Django on another port:

```bash
python manage.py runserver 8001
```

If the server will not start, check the configuration and installed packages:

```bash
python manage.py check
python -m pip check
```

If a dependency is missing, install it from the requirements file again:

```bash
python -m pip install -r requirements.txt
```

## Useful commands

```bash
# Check Django configuration
python manage.py check

# Run the test suite
python manage.py test dashboard

# Apply database migrations
python manage.py migrate

# Create a new migration after changing models
python manage.py makemigrations dashboard

# Create an administrator account
python manage.py createsuperuser

# Show the available management commands
python manage.py help

# Check installed package consistency
python -m pip check

# Stop the server
# Press Ctrl+C

# Use another port if 8000 is busy
python manage.py runserver 8001
```
