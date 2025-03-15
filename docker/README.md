# Food Event Chatbot

A chatbot system that processes iCal data to find events with free food and allows users to query this information.

## Features

- Process iCal calendar data to extract event information
- Analyze events to determine likelihood of free food
- Upload processed data to xTrace for knowledge retrieval
- User-friendly chat interface to query about food events
- Deployable via Docker

## Architecture

The system consists of two main components:

1. **Backend** (FastAPI):
   - Processes calendar data
   - Analyzes events using Gemini Flash 2.0
   - Uploads data to xTrace
   - Handles queries from the frontend

2. **Frontend** (Streamlit):
   - User interface for calendar processing
   - Chat interface to query about events
   - Status monitoring

## Setup

### Prerequisites

- Docker and Docker Compose
- Gemini Flash 2.0 API key
- xTrace API key

### Environment Variables

Create a `.env` file in the root directory:

```
GEMINI_API_KEY=your_gemini_api_key_here
XTRACE_API_KEY=your_xtrace_api_key_here
XTRACE_API_URL=https://beta0-api.xtrace.ai/v1
```

### Running the Application

1. Build and start the containers:

```bash
docker-compose up -d
```

2. Access the frontend:
   - Open your browser and go to `http://localhost:8501`

3. Process calendar data:
   - Enter the iCal URL in the sidebar (a default URL is provided)
   - Click "Process Calendar" button
   - Wait for processing to complete

4. Query about food events:
   - Once processing is complete, you can chat with the bot about food events

## Usage Flow

1. **First Run**:
   - The system processes the calendar data
   - Analyzes events for free food likelihood
   - Uploads the results to xTrace

2. **Second Run and Beyond**:
   - The system queries xTrace with user questions
   - Returns relevant information about food events

## API Endpoints

- `GET /`: API health check
- `GET /status`: Check processing status
- `POST /process`: Process calendar data
- `POST /query`: Query for information about events

## Development

### Project Structure

```
project.chatbot/
│
├── backend/
│   ├── app.py                 # FastAPI application
│   ├── ical_processor.py      # iCal data processing
│   ├── inference_provider.py  # Gemini Flash 2.0 integration
│   ├── xtrace_client.py       # xTrace API client
│   └── requirements.txt       # Backend dependencies
│
├── frontend/
│   ├── main.py                # Streamlit frontend
│   ├── components/            # UI components
│   │   └── chat_interface.py  # Chat interface
│   └── requirements.txt       # Frontend dependencies
│
├── shared/
│   └── models.py              # Shared data models
│
├── Dockerfile.backend         # Backend Docker configuration
├── Dockerfile.frontend        # Frontend Docker configuration
├── docker-compose.yml         # Docker compose configuration
└── README.md                  # Project documentation
```

### Local Development

1. Install backend dependencies:

```bash
cd backend
pip install -r requirements.txt
```

2. Install frontend dependencies:

```bash
cd frontend
pip install -r requirements.txt
```

3. Set environment variables:

```bash
export GEMINI_API_KEY=your_gemini_api_key_here
export XTRACE_API_KEY=your_xtrace_api_key_here
```

4. Run the backend:

```bash
cd backend
uvicorn app:app --reload
```

5. Run the frontend:

```bash
cd frontend
streamlit run main.py
```

## Troubleshooting

- If the backend fails to start, check your API keys and network connectivity
- If processing fails, try the "Force Reprocess" button
- Check the Docker logs for more detailed error information:

```bash
docker-compose logs backend
docker-compose logs frontend
```