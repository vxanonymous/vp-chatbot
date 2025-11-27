# Vacation Planning System

Full-stack application for vacation planning through AI-powered conversations. Built with FastAPI backend, React frontend, and OpenRouter AI integration.

**Created by Vinh Nguyen**

## Demo

The app is hosted on **[https://vp-chatbot.surge.sh](https://vp-chatbot.surge.sh)**

## Project Structure

```
vp-chatbot/
├── backend/
│   ├── app/
│   │   ├── api/               # REST API endpoints
│   │   ├── auth/              # JWT authentication
│   │   ├── services/          # Business logic services
│   │   ├── models/            # Pydantic data models
│   │   ├── database/          # MongoDB connection
│   │   ├── core/              # Core infrastructure
│   │   ├── domains/           # Domain-specific logic
│   │   └── main.py            # FastAPI app entry point
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── contexts/          # React contexts
│   │   └── services/          # API service calls
│   └── package.json           # Node.js dependencies
└── docs/                      # Documentation
```

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│  React + Vite | Tailwind CSS | Context API | Custom Hooks   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
                         │
┌────────────────────────▼────────────────────────────────────┐
│                      API Layer (FastAPI)                     │
│  /chat | /auth | /conversations | /health                    │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Service Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Core       │  │   Domain     │  │   External   │     │
│  │  Services    │  │   Services   │  │   Services   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Data Layer                                   │
│  MongoDB (Primary) | Redis (Cache) | OpenRouter API         │
└──────────────────────────────────────────────────────────────┘
```

### Design Principles

#### 1. Domain-Driven Design (DDD)
- **Core Services**: Domain-agnostic infrastructure (ConversationService, OpenAIService, UserService)
- **Domain Services**: Vacation-specific logic (VacationIntelligenceService, VacationPlanner, ProactiveAssistant)
- **Configuration-Driven**: All vacation content externalized to JSON config files

#### 2. Separation of Concerns
- **API Layer**: Handles HTTP requests/responses, authentication, validation
- **Service Layer**: Business logic and orchestration
- **Domain Layer**: Vacation-specific intelligence and planning
- **Data Layer**: Database access and caching

#### 3. Dependency Injection
- Service Container pattern for managing dependencies
- Lazy initialization of services
- Easy testing with mockable interfaces

#### 4. Configuration Management
- All prompts, examples, keywords, and destinations in JSON files
- No hardcoded vacation content in code
- Easy to update without code changes

## Core Components

### Frontend (React)

**Key Components**:
- **ChatInterface**: Main conversation UI with message display and input
- **AuthContext**: Authentication state management
- **useChat Hook**: Manages chat state and API communication
- **MessageList**: Displays conversation history
- **SuggestionPanel**: Shows proactive suggestions and vacation summaries

**Technologies**:
- React 18 with Hooks
- Vite for build tooling
- Tailwind CSS for styling
- Context API for state management

### API Layer (FastAPI)

**Key Endpoints**:
- `POST /chat/` - Send message and get response
- `POST /chat/stream` - Stream responses in real-time
- `GET /conversations` - List user conversations
- `POST /auth/signup` - User registration
- `POST /auth/login` - User authentication
- `GET /health` - System health check

**Features**:
- JWT-based authentication
- Request validation with Pydantic
- Error handling with custom exceptions
- Server-Sent Events for streaming

### Service Layer

#### Core Services

**ConversationService**
- Manages conversation lifecycle (CRUD)
- Handles message storage and retrieval
- Provides conversation analysis and summaries
- Manages conversation metadata and preferences

**UserService**
- User registration and authentication
- User profile management
- Password hashing and validation
- User session management

**OpenAIService**
- Integrates with OpenRouter API
- Generates conversational responses
- Extracts user preferences from messages
- Handles AI response streaming

**ConversationHandler**
- Orchestrates message processing pipeline
- Coordinates between services
- Manages conversation flow
- Handles error recovery

#### Domain Services (Vacation-Specific)

**VacationIntelligenceService**
- Analyzes user preferences and travel intentions
- Detects decision stages (exploring, planning, booking)
- Extracts destinations using AI with countries-list fallback and regex patterns
- Extracts budgets, dates, and interests from user messages
- Provides smart recommendations

**VacationPlanner**
- Creates personalized vacation summaries
- Generates destination-specific insights
- Provides budget breakdowns
- Suggests activities and itineraries

**ProactiveAssistant**
- Generates contextual suggestions
- Identifies missing information
- Guides conversation flow
- Provides next-step recommendations

**ConversationMemory**
- Maintains conversation context
- Tracks key points and preferences
- Provides relevance scoring
- Stores conversation insights

**ErrorRecoveryService**
- Provides error messages
- Validates conversation flow
- Detects off-topic messages
- Handles technical errors

#### Infrastructure Services

**ServiceContainer**
- Dependency injection container
- Manages service lifecycle
- Provides singleton service instances
- Enables testability through dependency injection

**ConfigManager**
- Manages application configuration
- Handles environment variables
- Provides configuration validation
- Supports different environments (dev, prod)

**RequestDeduplicator**
- Caches identical requests to reduce redundant API calls
- Reduces OpenRouter API costs by 20-40% for repeated queries
- Thread-safe cache with configurable TTL (default: 60 seconds)
- Automatic cleanup of expired entries
- Integrated into ConversationHandler for AI response caching

### Data Layer

**MongoDB**
- Primary database for persistent storage
- Stores users, conversations, and messages
- Flexible schema for conversation metadata
- Indexed for performance

**Redis** (Optional)
- In-memory cache for fast access
- Conversation context caching
- Session management
- Performance optimization

**OpenRouter API**
- External AI service gateway for conversation generation
- Multiple AI model integration (OpenAI-compatible)
- Streaming response support
- Preference extraction
- AI-based destination extraction (8000 token limit for long itineraries)

## Data Flow

### Message Processing Flow

```
1. User sends message
   ↓
2. Frontend → API: POST /chat/
   ↓
3. API validates request & authenticates user
   ↓
4. ConversationHandler.process_message()
   ├─→ Ensures conversation exists
   ├─→ Adds user message to conversation
   ├─→ ConversationMemory stores context
   ├─→ Extracts user preferences (destinations via AI, then regex/known-list fallback)
   ├─→ Prepares messages for AI
   ├─→ RequestDeduplicator checks cache for identical requests
   │   ├─→ Cache hit: Returns cached AI response (no API call)
   │   └─→ Cache miss: Proceeds to OpenRouter API call
   ├─→ OpenAIService generates response (if not cached)
   ├─→ Caches response for future identical requests
   ├─→ Saves assistant response
   └─→ Returns response to client
   ↓
5. API → Frontend: ChatResponse
   ├─→ response: AI message
   ├─→ suggestions: Proactive suggestions
   └─→ vacation_summary: Vacation summary
   ↓
6. Frontend displays response
```

### Streaming Flow

```
1. User sends message
   ↓
2. Frontend → API: POST /chat/stream
   ↓
3. API creates SSE stream
   ↓
4. Stream generates chunks:
   ├─→ Content chunks (word by word)
   ├─→ Suggestions (when ready)
   ├─→ Vacation summary (when ready)
   └─→ Done signal
   ↓
5. Frontend receives and displays chunks in real-time
```

## Configuration-Driven Content

Vacation-specific content is externalized to JSON configuration files in `domains/vacation/config/`:

- **`prompts.json`**: System prompts, response templates, and conversation rules
- **`examples.json`**: Example interactions for training the AI
- **`keywords.json`**: Keywords for stage detection, travel styles, and interest extraction
- **`destinations.json`**: Minimal list of all countries (199 countries), used as fallback when AI extraction fails
- **`destination_responses.json`**: Destination-specific budget, timing, and activity responses

**Implementation**:
- `VacationConfigLoader` singleton loads all configurations
- Services access config via `vacation_config_loader.get_config(type)`
- Configs are cached for performance
- No hardcoded vacation content in service code

**Benefits**:
- Content updates without code changes
- A/B testing capabilities
- Non-developers can update content
- Version control for content separately

## Error Handling Strategy

**Custom Exception Hierarchy**:
- `AppException` (base)
  - `NotFoundError` (404)
  - `ValidationError` (400)
  - `AuthenticationError` (401)
  - `AuthorizationError` (403)
  - `DatabaseError` (500)
  - `ServiceError` (502)
  - `TimeoutError` (504)

**Centralized Error Handling**:
- `handle_app_exception()` function in `error_handlers.py`
- Consistent error responses across all endpoints
- Error messages via `ErrorRecoveryService`
- Proper HTTP status codes mapping
- Error recovery mechanisms integrated in chat endpoints

## Concurrency Management

- Rate limiting middleware prevents abuse (20 requests/minute per user)
- Request deduplication caches identical requests for 60 seconds, reducing OpenRouter API costs by 20-40%
- Frontend request deduplication prevents concurrent message sending
- MongoDB atomic operations ensure data consistency
- Async locks protect shared state:
  - `ConversationService._cache_lock` protects cache read/write operations
  - `RateLimiter._lock` protects rate limit tracking
  - `RequestDeduplicator._lock` protects request cache operations
- API semaphore limits concurrent OpenRouter API calls to 5
- All cache operations use `async with self._cache_lock` for thread-safe access

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **MongoDB**: NoSQL database
- **Redis**: In-memory cache (optional)
- **OpenRouter API**: AI conversation generation
- **Pydantic**: Data validation
- **JWT**: Authentication tokens

### Frontend
- **React 18**: UI framework
- **Vite**: Build tool
- **Tailwind CSS**: Styling
- **Context API**: State management

### Development
- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **isort**: Import organization
- **Docker**: Containerization

## Getting Started

### Requirements
- **Python 3.11+** - For the FastAPI backend
- **Node.js 18+** - For the React frontend
- **MongoDB** - Database for storing conversations and user data
- **Redis** - In-memory cache for fast conversation access (optional)
- **OpenRouter API Key** - For AI-powered responses

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd vp-chatbot
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   ```

4. **Configure environment variables**
   ```bash
   # Set up your database connections and API keys
   cp .env.example .env
   # Edit .env with your MongoDB, Redis, and OpenRouter credentials
   ```

5. **Start the development servers**
   ```bash
   # Start the FastAPI backend (in one terminal)
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Start the Vite dev server (in another terminal)
   cd frontend
   npm run dev
   ```

### Production Deployment

```bash
# Using Docker Compose for easy deployment
docker-compose -f docker-compose.prod.yml up -d

# Or deploy manually:
# Backend: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
# Frontend: npm run build && serve -s dist
```

## API Documentation

- Interactive API docs available at `http://localhost:8000/docs` when running the backend
- OpenAPI specification automatically generated from FastAPI models
- Request/response examples included in the documentation

## License

This project is open source under the MIT License.
