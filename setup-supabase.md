# Supabase Setup Instructions

## Quick Setup Guide

### 1. Create Supabase Project
1. Go to [supabase.com](https://supabase.com) and sign up/login
2. Click "New Project"
3. Fill in project details:
   - **Name**: `sixtyfour-workflow`
   - **Database Password**: Choose a strong password
   - **Region**: Select closest to your location
4. Click "Create new project"

### 2. Get Your Credentials
Once your project is created, go to **Settings > API**:
- **Project URL**: `https://your-project-id.supabase.co`
- **Anon Key**: `eyJ...` (public key for client-side)
- **Service Role Key**: `eyJ...` (secret key for server-side)

### 3. Create Database Tables
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
```

### 4. Update Environment Variables

**Backend (.env in root directory):**
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_role_key_here
```

**Frontend (frontend/next.env.local):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
```

### 5. Verify Setup
Run this query in Supabase SQL Editor to verify tables were created:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('workflows', 'jobs');
```

You should see both `workflows` and `jobs` tables.

### 6. Test the Connection
1. Start your backend: `cd backend && python -m uvicorn app.main:app --reload`
2. Start your frontend: `cd frontend && npm run dev`
3. Try creating and saving a workflow

## Notes
- The backend will fall back to in-memory storage if Supabase credentials are not provided
- Make sure to keep your Service Role Key secret and only use it on the backend
- The Anon Key is safe to use in frontend applications
