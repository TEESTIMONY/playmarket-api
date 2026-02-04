# PlayMarket API

A Django REST API for managing bounties and user coin transactions.

## Features

- **Bounty Management**: Create, manage, and track bounties with coin rewards
- **User Profiles**: User coin balance tracking and transaction history
- **Redeem Codes**: Generate and redeem codes for coin rewards
- **RESTful API**: Full REST API with authentication and pagination
- **Production Ready**: Configured for deployment on Render with PostgreSQL

## Local Development

### Prerequisites

- Python 3.8+
- pip

### Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Copy `.env.example` to `.env` and configure your settings:
   ```bash
   cp .env.example .env
   ```

4. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start the development server**
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://localhost:8000`

## API Endpoints

### Bounties
- `GET /bounties/` - List all bounties
- `POST /bounties/` - Create a new bounty
- `GET /bounties/{id}/` - Get bounty details
- `PUT /bounties/{id}/` - Update a bounty
- `DELETE /bounties/{id}/` - Delete a bounty

### Bounty Claims
- `GET /bounties/{id}/claims/` - List claims for a bounty
- `POST /bounties/{id}/claims/` - Submit a claim
- `PUT /bounties/{id}/claims/{claim_id}/` - Update claim status

### Redeem Codes
- `POST /redeem/` - Redeem a code for coins

### User Profile
- `GET /profile/` - Get user profile and coin balance
- `GET /transactions/` - Get user transaction history

## Deployment to Render

This project is configured for easy deployment to [Render](https://render.com).

### Automatic Deployment

1. **Push to Git repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin <your-git-repo-url>
   git push -u origin main
   ```

2. **Connect to Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Create a new **Web Service**
   - Connect your Git repository
   - Use these settings:
     - **Environment**: Python
     - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
     - **Start Command**: `gunicorn playmarket.wsgi:application`

3. **Add PostgreSQL Database**
   - In Render dashboard, create a new **PostgreSQL** database
   - Name it `playmarket-db` (or update `render.yaml` if different)

4. **Environment Variables**
   Add these environment variables in Render dashboard:
   - `DEBUG`: `false`
   - `SECRET_KEY`: [Generate a secure key]
   - `ALLOWED_HOSTS`: `.onrender.com`
   - `CORS_ALLOWED_ORIGINS`: [Your frontend domain, e.g., `https://your-frontend.onrender.com`]
   - `DATABASE_URL`: [Render will auto-populate this]

5. **Deploy**
   - Render will automatically deploy your application
   - The first deployment will run migrations automatically

### Manual Deployment

You can also use the provided deployment script:
```bash
./deploy.sh
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `True` |
| `SECRET_KEY` | Django secret key | Development key |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1` |
| `DATABASE_URL` | Database connection string | SQLite for local |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed CORS origins | Local development origins |

## Project Structure

```
backend/
├── playmarket/          # Django project settings
├── bounties/            # Django app with models and API
├── requirements.txt     # Python dependencies
├── render.yaml         # Render deployment configuration
├── Procfile           # Process definition for Render
├── deploy.sh          # Deployment script
└── README.md          # This file
```

## Technologies

- **Django 6.0.1** - Web framework
- **Django REST Framework 3.16.1** - API framework
- **PostgreSQL** - Production database
- **SQLite** - Development database
- **Gunicorn** - WSGI server
- **dj-database-url** - Database configuration
- **python-dotenv** - Environment variables

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

For deployment issues or questions, please check the [Render Documentation](https://render.com/docs) or create an issue in this repository.