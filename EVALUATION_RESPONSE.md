# SixtyFour Workflow Engine - Evaluation Response

## 📊 Evaluation Criteria

### 1. Product Experience – UI Intuition and Smoothness

**Implementation Highlights:**

- **Drag & Drop Interface**: Intuitive workflow builder with visual block palette and canvas
  - Blocks can be dragged from palette to canvas or clicked to add
  - Smooth drag interactions with visual feedback and constraints
  - Grid-based canvas with visual guides for alignment

- **Real-time Visual Feedback**:
  - Connection mode with visual indicators when linking blocks
  - Live progress tracking with percentage completion and current step
  - Toast notifications for user actions and system feedback
  - Color-coded block types with meaningful icons (📁 Read CSV, ✨ Enrich Lead, etc.)

- **Responsive Design**:
  - Collapsible block palette to maximize canvas space
  - Adaptive layout that works on different screen sizes
  - Smooth transitions and animations for state changes

- **User-Friendly Features**:
  - Parameter configuration modal with form validation
  - Clear workflow naming and saving functionality
  - Empty state guidance for new users
  - Connection visualization with clickable lines for removal

**Code Example - Smooth Drag Implementation:**
```typescript
const handleMouseDown = useCallback((blockId: string, event: React.MouseEvent) => {
  // Global mouse event listeners for smoother dragging
  const handleGlobalMouseMove = (e: MouseEvent) => {
    const newX = e.clientX - rect.left - dragOffset.x
    const newY = e.clientY - rect.top - dragOffset.y
    // Constrain to canvas bounds with padding
    const constrainedX = Math.max(100, Math.min(rect.width - 100, newX))
    const constrainedY = Math.max(60, Math.min(rect.height - 60, newY))
    updateBlock(blockId, { position: { x: constrainedX, y: constrainedY } })
  }
}, [blocks, dragOffset, updateBlock])
```

### 2. Backend Stability – Reliable Workflow Execution & Speed Optimization

**Reliability Features:**

- **Robust Error Handling**:
  - Try-catch blocks around all API calls and data operations
  - Graceful degradation when Sixtyfour API calls fail
  - Comprehensive logging with structured error messages
  - Job status tracking with detailed error reporting

- **Async Processing Architecture**:
  - Non-blocking workflow execution using asyncio
  - Background job processing with real-time status updates
  - Proper resource cleanup and memory management

- **Data Integrity**:
  - DataFrame validation and type checking
  - Atomic operations for database updates
  - Rollback mechanisms for failed operations

**Speed Optimization Strategies:**

1. **Concurrent API Processing**:
   ```python
   async def batch_enrich_leads(self, leads: List[Dict[str, Any]], struct: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
       # Create tasks for concurrent execution
       tasks = [self.enrich_lead(lead, struct) for lead in leads]
       # Execute all tasks concurrently
       results = await asyncio.gather(*tasks, return_exceptions=True)
   ```

2. **Configurable Batch Processing**:
   - Adjustable batch sizes (default: 10 concurrent requests)
   - Prevents API rate limiting while maximizing throughput
   - Progress tracking for long-running batch operations

3. **Optimized Timeout Management**:
   - Extended timeouts for enrich-lead (180s) due to API processing time
   - Shorter timeouts for status checks (30s)
   - Connection pooling with httpx.AsyncClient

4. **Memory-Efficient DataFrame Operations**:
   - Streaming CSV processing for large files
   - In-memory DataFrame management with cleanup
   - Efficient pandas operations for filtering and transformations

5. **Caching and State Management**:
   - DataFrameManager for efficient intermediate result storage
   - Minimal data serialization between processing steps
   - Optional Supabase integration with fallback to in-memory storage

### 3. State Management – Data State Transitions

**Comprehensive State Architecture:**

1. **Job Lifecycle Management**:
   ```python
   class JobStatus(str, Enum):
       PENDING = "pending"
       RUNNING = "running" 
       COMPLETED = "completed"
       FAILED = "failed"
       CANCELLED = "cancelled"
   ```

