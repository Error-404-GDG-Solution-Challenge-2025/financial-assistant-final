# Financial Assistant

A comprehensive AI-powered financial assistant built to help users with investment decisions, financial analysis, and market research through natural language conversation.

## 📊 Features

- **Natural Language Financial Queries**: Ask questions about stocks, market trends, company performance, and investment strategies in plain English.
- **Real-time Financial Data**: Access up-to-date stock prices, company fundamentals, analyst recommendations, and financial metrics.
- **Deep Research Capabilities**: Toggle advanced research mode to automatically decompose complex queries into sub-questions for comprehensive analysis.
- **Knowledge Base Integration**: Local vector storage of financial domain knowledge for rapid access to fundamental concepts.
- **Web Research Integration**: Dynamic web search using Tavily to supplement local knowledge with the latest financial news and information.
- **Conversational Memory**: Persistent chat history allowing for contextual follow-up questions and continuity between sessions.
- **Modern React Frontend**: Clean, intuitive chat interface with dark mode and mobile responsiveness.
- **Authentication**: User login/sign-up functionality with Firebase authentication.

## 🛠️ Technologies Used

### Backend

- **Python** with FastAPI/Streamlit for server implementation
- **Langchain** for orchestrating LLMs and agent workflows
- **Agno** framework for agent creation and tool calling
- **FAISS/Chroma** vector database for knowledge storage
- **YFinance** API for financial data retrieval
- **Tavily API** for web search capabilities
- **Google Gemini API** LLMs for natural language understanding and generation

### Frontend

- **React** for UI components and state management
- **Material-UI** for design components and theming
- **Firebase** for authentication and user management
- **Axios** for API communication

## 🏗️ Architecture

### Core Components

1. **Knowledge Retrieval System**

   - Vector database storing financial domain knowledge
   - Relevance grading to assess retrieved document quality
   - Dynamic retrieval-augmented generation (RAG) for accurate responses

2. **Deep Research Engine**

   - Query decomposition into researchable sub-questions
   - Recursive research with configurable depth limits
   - Parallel processing of sub-questions
   - Synthesis of findings into coherent responses

3. **Financial Data Integration**

   - Real-time stock price and performance metrics
   - Company fundamentals and business analysis
   - Analyst recommendations and forecasts
   - Market trends and sector analysis

4. **Web Processing Pipeline**

   - Small talk detection to handle non-financial queries
   - Relevance assessment for determining search needs
   - Web search for timely information through Tavily

5. **UI/UX Layer**
   - Chat interface with message history
   - Session management and conversation persistence
   - Authentication and user profile management
   - Deep research mode toggle for user control

### Data Flow

1. User submits a query through the React frontend
2. Backend processes the query through:
   - Small talk detection
   - RAG-based knowledge retrieval
   - Relevance grading
   - Optional deep research (if enabled)
   - Real-time financial data lookup
   - Web search when necessary
3. Results are synthesized into a comprehensive response
4. Response is returned to frontend and displayed
5. Conversation history is updated and persisted

## 🚀 Setup and Installation

### Prerequisites

- Python 3.9+
- Node.js 18+
- API keys for external services:
  - Tavily API
  - OpenAI/Claude API
  - Firebase project credentials

### Backend Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/financial-assistant-final.git
   cd financial-assistant-final/final_backend
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the `final_backend` directory with:

   ```
   TAVILY_API_KEY=your-tavily-api-key
   OPENAI_API_KEY=your-openai-api-key
   # Add any other API keys needed
   ```

5. Initialize the vector database (if not already present):

   ```bash
   python ingest.py
   ```

6. Start the backend server:

   ```bash
   # For Streamlit interface
   streamlit run frontend.py

   # For FastAPI server (if implementing the React frontend)
   uvicorn run:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:

   ```bash
   cd ../Frontend_React
   ```

2. Install dependencies:

   ```bash
   npm install
   # or
   pnpm install
   ```

3. Set up Firebase configuration:
   Create or update `src/firebase.js` with your Firebase project credentials.

4. Start the development server:

   ```bash
   npm start
   # or
   pnpm start
   ```

5. Open your browser and navigate to `http://localhost:3000`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.
