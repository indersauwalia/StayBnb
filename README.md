# Elsewhere

A small, server-rendered property rental platform built with Django, SQLite, Django Templates, Bootstrap 5, and vanilla JavaScript.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Django Admin is at `/admin/`.

## Features

- Guest and host registration, login, logout, and profile management.
- Property creation, editing, deletion, amenities, and multiple image uploads for hosts.
- Location, property type, and nightly price filters.
- Date-based booking requests, overlap checks, host approval/cancellation, and guest dashboards.
- Reviews for confirmed bookings after checkout; one review per guest and property.
- Admin management for profiles, properties, property images, bookings, and reviews.

Listings without uploaded photos use a remote Unsplash image as a presentation fallback. Uploaded property images are served from the local `media/` directory while `DEBUG` is enabled.

## Before deployment

Set `DJANGO_SECRET_KEY` to a unique secret, set `DJANGO_DEBUG=false`, configure `DJANGO_ALLOWED_HOSTS` as a comma-separated list, use a production web server for static and uploaded media, and review the security settings for your hosting environment.