2. **Progress Tracking**:
   ```python
   class JobProgress(BaseModel):
       current_step: int = 0
       total_steps: int = 0
       current_block_id: Optional[str] = None
       current_block_name: Optional[str] = None
       processed_rows: int = 0
       total_rows: int = 0
       message: str = ""
       percentage: float = 0.0
   ```

3. **DataFrame State Management**:
   - DataFrameManager tracks intermediate results between blocks
   - Unique keys for each block output prevent data conflicts
   - Metadata tracking for debugging and optimization

4. **Frontend State Synchronization**:
   - Real-time job monitoring with polling
   - Optimistic UI updates with error rollback
   - Connection state management for block linking

5. **Database State Persistence**:
   - Atomic updates for job status changes
   - JSON serialization for complex data structures
   - Fallback to in-memory storage when database unavailable

## 🗣️ Discussion Topics

### 1. How would you implement the enrich_company endpoint?

**Proposed Implementation:**

```python
async def enrich_company(self, company_info: Dict[str, Any], struct: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Enrich company information using Sixtyfour API
    
    Args:
        company_info: Dictionary containing company information (name, domain, industry, etc.)
        struct: Optional dictionary defining the structure of data to return
    """
    if struct is None:
        struct = {
            "company_name": "Official company name",
            "domain": "Primary company domain",
            "industry": "Primary industry classification",
            "employee_count": "Number of employees",
            "revenue": "Annual revenue estimate",
            "founded_year": "Year company was founded",
            "headquarters": "Primary headquarters location",
            "description": "Company description and business model",
            "technologies": "Technology stack and tools used",
            "funding_stage": "Current funding stage (seed, series A, etc.)",
            "total_funding": "Total funding raised",
            "key_executives": "List of key executives and their roles",
            "social_media": "Social media profiles and handles",
            "recent_news": "Recent news and press mentions"
        }
    
    data = {
        "company_info": company_info,
        "struct": struct
    }
    
    logger.info(f"Enriching company: {company_info.get('name', 'Unknown')}")
    return await self._make_request("enrich-company", data)
```

**Integration into Workflow Engine:**

1. **New Block Type**: Add `ENRICH_COMPANY` to BlockType enum
2. **Block Configuration**: Company-specific parameters and struct customization
3. **Data Flow**: Input can be company names, domains, or partial company data
4. **Output Format**: Standardized company profile with enriched fields
5. **Batch Processing**: Support for bulk company enrichment with rate limiting

### 2. How to prevent incompatible blocks from being chained together?

**Block Compatibility System:**

```python
class BlockCompatibility:
    """Defines input/output types and validation rules for blocks"""
    
    BLOCK_IO_TYPES = {
        'read_csv': {'inputs': [], 'outputs': ['dataframe']},
        'filter': {'inputs': ['dataframe'], 'outputs': ['dataframe']},
        'enrich_lead': {'inputs': ['dataframe'], 'outputs': ['dataframe']},
        'enrich_company': {'inputs': ['dataframe'], 'outputs': ['dataframe']},
        'find_email': {'inputs': ['dataframe'], 'outputs': ['dataframe']},
        'save_csv': {'inputs': ['dataframe'], 'outputs': []}
    }
    
    INCOMPATIBLE_CHAINS = [
        ('enrich_company', 'enrich_lead'),  # Company data shouldn't flow to lead enrichment
        ('find_email', 'enrich_company'),   # Email results shouldn't enrich companies
    ]
    
    @classmethod
    def can_connect(cls, source_type: BlockType, target_type: BlockType) -> bool:
        """Check if two block types can be connected"""
        # Check basic input/output compatibility
        source_outputs = cls.BLOCK_IO_TYPES[source_type]['outputs']
        target_inputs = cls.BLOCK_IO_TYPES[target_type]['inputs']
        
        if not target_inputs:  # Target accepts no inputs (like save_csv)
            return len(source_outputs) > 0
        
        if not any(output in target_inputs for output in source_outputs):
            return False
        
        # Check explicit incompatibility rules
        if (source_type, target_type) in cls.INCOMPATIBLE_CHAINS:
            return False
        
        return True
```

