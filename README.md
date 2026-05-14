# AI News Aggregator - Live Build Repository

This repository accompanies my 3-hour live coding session where I build a complete AI-powered news aggregator from scratch. This is a **private repository** containing valuable implementation details and deployment strategies used in production environments.

## End-to-End Setup Guide

Follow these instructions to configure, install, and run the application locally.

### Prerequisites

1. **Python 3.12+**: Ensure Python is installed.
2. **PostgreSQL**: The app uses PostgreSQL. You can run it natively or via Docker. 
   - *Docker Desktop* (Recommended): You need Docker installed to use the included `docker-compose.yml`.
3. **uv** (Optional but recommended): A fast Python package installer and resolver. Install via `pip install uv`.

### 1. Environment Variables Configuration

1. A `.env.example` file has been provided in the root directory.
2. Copy it to create your own `.env` file (if you haven't already):
   ```bash
   cp .env.example .env
   ```
3. Open the `.env` file and populate it:
   - `OPENAI_API_KEY`: Get this from your OpenAI platform dashboard.
   - `MY_EMAIL`: Your email address for sending digests.
   - `APP_PASSWORD`: If using Gmail, you must generate an [App Password](https://myaccount.google.com/apppasswords).
   - `POSTGRES_*`: Leave as defaults if using the provided Docker setup.

### 2. Database Setup

If you have Docker Desktop installed, you can spin up the required PostgreSQL instance:
```bash
cd docker
docker-compose up -d
cd ..
```
This will start a PostgreSQL container named `ai-news-aggregator-db` running on port `5432` with the credentials matching the default `.env`. If you prefer a native installation, ensure you have a database matching the `.env` details.

### 3. Install Dependencies & Activate Environment

**Using `uv` (Recommended for speed):**
*Note: If `uv` is not recognized globally, prefix commands with `python -m uv`.*
```bash
pip install uv
python -m uv venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

python -m uv sync
```

**Using standard `pip`:**
```bash
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

pip install -e .
```

### 4. Initialize the Database

Once the database is running and dependencies are installed, create the necessary tables:
```bash
python app/database/create_tables.py
```
*Expected Output: `Tables created successfully`*

### 5. Running the Application

There are two ways to run the application:

**Option A: Command Line Interface (CLI)**
You can run the main aggregator pipeline directly:
```bash
python main.py
```
*Note: You can also pass custom arguments: `python main.py [HOURS] [TOP_N]` (e.g. `python main.py 24 10`)*

**Option B: Web UI (FastAPI)**
We have built a beautiful frontend UI that connects to a FastAPI backend. This allows you to view scraped articles and trigger the pipeline from your browser.
To start the API server, run:
```bash
python -m uvicorn app.api:app --reload
```
*(If you are using uv and the environment is not activated, you can also use `python -m uv run uvicorn app.api:app --reload`)*

Then, open your browser and navigate to `http://localhost:8000`.

The Web UI now opens with signup/login. Create an account with an email ID, username, and password before using the dashboard. See `AUTHENTICATION.md` for the implementation details behind signup, login, logout, and session management.

The pipeline will:
1. Scrape articles from configured sources (YouTube channels, OpenAI blog, Anthropic blog).
2. Process the markdown and transcripts using AI.
3. Create personalized summaries and digests for the articles.
4. Generate and send an email digest to your configured email address.

---

## Project Structure

This project is organized across three branches, each corresponding to a different phase of the build:

- **`master`** - Part 1: Local setup and core functionality
- **`deployment`** - Part 2: Deployment configuration and infrastructure
- **`deployment-final`** - Part 3: Final optimizations and production-ready changes

Each branch serves as an intermediate checkpoint, allowing you to reference the exact state of the codebase at any point during the video.

## How This Video Works

This is a **live coding build**, not a traditional step-by-step tutorial. Here's what to expect:

- **Fast-paced development** - I code at my natural pace, leveraging AI tools extensively
- **AI-assisted workflow** - You won't see every code snippet or file generation in real-time
- **Real-world approach** - This condenses 20-40 hours of learning into a single session
- **Not cookie-cutter** - Unlike structured tutorials, this reflects how coding actually happens in practice

## How to Follow Along

### Recommended Approach (Maximum Learning)

1. **Clone this repository** before starting the video
2. **Keep a local copy ready** on your system as you code along
3. **Use intermediate checkpoints** - When I make major updates or run tests, pause and:
   - Reference the corresponding branch in this repository
   - Copy relevant code snippets into your project
   - Use AI coding assistants to help you reach the same checkpoint
4. **Iterate step-by-step** - Don't rush ahead. Ensure each phase works before moving forward
5. **Expect confusion** - Some parts will move fast and may not be immediately clear. This is where real learning happens

### Alternative Approach (Not Recommended)

You can skip ahead to the `deployment-final` branch and try to get everything working, but you'll miss the iterative problem-solving process that makes this valuable.

## Why This Approach?

Traditional tutorials show you the "right way" to do things. This video shows you the **real way** - with AI assistance, rapid iteration, debugging, and adapting on the fly. By following along and hitting the same checkpoints, you'll:

- Learn how to effectively leverage AI coding tools
- Understand the thought process behind architectural decisions
- Experience real-world development workflows
- Build muscle memory through hands-on practice

**The most valuable learning happens when you struggle, reference the code, and push through to the next checkpoint.**
