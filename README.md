<div align="center">

# 🚀 Boost AI

**An intelligent AI-powered chat assistant built with modern technologies**

[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-5.2-DC382D?logo=redis)](https://redis.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

**Boost AI** is a full-stack AI chat application that allows users to create, manage, and interact with AI-powered conversations. It features **real-time streaming responses**, **user authentication**, **image support**, **markdown formatting**, **chat sharing**, **feedback system**, and **Redis caching** — all wrapped in a beautiful dark-themed UI.

---

## ✨ Features

### Core Features
- 🔐 **Secure Authentication** — Clerk-based user auth with JWT tokens
- 💬 **Real-time Streaming** — AI responses stream live via Server-Sent Events (SSE)
- 🖼️ **Image Upload** — Upload and display images in chat via ImageKit.io
- 📄 **Rich Markdown** — Full markdown support with tables, code blocks, and formatting
- 🗂️ **Chat History** — Persistent conversations with auto-generated titles

### Message Actions
- ✏️ **Edit Messages** — Edit your prompts inline and resend (with confirmation)
- 📋 **Copy Messages** — One-click copy for any message
- 👍👎 **Feedback** — Like or dislike AI responses (stored in database)
- 🔗 **Share Chats** — Generate shareable links for any conversation

### Shared Chats
- 🔐 **Auth Required** — Non-logged-in users see a login modal first
- 👁️ **View Only** — Shared chats are read-only for other users
- 📌 **Visual Indicator** — Shared chats show a special icon in sidebar

### Performance
- ⚡ **Redis Caching** — Chat data cached with 5-minute TTL (Upstash)
- 🔄 **Smart Invalidation** — Cache auto-refreshes on data changes
- 📦 **In-Memory Fallback** — Works without Redis (per-instance cache)

---

## 🛠️ Tech Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| **React 18** | UI framework |
| **Vite** | Build tool & dev server |
| **React Router v7** | Client-side routing |
| **TanStack Query** | Server state management & caching |
| **Clerk** | Authentication UI & session |
| **react-markdown** | Markdown rendering |
| **remark-gfm** | GitHub Flavored Markdown (tables, etc.) |
| **ImageKit.io** | Image upload & CDN |
| **OGL** | WebGL animated background |

### Backend (Python/FastAPI)
| Technology | Purpose |
|------------|---------|
| **FastAPI** | Async web framework |
| **SQLAlchemy** | ORM with async PostgreSQL |
| **psycopg** | PostgreSQL async driver |
| **Groq** | LLM inference API (GPT-OSS-120B) |
| **Redis** | Caching layer (Upstash) |
| **Pydantic** | Data validation & settings |
| **PyJWT** | JWT token decoding |

### Infrastructure
| Service | Purpose |
|---------|---------|
| **Vercel** | Frontend deployment |
| **Render** | Backend deployment |
| **Supabase** | PostgreSQL database |
| **Upstash** | Redis caching |
| **Clerk** | Authentication |
| **Groq** | AI model inference |
| **ImageKit** | Image hosting |

---

## 📁 Project Structure

```
chatgpt-clone/
├── backend/
│   ├── main.py                    # FastAPI entry point
│   ├── settings.py                # Environment configuration
│   ├── database.py                # SQLAlchemy async engine
│   ├── models.py                  # Database models (Chat, UserChat)
│   ├── schemas.py                 # Pydantic request/response schemas
│   ├── routes/
│   │   ├── chats.py               # Chat CRUD + streaming + feedback
│   │   ├── userchats.py           # User chat list
│   │   └── upload.py              # ImageKit upload auth
│   └── services/
│       ├── auth.py                # JWT authentication
│       ├── groq_chat.py           # AI streaming service
│       ├── groq_title.py          # Auto title generation
│       ├── cache.py               # Redis + in-memory cache
│       └── imagekit.py            # ImageKit params
│
├── client/
│   ├── src/
│   │   ├── main.jsx               # App entry & router
│   │   ├── layouts/
│   │   │   ├── rootLayout/        # Clerk + Query providers
│   │   │   └── dashboardLayouts/  # Sidebar + auth guard
│   │   ├── routes/
│   │   │   ├── homepage/          # Landing page
│   │   │   ├── chatpage/          # Chat view
│   │   │   ├── sharedChatPage/    # Shared chat views
│   │   │   └── ...
│   │   └── components/
│   │       ├── newPrompt/         # Messages + actions
│   │       ├── chatInput/         # Input form
│   │       ├── chatList/          # Sidebar list
│   │       ├── upload/            # Image upload
│   │       └── darkVeil/          # WebGL background
│   └── package.json
│
└── render.yaml                    # Render deployment config
```

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- PostgreSQL database
- Redis (optional, falls back to in-memory)

### 1. Clone the repository
```bash
git clone https://github.com/your-username/chatgpt-clone.git
cd chatgpt-clone
```

### 2. Setup Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file:
```env
DATABASE_URL=postgresql+psycopg://user:pass@host:5432/dbname
GROQ_API_KEY=gsk_xxxxx
CLERK_SECRET_KEY=sk_test_xxxxx
IMAGEKIT_URL_PUBLIC_KEY=public_xxxxx
IMAGEKIT_URL_PRIVATE_KEY=private_xxxxx
IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/xxxxx
CLIENT_URL=http://localhost:5173
REDIS_URL=rediss://default:password@host:6379
CACHE_TTL=300
CACHE_ENABLED=true
```

Start the server:
```bash
uvicorn main:app --reload --port 8000
```

### 3. Setup Frontend
```bash
cd client
npm install
```

Create `.env` file:
```env
VITE_API_URL=http://localhost:8000
VITE_CLERK_PUBLISHABLE_KEY=pk_test_xxxxx
VITE_IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/xxxxx
VITE_IMAGEKIT_URL_PUBLIC_KEY=public_xxxxx
```

Start the dev server:
```bash
npm run dev
```

### 4. Open
Visit [http://localhost:5173](http://localhost:5173)

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/api/chats` | Create new chat |
| `GET` | `/api/chats/{id}` | Get chat by ID |
| `GET` | `/api/chats/shared/{id}` | Get shared chat |
| `POST` | `/api/chats/{id}/message` | Send message (SSE streaming) |
| `PUT` | `/api/chats/{id}/feedback` | Update like/dislike |
| `PUT` | `/api/chats/{id}/share` | Toggle share status |
| `PUT` | `/api/chats/{id}/edit` | Edit message |
| `GET` | `/api/userchats` | Get user's chat list |
| `GET` | `/api/upload` | Get ImageKit upload auth |

---

## 🗄️ Database Schema

### chats
| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | String | Clerk user ID |
| `history` | JSONB | Chat messages array |
| `is_shared` | Boolean | Share status |
| `feedback` | JSONB | Like/dislike per message |
| `edit_history` | JSONB | Edit history records |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last update timestamp |

### user_chats
| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Auto-increment ID |
| `user_id` | String | Clerk user ID |
| `chat_id` | UUID | Foreign key to chats |
| `title` | Text | Auto-generated title |
| `is_shared` | Boolean | Share status |
| `created_at` | DateTime | Creation timestamp |

---

## ⚡ Caching Strategy

| Cache Key Pattern | TTL | Description |
|-------------------|-----|-------------|
| `boostai:chat:{userId}:{chatId}` | 5 min | Individual chat data |
| `boostai:userchats:{userId}` | 5 min | User's chat list |
| `boostai:shared_chat:{chatId}` | 10 min | Shared chat data |

**Cache is invalidated** on: chat creation, message send, feedback update, share toggle, message edit.

---

## 🌐 Deployment

### Frontend (Vercel)
- Connected to GitHub repo
- Auto-deploys on push to `main`
- SPA rewrite rules for React Router

### Backend (Render)
- Python service with auto-deploy
- Runs `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Auto-migration on startup

### Database (Supabase)
- PostgreSQL 16
- Connection pooling via pooler

### Cache (Upstash)
- Redis 5.2 with TLS
- Serverless, pay-per-request

---

## 🔧 Available Scripts

### Frontend
```bash
npm run dev      # Start dev server
npm run build    # Production build
npm run preview  # Preview build
npm run lint     # Lint code
```

### Backend
```bash
uvicorn main:app --reload          # Dev server with hot reload
uvicorn main:app --port 8000       # Production server
python migrate.py                   # Run migrations manually
```

---

## 👨‍💻 Author

**Abhijeet Bhale**
- GitHub: [@abhijeetBhale](https://github.com/abhijeetBhale)
- LinkedIn: [Abhijeet Bhale](https://linkedin.com/in/abhijeetbhale7)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
