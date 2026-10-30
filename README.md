# VUKA Backend

## Overview

Vuka is a platform designed to help high-school graduates in Kenya turn educational social-media engagement into structured career and skills development. VUKA combines personalized onboarding, educational content discovery, AI-generated assessments, progress tracking, career opportunities, and graduate verification into a single backend platform.

This repository contains the **VUKA backend API**, built with **FastAPI**, **PostgreSQL**, and **SQLAlchemy**. It handles authentication, onboarding, content discovery, assessments, progress tracking, and opportunity recommendations.

## Key Features

* **User management** — Registration and authentication using email and password, with stateless session management for multi-device access.
* **Content pathways** — Uses site-restricted keyword searches to discover educational content and link users to relevant learning resources on TikTok and YouTube.
* **Verified assessments** — Provides dynamic quizzes and check-ins to verify learning before awarding progress points.
* **User progress tracking** — Tracks experience points (XP), assessment performance, and consecutive-day streaks.
* **Opportunity recommendations** — Connects users with relevant scholarships, bootcamps, and other career opportunities based on their progress and interests.

## Data Model

The database design is documented in the project's **ERD documentation** in `docs/`.

At a high level, the core tables are:

| Table                        | Purpose                                                                   |
| ---------------------------- | ------------------------------------------------------------------------- |
| `registration`               | Stores user account and authentication information.                       |
| `onboarding-assessment`      | Stores career interests, baseline skills, and preferred social platforms. |
| `content_pathway`            | Stores personalized educational content recommendations.                  |
| `verified_assessments`       | Stores assessment checkpoints, submissions, and results.                  |
| `user_progress`              | Tracks XP, progress, and daily streaks.                                   |
| `opportunity_recommendation` | Stores relevant scholarships, bootcamps, and career opportunities.        |

### Entity Relationships

* One **registration account** → one **onboarding assessment** (1:1)
* One **onboarding assessment** → many **content pathways** (1:N)
* One **registration account** → many **verified assessments** (1:N)
* One **content pathway** → many **verified assessments** (1:N)
* One **registration account** → many **user progress** records (1:N)
* One **registration account** → many **opportunity recommendations** (1:N)

## Tech Stack

* **Framework:** FastAPI (Python)
* **Database:** SQL / PostgreSQL
* **AI/ML:** Google Gemini for assessment generation and profile processing
* **External Services:** YouTube Data API v3 and Google Serper API for content and opportunity discovery

## Prerequisites

* Python 3.10+
* PostgreSQL or another supported SQL database
* `pip`
* Google Gemini API credentials
* Google Serper API credentials
* YouTube Data API credentials

## Installation

```bash
git clone git@github.com:akirachix/Vuka_Backend.git
cd Vuka_Backend

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

## Running the App

```bash
uvicorn main:vuka --reload
```

The API will be available at:

`http://localhost:8000`

Interactive API documentation:

`http://localhost:8000/docs`

## Environment Variables

| Variable         | Description                                    |
| ---------------- | ---------------------------------------------- |
| `DATABASE_URL`   | Connection string for the SQL database         |
| `SERPER_API_KEY` | Google Serper API key                          |
| `GEMINI_API_KEY` | Google Gemini API key                          |
| `SECRET_KEY`     | Secret key used for authentication and signing |

## Project Structure

```text
app/
├── main.py            # FastAPI application entrypoint
├── models/            # Database models
├── schemas/           # Pydantic request/response schemas
├── routers/           # API route definitions
├── services/          # Business logic and external integrations
└── core/              # Configuration, security, and database setup
```

## API Documentation

FastAPI provides interactive API documentation when the application is running:

* **Swagger UI:** `/docs`
* **ReDoc:** `/redoc`

## Contributing

1. Fork the repository.
2. Create a feature branch:

```bash
git checkout -b feature/your-feature
```

3. Make your changes and test them.
4. Commit with a clear message.
5. Open a pull request describing your changes.
