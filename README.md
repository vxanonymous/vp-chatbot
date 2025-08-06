# Vacation Planning Chatbot 🏖️

Your friendly AI travel companion that helps you plan the perfect vacation. Built with modern web technologies - FastAPI backend, React frontend, and OpenAI integration. Just tell us where you want to go, what you like to do, and we'll help you create an amazing trip plan.

**Created by Vinh Nguyen**

## What's Inside

```
vp-chatbot/
├── backend/                    # FastAPI backend - the brain
│   ├── app/
│   │   ├── api/               # REST API endpoints (chat, auth, conversations)
│   │   ├── auth/              # JWT authentication & security
│   │   ├── services/          # Business logic (OpenAI, User, Conversation services)
│   │   ├── models/            # Pydantic data models & schemas
│   │   ├── database/          # MongoDB connection & management
│   │   └── main.py            # FastAPI app entry point
│   └── requirements.txt       # Python dependencies
├── frontend/                   # React + Vite frontend
│   ├── src/
│   │   ├── components/        # React components (ChatInterface, MessageList, etc.)
│   │   ├── pages/             # Page components (ChatPage, AuthPage, LandingPage)
│   │   ├── hooks/             # Custom React hooks (useChat, useConversations)
│   │   ├── contexts/          # React contexts (Auth, Notification)
│   │   └── services/          # API service calls
│   └── package.json           # Node.js dependencies
└── docs/                      # Documentation & deployment guides
```

## What This Does

Think of this as having a knowledgeable travel friend who:
- Remembers what you like and don't like
- Suggests great places to visit based on your style
- Helps you figure out budgets and timing
- Gives you insider tips for your destination
- Keeps track of your planning progress

## Tech Stack

**Backend:**
- **FastAPI** - Modern, fast Python web framework with automatic API docs
- **MongoDB** - NoSQL database for flexible data storage
- **Redis** - In-memory caching for fast conversation access
- **OpenAI API** - GPT integration for intelligent responses
- **Pydantic** - Data validation and serialization
- **JWT** - Secure authentication tokens

**Frontend:**
- **React 18** - Modern UI framework with hooks
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **Context API** - State management
- **Custom Hooks** - Reusable logic

## Cool Features

- 🤖 **Smart Conversations**: The AI remembers what you've talked about and builds on it
- 🌍 **Knows the World**: Has info about destinations, activities, and local tips
- 💰 **Budget Friendly**: Helps you plan trips that fit your budget
- 📅 **Flexible Planning**: Works with your schedule, whether you're planning months ahead or last minute
- 🎯 **Personal Touch**: Learns your travel style and gives you personalized suggestions
- 🔒 **Keeps You Safe**: Secure login and protects your information
- 📱 **Works Everywhere**: Looks great on your phone, tablet, or computer
- 🌙 **Easy on the Eyes**: Dark mode for when you're planning late at night

## Key Services

- **ConversationService** - Manages chat history and context
- **UserService** - Handles authentication and user management
- **OpenAIService** - Integrates with GPT for intelligent responses
- **VacationPlannerService** - Creates personalized trip plans
- **VacationIntelligenceService** - Analyzes user preferences
- **ProactiveAssistantService** - Suggests next steps in planning
- **ConversationMemoryService** - Maintains conversation context

## Getting Started

### What You Need
- **Python 3.11+** - For the FastAPI backend
- **Node.js 18+** - For the React frontend
- **MongoDB** - Database for storing conversations and user data
- **Redis** - In-memory cache for fast conversation access
- **OpenAI API Key** - For AI-powered responses

### Setting It Up

1. **Get the code**
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
   # Edit .env with your MongoDB, Redis, and OpenAI credentials
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

### For Production Deployment

```bash
# Using Docker Compose for easy deployment
docker-compose -f docker-compose.prod.yml up -d

# Or deploy manually:
# Backend: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
# Frontend: npm run build && serve -s dist
```



## Architecture Overview

### Backend Architecture
- **FastAPI** - High-performance async web framework with automatic OpenAPI docs
- **MongoDB** - Document database for flexible conversation and user data storage
- **Redis** - In-memory cache for fast conversation retrieval and session management
- **OpenAI GPT** - Large language model for intelligent travel planning responses
- **JWT Authentication** - Secure token-based user authentication

### Frontend Architecture
- **React 18** - Component-based UI with hooks for state management
- **Vite** - Lightning-fast build tool and development server
- **Tailwind CSS** - Utility-first CSS framework for responsive design
- **Context API** - React's built-in state management for auth and notifications
- **Custom Hooks** - Reusable logic for chat, conversations, and API calls

### API Design
- **RESTful endpoints** for chat, authentication, and conversation management
- **WebSocket support** for real-time chat features
- **Automatic API documentation** at `/docs` endpoint
- **Request/response validation** with Pydantic models

## Security & Performance

### Security Features
- **JWT Authentication** - Secure token-based user sessions
- **Password Hashing** - bcrypt encryption for user passwords
- **Input Validation** - Pydantic models prevent injection attacks
- **CORS Protection** - Configured for secure cross-origin requests
- **Rate Limiting** - Prevents abuse and ensures fair usage

### Performance Optimizations
- **Async/Await** - Non-blocking operations for better responsiveness
- **Database Indexing** - Optimized MongoDB queries for fast data retrieval
- **Redis Caching** - In-memory storage for frequently accessed conversations
- **Connection Pooling** - Efficient database connection management
- **Response Compression** - Faster data transfer with gzip compression



## Development & Documentation

### API Documentation
- **Interactive API docs** available at `http://localhost:8000/docs` when running the backend
- **OpenAPI specification** automatically generated from FastAPI models
- **Request/response examples** included in the documentation

### Code Organization
- **Modular architecture** with clear separation of concerns
- **Type hints** throughout the codebase for better IDE support
- **Comprehensive comments** explaining business logic and design decisions
- **Consistent coding patterns** for maintainability

### Getting Help
- Check the documentation in `/docs/` folder
- Review the well-organized and commented source code
- Open an issue for bugs or feature requests
- API documentation is available at `/docs` endpoint when running

## Contributing

Want to help make it better? We welcome contributions!

1. **Fork the repository** and clone it locally
2. **Create a feature branch** for your changes
3. **Make your changes** following the existing code patterns
4. **Test your changes** to ensure everything works
5. **Submit a pull request** with a clear description

### Development Guidelines
- Follow the existing code style and patterns
- Add type hints to new functions
- Include comments for complex business logic
- Test your changes before submitting
- Update documentation if needed

## License

This project is open source under the MIT License - feel free to use it, modify it, and share it!

---

**Ready to plan your next adventure?**