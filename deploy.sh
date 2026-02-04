#!/bin/bash

# Deployment script for Render
echo "Starting deployment setup for Render..."

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser (optional, for admin access)
echo "Creating superuser..."
python manage.py createsuperuser

echo "Deployment setup complete!"
echo ""
echo "To deploy to Render:"
echo "1. Push your code to a Git repository (GitHub, GitLab, etc.)"
echo "2. Go to https://dashboard.render.com/"
echo "3. Create a new Web Service and connect your repository"
echo "4. Use the following settings:"
echo "   - Environment: Python"
echo "   - Build Command: pip install -r requirements.txt && python manage.py collectstatic --noinput"
echo "   - Start Command: gunicorn playmarket.wsgi:application"
echo "5. Add a PostgreSQL database service"
echo "6. Configure environment variables in Render dashboard:"
echo "   - DEBUG: false"
echo "   - SECRET_KEY: [generate a secure key]"
echo "   - ALLOWED_HOSTS: .onrender.com"
echo "   - CORS_ALLOWED_ORIGINS: [your frontend domain]"
echo "   - DATABASE_URL: [Render will provide this automatically]"