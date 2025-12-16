#!/bin/bash

# Quick Start Script for Autonomous Compliance Platform
set -e

echo "=== Autonomous Compliance & Security Automation Platform ==="
echo "Quick Start Setup"
echo ""

# Check prerequisites
echo "Checking prerequisites..."
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed. Aborting." >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js is required but not installed. Aborting." >&2; exit 1; }

# Setup backend
echo "Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing backend dependencies..."
pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "IMPORTANT: Edit backend/.env with your configuration!"
fi

# Setup frontend
echo ""
echo "Setting up frontend..."
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install --silent
fi

if [ ! -f ".env" ]; then
    echo "Creating frontend .env..."
    echo "REACT_APP_API_URL=http://localhost:8000" > .env
fi

cd ..

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your database and AWS credentials"
echo "2. Start PostgreSQL (or use RDS)"
echo "3. Run database migrations:"
echo "   cd backend && alembic upgrade head"
echo "4. Create admin user (see DEPLOYMENT_GUIDE.md)"
echo "5. Start backend:"
echo "   cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "6. Start frontend:"
echo "   cd frontend && npm start"
echo "7. Access dashboard: http://localhost:3000"
echo ""
echo "For production deployment, see DEPLOYMENT_GUIDE.md"
