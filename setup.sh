#!/bin/bash

# SixtyFour Workflow Engine Setup Script

echo "🚀 Setting up SixtyFour Workflow Engine..."

# Check if Python 3.8+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed. Please install Node.js 18 or higher."
    exit 1
fi

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ Created .env file. Please edit it with your Sixtyfour API credentials."
else
    echo "✅ .env file already exists."
fi

# Setup Backend
echo "🐍 Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Backend setup complete!"

# Setup Frontend
echo "⚛️ Setting up frontend..."
cd ../frontend

# Install Node.js dependencies
echo "📥 Installing Node.js dependencies..."
npm install

echo "✅ Frontend setup complete!"

# Create necessary directories
echo "📁 Creating necessary directories..."
cd ..
mkdir -p uploads
mkdir -p backend/logs

echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit the .env file with your Sixtyfour API credentials:"
echo "   - Get your API key from https://app.sixtyfour.ai"
echo "   - Set SIXTYFOUR_API_KEY and SIXTYFOUR_ORG_ID"
echo ""
echo "2. Start the backend server:"
echo "   cd backend && source venv/bin/activate && cd app && python main.py"
echo ""
echo "3. Start the frontend server (in a new terminal):"
echo "   cd frontend && npm run dev"
echo ""
echo "4. Open http://localhost:3000 in your browser"
echo ""
echo "📚 API Documentation will be available at http://localhost:8000/docs"
