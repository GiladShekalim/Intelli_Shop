# IntelliShop

IntelliShop is a web-based application that aggregates, enhances, stores, and serves discount/coupon data in one convinent platform for consumers. It integrates a Selenium scraping pipeline, an AI enhancement stage using the Groq API, MongoDB-backed models and queries, and a web UI for authentication, personalization, search/filtering, and favorites.

## 🟦 Quick start

### 1) Environment

Create a `.env` file at the repository root:

```
# MongoDB
MONGODB_URI=mongodb+srv://username:password@yourcluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_NAME=IntelliDB

# Django
SECRET_KEY=your-secret-key-here
DEBUG=True

# Groq API
GROQ_API_KEY=<your_api_key_here>
```

### 2) Run the setup menu

```bash
./WebpageTest/intelliShop.sh
```

Menu options:
- 1. Setup and start server
- 2. Data validation and insert → Setup and start server
- 3. AI enhancement → Data validation and insert → Setup and start server
- 4. Data scraping
- 5. Tests (pytest + JSON report → QA_Report.txt)

Access the application at `http://localhost:8000` after setup completes.

## 🟦 Features

- Personalized top-10 recommendations (favorites-weighted ranking)
- AI-powered enhancement and filter generation
- Multi-source scraping (HOT, Adif) to centralized data dir
- Import with schema validation and legacy mapping
- Search/filter scenarios: text-only, parameters-only, combined
- Favorites management

## 🟦 Technologies

- Backend: Django (Python 3)
- Database: MongoDB (primary), SQLite (Django sessions/admin)
- Frontend: Django templates, Bootstrap 5
- AI: Groq API (`groq` client)
- Scraping: Selenium, webdriver-manager
- Tooling: jsonschema, python-dateutil, flake8/black, pytest

## 🟦 System Architecture

Subsystems and purposes:

- Web application (Django): HTTP routing, views, templates, static assets, sessions/auth, personalization
- Data layer (MongoDB + SQLite for sessions/admin): schema validation, import/export, filtered queries
- Scraper (Selenium): multi-source scraping to JSON files
- AI enhancement (Groq): schema-constrained enrichment and normalization with fail and request handeling
- Validation: imports enhanced JSON into MongoDB with logging
- Orchestration: setup scripts, environment management, test discovery and QA report generation

## 🟦 Simplified Directory tree

```
WebpageTest/
  mysite/                      # Django project
    mysite/                    # Settings, URLs, WSGI/ASGI
    intellishop/               # App: views, models, utils, templates, static, commands, data
  scraper/                     # Standalone Selenium scraper
  unit_tests/                  # Test discovery + runner, QA artifacts
  build.sh, intelliShop.sh     # Orchestration & menu scripts
```

## 🟦 Main workflows

1) Scrape → Enhance → Import → Serve
- Scrape raw discounts to `WebpageTest/mysite/intellishop/data/*.json`
- Enhance with Groq to conform to a strict JSON schema and enrich fields
- Import enhanced data into MongoDB with validation and version control
- Serve through Django views: login, personalized top-10, search/filter, favorites

2) Personalization
- Results are ranked using favorites-based category/status weighting and capped to top-10

3) Search and filtering
- Three scenarios: text-only, parameters-only (statuses, interests, price/percentage), and combined

## 🟦 Subsystems and navigation

### Web application (Django)
- **App URLs:** [WebpageTest/mysite/intellishop/urls.py](WebpageTest/mysite/intellishop/urls.py)
  - Purpose: endpoints for home, auth, search/filter, favorites, AI helper
- **Views (main flows):** [WebpageTest/mysite/intellishop/views.py](WebpageTest/mysite/intellishop/views.py)
  - Purpose: login/register, personalized home (favorites-weighted top-10), search/filter, favorites CRUD

### Data layer (MongoDB)
- **Models and schema:** [WebpageTest/mysite/intellishop/models/mongodb_models.py](WebpageTest/mysite/intellishop/models/mongodb_models.py)
  - Purpose: `User`, `Coupon` schema, import helpers, and query APIs
  - **Main algorithms:**
    - `Coupon.get_filtered_coupons` (3 scenarios)
    - `Coupon._build_parameter_query` (status/category/price/percentage logic)

### Scraper (Selenium)
- **Entrypoint:** [WebpageTest/scraper/main.py](WebpageTest/scraper/main.py)
  - Purpose: orchestrate scraping sources, write JSON into app data dir
- **HOT scraper:** [WebpageTest/scraper/scrapers/hot_scraper.py](WebpageTest/scraper/scrapers/hot_scraper.py)
  - Purpose: extract discount items; detect external link vs. phone-only
- **Adif scraper:** [WebpageTest/scraper/scrapers/adif_scraper.py](WebpageTest/scraper/scrapers/adif_scraper.py)
  - Purpose: extract discount items from Adif portal

### AI enhancement (Groq)
- **Core enhancement:** [WebpageTest/mysite/groq_chat.py](WebpageTest/mysite/groq_chat.py)
  - Purpose: schema-bound enhancement; rate limiting and deduplication
- **Filter helper:** [WebpageTest/mysite/intellishop/utils/groq_helper.py](WebpageTest/mysite/intellishop/utils/groq_helper.py)
  - Purpose: derive filter parameters (statuses/interests/price/percentage bucket) from natural language

### Ingestion and validation
- **Database updater:** [WebpageTest/mysite/update_database.py](WebpageTest/mysite/update_database.py)
  - Purpose: scan data dir for `enhanced_*.json` and import via model API with logging

### Orchestration and tooling
- **Interactive menu:** [WebpageTest/intelliShop.sh](WebpageTest/intelliShop.sh)
  - Purpose: guided selections (setup, AI, scraping, tests)
- **Test runner + QA report:** [WebpageTest/unit_tests/Run_Test_scripts.py](WebpageTest/unit_tests/Run_Test_scripts.py)
  - Purpose: run pytest, produce JSON report and `QA_Report.txt`

## 🟦 Data schema (Coupon, key fields)

- `discount_id` (string), `title` (string), `description` (string)
- `price` (integer), `discount_type` (fixed_amount | percentage | buy_one_get_one | Cost)
- `image_link`, `discount_link`, `provider_link`, `terms_and_conditions`
- `club_name` (array[string])
- `category` (array[string]), `consumer_statuses` (array[string])
- `valid_until` (string), `usage_limit` (integer|null)

## 🟦 Endpoints

- User dashboard - `GET /home/`
- Authentication flows - `POST /login/`, `POST /register/`, `POST /logout/`
- Favorites - `GET /favorites/`, `POST /add_favorite/`, `POST /remove_favorite/`, `GET /check_favorite/<discount_id>/`
- Listing, filtering, search - `GET /show_all_discounts/`, `POST /filtered_discounts/`, `POST /search_discounts/`
- Generate filters from natural language - `POST /ai_filter_helper/`

## 🟦 Collaborators

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/GiladShekalim">
        <img src="https://github.com/GiladShekalim.png?size=120" width="120" height="120" alt="Gilad Shekalim" />
        <br />
        <sub><b>Gilad Shekalim</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/OrenGolov">
        <img src="https://github.com/OrenGolov.png?size=120" width="120" height="120" alt="Oren Golovchik" />
        <br />
        <sub><b>Oren Golovchik</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/ArielArviv">
        <img src="https://github.com/ArielArviv.png?size=120" width="120" height="120" alt="Ariel Arviv" />
        <br />
        <sub><b>Ariel Arviv</b></sub>
      </a>
    </td>
  </tr>
  </table>

