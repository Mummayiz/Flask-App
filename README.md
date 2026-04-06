# Pulseboard

Pulseboard is a Flask-based productivity analytics platform that helps users track tasks, focus sessions, hobbies, calendar activity, and personal productivity trends. It also includes a separate admin workspace for platform-wide analytics and user monitoring.

## Highlights

- Flask + Jinja application
- JSON-based storage only
- No SQL database
- No API keys required
- Separate user and admin dashboards
- Offline AI coach with predefined guidance
- Chart.js analytics and activity heatmaps
- 1000+ seeded sample users for admin insights

## Features

### User workspace

- Register and log in
- Personal dashboard with charts and productivity score
- Task manager
- Focus session tracking
- Hobbies tracker
- Calendar planner
- Activity heatmap
- AI coach page

### Admin workspace

- Dedicated admin login
- Admin dashboard with:
  - top productive users
  - top active users
  - task completion rankings
  - average focus comparisons
  - daily active users
  - weekly productivity trend
  - task priority distribution
- Searchable user table
- Per-user detail page for:
  - tasks
  - focus sessions
  - hobbies
  - activity logs

## Productivity score

The app uses this formula:

```text
productivity_score =
(tasks_completed * 2) + (focus_minutes * 0.5) + (hobby_time * 0.2)
```

## Tech stack

- Python
- Flask
- HTML
- CSS
- JavaScript
- Chart.js
- JSON files for persistence

## Project structure

```text
productivity-analytics/
├── app.py
├── app/
├── static/
├── templates/
├── utils/
├── data/
└── seed_data.py
```

## Data files

Application data is stored in:

- `data/users.json`
- `data/tasks.json`
- `data/focus.json`
- `data/hobbies.json`
- `data/calendar_events.json`
- `data/activity_logs.json`
- `data/ai_data.json`

## Local setup

### 1. Open the project

```powershell
cd C:\Users\Lenovo\projects\productivity-analytics
```

### 2. Create or use the virtual environment

```powershell
.\.venv\Scripts\activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Run the app

```powershell
python app.py
```

## Local URLs

- User login: [http://127.0.0.1:5000/login](http://127.0.0.1:5000/login)
- Admin login: [http://127.0.0.1:5000/admin/login](http://127.0.0.1:5000/admin/login)
- Admin dashboard: [http://127.0.0.1:5000/admin/dashboard](http://127.0.0.1:5000/admin/dashboard)

## Admin credentials

```text
username: admin
password: admin123
```

## Seed demo data

To regenerate demo data:

```powershell
python seed_data.py
```

## Public sharing

If you want a temporary public URL with localtunnel:

```powershell
lt --port 5000 --local-host 127.0.0.1
```

Then open the generated URL with:

- `/login`
- `/admin/login`
- `/admin/dashboard`

## Notes

- This is a local development app.
- JSON files change when the app is used.
- Admin analytics use real stored data from the JSON files.