**Frontend Implementation:**

```typescript
const finishConnection = useCallback((targetId: string) => {
  const sourceBlock = blocks.find(b => b.block_id === connectingFrom)
  const targetBlock = blocks.find(b => b.block_id === targetId)
  
  if (!BlockCompatibility.canConnect(sourceBlock.block_type, targetBlock.block_type)) {
    toast.error(`Cannot connect ${sourceBlock.name} to ${targetBlock.name}: Incompatible data types`)
    return
  }
  
  // Proceed with connection...
}, [blocks, connectingFrom])
```

**Data Schema Validation:**

```python
def validate_data_schema(self, df: pd.DataFrame, required_schema: Dict[str, str]) -> bool:
    """Validate that DataFrame has required columns for block execution"""
    for column, data_type in required_schema.items():
        if column not in df.columns:
            return False
        if not self._validate_column_type(df[column], data_type):
            return False
    return True
```

### 3. How would you scale the backend to process thousands of rows in a CSV?

**Scaling Strategy:**

1. **Streaming CSV Processing**:
   ```python
   async def process_large_csv(self, file_path: str, chunk_size: int = 1000):
       """Process CSV in chunks to handle large files"""
       for chunk in pd.read_csv(file_path, chunksize=chunk_size):
           yield await self.process_chunk(chunk)
   ```

2. **Distributed Task Queue**:
   ```python
   # Using Celery for distributed processing
   from celery import Celery
   
   @celery.task
   def process_batch_async(batch_data: List[Dict], block_config: Dict):
       """Process batch of rows asynchronously"""
       return sixtyfour_service.batch_enrich_leads(batch_data)
   ```

3. **Database Optimization**:
   - Connection pooling for concurrent database operations
   - Batch inserts for job results and progress updates
   - Indexed queries for job status lookups
   - Read replicas for status monitoring

4. **Memory Management**:
   ```python
   class OptimizedDataFrameManager:
       def __init__(self, max_memory_mb: int = 1000):
           self.max_memory = max_memory_mb * 1024 * 1024
           self.current_memory = 0
           
       def store_dataframe(self, key: str, df: pd.DataFrame):
           # Implement LRU cache with memory limits
           df_memory = df.memory_usage(deep=True).sum()
           if self.current_memory + df_memory > self.max_memory:
               self._evict_oldest()
           self.dataframes[key] = df
   ```

5. **API Rate Limiting & Circuit Breakers**:
   ```python
   class RateLimitedSixtyfourService:
       def __init__(self):
           self.rate_limiter = AsyncLimiter(max_rate=100, time_period=60)  # 100 requests per minute
           self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=30)
           
       async def enrich_lead_with_backoff(self, lead_info: Dict):
           async with self.rate_limiter:
               return await self.circuit_breaker.call(self.enrich_lead, lead_info)
   ```

6. **Horizontal Scaling**:
   - Containerized backend with Docker
   - Load balancer for multiple backend instances
   - Shared state via Redis or database
   - Auto-scaling based on queue depth

7. **Progress Optimization**:
   - Batch progress updates (every 100 rows vs every row)
   - WebSocket connections for real-time updates
   - Compressed progress payloads

### 4. Product decisions, tradeoffs, and improvements with more time

**Key Product Decisions:**

1. **Synchronous vs Asynchronous Execution**:
   - **Decision**: Chose async execution with real-time progress
   - **Tradeoff**: More complex implementation vs better user experience
   - **Alternative**: Could have used simple synchronous processing

2. **In-Memory vs Database Storage**:
   - **Decision**: Hybrid approach with Supabase + in-memory fallback
   - **Tradeoff**: Flexibility vs consistency
   - **Improvement**: Implement proper database migrations and connection pooling

