# JARVIS 2.0 Web Interface

Modern, responsive web interface for JARVIS 2.0 AI Assistant.

## Features

- �� **Authentication** - Secure login and registration
- 💬 **Real-time Chat** - Stream AI responses in real-time
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- 🎨 **Modern UI** - Beautiful gradient design with dark mode support
- ⚡ **Fast** - Built with Next.js 14 and React Server Components
- 🔒 **Secure** - JWT authentication with auto token refresh

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- JARVIS 2.0 API Server running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Create environment file
cp .env.example .env.local

# Edit .env.local and set your API URL
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Run development server
npm run dev
```

Open http://localhost:3000 in your browser.

## Available Scripts

- `npm run dev` - Start development server (http://localhost:3000)
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## Project Structure

```
web/
├── app/                    # Next.js App Router
│   ├── auth/              # Authentication pages
│   │   ├── login/         # Login page
│   │   └── register/      # Registration page
│   ├── chat/              # Chat interface
│   ├── settings/          # Settings page
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page (redirects)
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── ui/               # UI components
│   ├── chat/             # Chat components
│   └── layout/           # Layout components
├── lib/                   # Utilities
│   ├── api/              # API client
│   │   └── client.ts     # HTTP client with auth
│   └── store/            # Zustand stores
│       ├── auth.ts       # Auth state
│       └── chat.ts       # Chat state
├── types/                 # TypeScript types
│   └── index.ts          # Shared types
├── public/               # Static assets
├── package.json          # Dependencies
├── tsconfig.json         # TypeScript config
├── tailwind.config.ts    # Tailwind config
└── next.config.mjs       # Next.js config
```

## Features Explained

### Authentication

- **Login**: `/auth/login`
- **Register**: `/auth/register`
- JWT tokens stored in localStorage
- Automatic token refresh
- Protected routes redirect to login

### Chat Interface

- **Real-time streaming**: See responses as they're generated
- **Markdown support**: Code blocks, lists, formatting
- **Message history**: All messages saved to conversation
- **Auto-scroll**: Automatically scrolls to new messages
- **Keyboard shortcuts**: Enter to send, Shift+Enter for new line

### Settings

- **Account info**: View your profile
- **System status**: CPU, memory, disk usage
- **Model selection**: Switch between AI models
- **Configuration**: View current settings

## Environment Variables

Create `.env.local` file:

```env
# API Server URL (required)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional
# NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## API Integration

The web interface connects to the JARVIS API server:

### Endpoints Used

- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/chat/completions` - Send message
- `POST /api/v1/chat/completions/stream` - Stream response
- `GET /api/v1/chat/conversations` - List conversations
- `GET /api/v1/system/status` - System metrics
- `GET /api/v1/system/models` - Available models
- `POST /api/v1/system/models/{name}` - Switch model

### Authentication Flow

1. User enters credentials
2. POST to /api/v1/auth/login
3. Receive access_token and refresh_token
4. Store tokens in localStorage
5. Add Authorization header to all requests
6. Auto-refresh when token expires

## Deployment

### Build for Production

```bash
npm run build
npm start
```

### Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Deploy to Netlify

```bash
# Build
npm run build

# Deploy dist folder to Netlify
```

### Docker

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

```bash
docker build -t jarvis-web .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://your-api jarvis-web
```

## Customization

### Theming

Edit `app/globals.css` to customize colors:

```css
:root {
  --primary: 221.2 83.2% 53.3%;  /* Blue */
  --secondary: 210 40% 96.1%;     /* Light gray */
  /* ... */
}
```

### Components

UI components in `components/ui/` can be customized or replaced.

### Store

State management in `lib/store/` using Zustand.

## Troubleshooting

### Can't connect to API

```
Error: Failed to fetch
```

**Solution**: Make sure API server is running on the correct URL.

```bash
# Check API server
curl http://localhost:8000/health

# Update .env.local with correct URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Authentication fails

```
Error: 401 Unauthorized
```

**Solution**: Check credentials or clear localStorage.

```javascript
// In browser console
localStorage.clear();
window.location.reload();
```

### Build errors

```
Error: Module not found
```

**Solution**: Reinstall dependencies.

```bash
rm -rf node_modules package-lock.json
npm install
```

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State**: Zustand
- **HTTP**: Axios
- **Markdown**: react-markdown
- **Icons**: Lucide React

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## License

MIT

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/UdaySoni32/Jarvis-2.0/issues
- Documentation: See main project README

---

**Version**: 2.0.0
**Last Updated**: April 8, 2026
