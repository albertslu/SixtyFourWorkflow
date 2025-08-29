# Supabase Setup Guide

## 🚀 Quick Setup

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Sign up/Sign in
3. Click "New Project"
4. Choose your organization
5. Fill in project details:
   - **Name**: `sixtyfour-workflow`
   - **Database Password**: Choose a strong password
   - **Region**: Select closest to your location
6. Click "Create new project"

### 2. Get Your Credentials

Once your project is created, go to **Settings > API**:

- **Project URL**: `https://your-project-id.supabase.co`
- **Anon Key**: `eyJ...` (public key for client-side)
- **Service Role Key**: `eyJ...` (secret key for server-side)

### 3. Update Environment Variables

Copy these to your `.env` file:

```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_role_key_here
```

## 📊 Database Schema

### 4. Create Tables

Go to **SQL Editor** in your Supabase dashboard and run this SQL:

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Workflows table
CREATE TABLE workflows (
    workflow_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    blocks JSONB NOT NULL DEFAULT '[]',
    connections JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Jobs table
CREATE TABLE jobs (
    job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    progress JSONB NOT NULL DEFAULT '{}',
    results JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    final_output_path TEXT
);

-- Indexes for better performance
CREATE INDEX idx_workflows_created_at ON workflows(created_at DESC);
CREATE INDEX idx_jobs_workflow_id ON jobs(workflow_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);

-- Update trigger for workflows
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_workflows_updated_at 
    BEFORE UPDATE ON workflows 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) - Optional for multi-tenant setup
-- ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- Policies (uncomment if using RLS)
-- CREATE POLICY "Users can view their own workflows" ON workflows
--     FOR SELECT USING (auth.uid() = user_id);
-- CREATE POLICY "Users can create workflows" ON workflows
--     FOR INSERT WITH CHECK (auth.uid() = user_id);
-- CREATE POLICY "Users can update their own workflows" ON workflows
--     FOR UPDATE USING (auth.uid() = user_id);
-- CREATE POLICY "Users can delete their own workflows" ON workflows
--     FOR DELETE USING (auth.uid() = user_id);
```

### 5. Verify Setup

Run this query to verify tables were created:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('workflows', 'jobs');
```

You should see both `workflows` and `jobs` tables.

## 🔧 Configuration Options

### Option 1: Use Supabase (Recommended)

- ✅ Managed PostgreSQL database
- ✅ Real-time subscriptions
- ✅ Built-in authentication
- ✅ Automatic backups
- ✅ Easy scaling

Set these in your `.env`:
```bash
SUPABASE_URL=your_project_url
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_role_key
```

### Option 2: Local PostgreSQL

If you prefer local development:

1. Install PostgreSQL locally
2. Create a database: `createdb workflow_db`
3. Set this in your `.env`:
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/workflow_db
```

The application will automatically detect and use the appropriate configuration.

## 🔍 Testing the Setup

### 1. Start the Backend

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
cd app
python main.py
```

### 2. Check API Documentation

Visit `http://localhost:8000/docs` to see the interactive API documentation.

### 3. Test Database Connection

The application will log database connection status on startup. Look for:
```
Connected to Supabase database
```

### 4. Create a Test Workflow

Use the API docs or curl:

```bash
curl -X POST "http://localhost:8000/api/workflows/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Workflow",
    "description": "A simple test workflow",
    "blocks": [],
    "connections": []
  }'
```

## 🔒 Security Notes

### For Development
- The anon key is safe to use in frontend code
- The service role key should ONLY be used in backend code
- Never commit real keys to version control

### For Production
- Enable Row Level Security (RLS)
- Set up proper authentication
- Use environment-specific projects
- Enable database backups
- Monitor usage and set up alerts

## 📈 Monitoring

### Supabase Dashboard
- **Database**: Monitor queries, connections, and performance
- **Auth**: Track user activity (if using authentication)
- **Storage**: Monitor file uploads and storage usage
- **Logs**: View real-time logs and errors

### Application Logs
- Check `backend/logs/app.log` for application logs
- Check `backend/logs/error.log` for error logs

## 🆘 Troubleshooting

### Common Issues

1. **Connection Error**: 
   - Verify SUPABASE_URL and keys are correct
   - Check if your IP is allowed (Supabase allows all by default)

2. **Table Not Found**:
   - Ensure you ran the SQL schema creation script
   - Check table names match exactly

3. **Permission Denied**:
   - Verify you're using the service role key for server operations
   - Check if RLS is enabled and policies are correct

4. **Timeout Errors**:
   - Check your internet connection
   - Verify Supabase project is active

### Getting Help

- Check Supabase documentation: [docs.supabase.com](https://docs.supabase.com)
- Join Supabase Discord: [discord.supabase.com](https://discord.supabase.com)
- Check application logs in `backend/logs/`