3. **Block Parameter Configuration**:
   - **Decision**: Modal-based parameter editing
   - **Tradeoff**: Clean UI vs inline editing convenience
   - **Improvement**: Add inline parameter preview and validation

4. **Error Handling Strategy**:
   - **Decision**: Graceful degradation with detailed error reporting
   - **Tradeoff**: Complexity vs robustness
   - **Improvement**: Add retry mechanisms and partial failure recovery

**Improvements with More Time:**

1. **Advanced Workflow Features**:
   - Conditional branching (if/else blocks)
   - Loop blocks for iterative processing
   - Parallel execution paths
   - Workflow templates and sharing

2. **Enhanced User Experience**:
   - Undo/redo functionality
   - Workflow versioning and history
   - Block search and categorization
   - Keyboard shortcuts and accessibility

3. **Performance Optimizations**:
   - Workflow execution planning and optimization
   - Caching layer for repeated operations
   - Incremental processing for large datasets
   - Smart batching based on API response times

4. **Enterprise Features**:
   - User authentication and authorization
   - Team collaboration and sharing
   - Audit logging and compliance
   - Custom block development SDK

### 5. Learnings about Sixtyfour API and suggested improvements

**Key Learnings:**

1. **API Response Time Variability**:
   - Enrich-lead can take 2-3 minutes per request
   - Response times vary significantly based on data complexity
   - Need for robust timeout and retry mechanisms

2. **Data Structure Flexibility**:
   - The `struct` parameter allows customizable output schemas
   - API handles partial input data gracefully
   - Response quality varies with input data completeness

3. **Rate Limiting Considerations**:
   - Need to balance throughput with API limits
   - Concurrent requests improve performance but require careful management
   - Error responses don't always clearly indicate rate limiting

**Suggested API Improvements:**

1. **Async Processing Support**:
   ```json
   // Suggested async endpoint
   POST /enrich-lead-async
   Response: {"task_id": "uuid", "estimated_completion": "2024-01-01T12:00:00Z"}
   
   GET /task-status/{task_id}
   Response: {"status": "processing", "progress": 0.75, "result": null}
   ```

2. **Batch Processing Endpoint**:
   ```json
   POST /batch-enrich-leads
   {
     "leads": [/* array of lead objects */],
     "struct": {/* common structure */},
     "batch_options": {
       "max_concurrent": 5,
       "timeout_per_lead": 180
     }
   }
   ```

3. **Enhanced Error Responses**:
   ```json
   {
     "error": "rate_limit_exceeded",
     "message": "Rate limit exceeded. Try again in 60 seconds.",
     "retry_after": 60,
     "current_usage": {"requests": 95, "limit": 100, "window": "1h"}
   }
   ```

4. **Progress Webhooks**:
   ```json
   // For long-running operations
   {
     "webhook_url": "https://myapp.com/webhooks/sixtyfour",
     "events": ["task_started", "task_progress", "task_completed", "task_failed"]
   }
   ```

5. **Data Quality Indicators**:
   ```json
   {
     "structured_data": {/* enriched data */},
     "confidence_scores": {
       "email": 0.95,
       "phone": 0.73,
       "title": 0.88
     },
     "data_sources": ["linkedin", "company_website", "public_records"],
     "last_updated": "2024-01-01T12:00:00Z"
   }
   ```

6. **API Usage Analytics**:
   - Endpoint for checking current usage and limits
   - Historical usage data for optimization
   - Cost estimation for batch operations

**Implementation Benefits:**

These improvements would enable:
- Better user experience with progress indication
- More efficient resource utilization
- Improved error handling and recovery
- Better cost management and optimization
- Enhanced data quality assessment

## 🎯 Conclusion

The SixtyFour Workflow Engine demonstrates a production-ready approach to building scalable, user-friendly data processing workflows. The implementation balances performance, reliability, and user experience while providing a solid foundation for future enhancements. The modular architecture allows for easy extension with new block types and processing capabilities, making it a versatile platform for data enrichment workflows.
