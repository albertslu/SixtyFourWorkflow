# SixtyFour Workflow Engine

A simplified replica of Sixtyfour's Workflow Engine with both frontend and backend components. This application allows users to configure and execute workflows made up of modular blocks.

## 🚀 Features

### Backend Capabilities
- **Enrich Lead**: Use the Sixtyfour `/enrich-lead` endpoint
- **Find Email**: Use the Sixtyfour `/find-email` endpoint  
- **Read CSV**: Load CSV files into dataframes
- **Filter**: Apply pandas-like filtering logic to dataframes
- **Save CSV**: Export dataframes back to CSV files
- **Chainable Blocks**: All blocks can be connected in any order
- **Async Processing**: Efficient job handling with progress tracking
- **Parallelization**: Optimized execution for faster processing

### Frontend Features
- **Drag & Drop Interface**: Intuitive workflow builder
- **Real-time Progress**: Live job status and progress tracking
- **Parameter Configuration**: Easy block parameter setup
- **Results Display**: Clear visualization of intermediate and final results
- **Modern UI**: Built with React, Next.js, and Tailwind CSS

## 📁 Project Structure

```
SixtyFourWorkflow/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Data models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   ├── tests/              # Backend tests
│   ├── requirements.txt    # Python dependencies
│   └── venv/              # Virtual environment
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── lib/           # Utility libraries
│   │   ├── types/         # TypeScript types
│   │   ├── hooks/         # Custom React hooks
│   │   └── utils/         # Helper functions
│   ├── pages/             # Next.js pages
│   └── public/            # Static assets
├── uploads/               # File storage directory
├── env.example           # Environment variables template
└── README.md             # This file
```

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm or yarn
- Supabase account (optional, can use local storage)

### Quick Setup (Recommended)

1. **Run the automated setup script**
   ```bash
   ./setup.sh
   ```

2. **Set up Supabase (Optional but Recommended)**
   - Follow the [Supabase Setup Guide](./SUPABASE_SETUP.md)
   - Update your `.env` file with Supabase credentials

3. **Configure Sixtyfour API**
   - Get your API key from [app.sixtyfour.ai](https://app.sixtyfour.ai)
   - Update `.env` with your credentials:
   ```bash
   SIXTYFOUR_API_KEY=your_api_key_here
   SIXTYFOUR_ORG_ID=your_organization_id_here
   ```

4. **Test the backend**
   ```bash
   cd backend
   python test_backend.py
   ```

5. **Start the servers**
   ```bash
   # Terminal 1 - Backend
   cd backend && source venv/bin/activate && cd app && python main.py
   
   # Terminal 2 - Frontend
   cd frontend && npm run dev
   ```

### Manual Setup

#### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp ../env.example .env
   # Edit .env file with your configurations
   ```

5. **Run the backend server**
   ```bash
   cd app
   python main.py
   ```
   
   The backend will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Set up environment variables**
   ```bash
   cp ../env.example .env.local
   # Add NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Run the development server**
   ```bash
   npm run dev
   # or
   yarn dev
   ```
   
   The frontend will be available at `http://localhost:3000`

## 🔧 Configuration

### Environment Variables

Copy `env.example` to `.env` and configure the following:

```bash
# Sixtyfour API Configuration
SIXTYFOUR_API_KEY=your_api_key_here
SIXTYFOUR_ORG_ID=your_organization_id_here
SIXTYFOUR_BASE_URL=https://api.sixtyfour.ai

# Backend Configuration
BACKEND_HOST=localhost
BACKEND_PORT=8000
DEBUG=True

# Frontend Configuration
FRONTEND_PORT=3000

# File Storage
UPLOAD_FOLDER=./uploads
MAX_FILE_SIZE=10485760  # 10MB
```

## 📊 Example Workflows

### Basic Workflow
```
Read CSV → Enrich Lead → Save CSV
```

### Advanced Filtered Workflow
```
Read CSV → 
Filter (company name contains 'Ariglad Inc') → 
Enrich Lead (return educational background) → 
Add boolean field is_american_education → 
Filter (is_american_education = True) → 
Save CSV
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
source venv/bin/activate
pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm run test
# or
yarn test
```

## 🚀 Development

### Code Formatting
```bash
# Backend
cd backend
black app/
isort app/
flake8 app/

# Frontend
cd frontend
npm run lint
```

### Type Checking
```bash
# Frontend
cd frontend
npm run type-check
```

## 📝 API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Run linting and tests
6. Submit a pull request

## 📄 License

This project is for demonstration purposes as part of a take-home assignment.

## 🔗 Sample Data

Use the provided sample CSV file for testing workflows. The file should be placed in the `uploads/` directory.

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**: Change the port in your `.env` file
2. **API key issues**: Ensure your Sixtyfour API key is correctly set
3. **File upload errors**: Check that the `uploads/` directory exists and has write permissions
4. **CORS errors**: Verify the frontend URL is added to the backend CORS configuration

### Getting Help

If you encounter issues:
1. Check the console logs for error messages
2. Verify all environment variables are set correctly
3. Ensure all dependencies are installed
4. Check that both backend and frontend servers are running
