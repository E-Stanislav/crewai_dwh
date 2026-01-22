"""
DWH Project Analyzer - Streamlit Chat Interface

A multi-agent system for analyzing DWH projects using CrewAI.
"""

import os
# Disable CrewAI telemetry before importing crewai
os.environ["CREWAI_TELEMETRY"] = "false"
os.environ["OTEL_SDK_DISABLED"] = "true"

import streamlit as st
from datetime import datetime
from pathlib import Path

from schemas.config import LLMProvider, LLMConfig
from schemas.messages import ChatMessage, MessageRole, CrewRequest, AnalysisMode
from config.llm_config import LLM_MODELS
from config.settings import settings
from crew.project_crew import ProjectAnalyzerCrew


# Page configuration
st.set_page_config(
    page_title="DWH Project Analyzer",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better chat styling
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    }
    
    .main-header {
        background: linear-gradient(90deg, #e94560 0%, #0f3460 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0;
    }
    
    .sub-header {
        color: #a0a0a0;
        font-size: 1rem;
        margin-top: 0;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 0.75rem;
        margin-bottom: 1rem;
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .user-message {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        border-left: 4px solid #e94560;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #1a1a2e 0%, #2d2d44 100%);
        border-left: 4px solid #4ecca3;
    }
    
    .sidebar .stSelectbox label, .sidebar .stTextInput label {
        color: #ffffff;
        font-weight: 600;
    }
    
    .mode-button {
        transition: all 0.2s ease;
    }
    
    .stButton>button {
        background: linear-gradient(90deg, #e94560 0%, #0f3460 100%);
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(233, 69, 96, 0.4);
    }
    
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-ready {
        background: #4ecca3;
        box-shadow: 0 0 8px #4ecca3;
    }
    
    .status-working {
        background: #ffd93d;
        box-shadow: 0 0 8px #ffd93d;
        animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .info-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 0.75rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    code {
        background: rgba(233, 69, 96, 0.1);
        padding: 0.2rem 0.4rem;
        border-radius: 0.25rem;
        color: #e94560;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "crew" not in st.session_state:
        st.session_state.crew = None
    
    if "project_configured" not in st.session_state:
        st.session_state.project_configured = False


def render_sidebar():
    """Render the sidebar with settings."""
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        # Project Selection
        st.markdown("### 📁 Project")
        
        # Load projects from yaml
        projects = settings.load_projects()
        
        if projects:
            # Create options for selectbox
            project_options = {p.name: p.path for p in projects}
            project_names = list(project_options.keys())
            
            selected_project = st.selectbox(
                "Select Project",
                options=project_names,
                index=0,
                help="Select a project from projects.yaml"
            )
            
            project_path = project_options[selected_project]
            
            # Show selected path
            st.caption(f"📂 `{project_path}`")
        else:
            st.warning("⚠️ No projects found in projects.yaml")
            project_path = st.text_input(
                "Project Path",
                value=".",
                help="Path to the DWH project to analyze",
                placeholder="/path/to/your/dbt/project"
            )
        
        # Validate path
        path_valid = Path(project_path).exists() if project_path else False
        if project_path:
            if path_valid:
                st.success(f"✅ Path exists")
            else:
                st.error(f"❌ Path not found")
        
        st.markdown("---")
        
        # LLM Settings
        st.markdown("### 🤖 LLM Configuration")
        
        provider = st.selectbox(
            "Provider",
            options=[p.value for p in LLMProvider],
            index=0,
            format_func=lambda x: {
                "openai": "🟢 OpenAI",
                "anthropic": "🟣 Anthropic", 
                "ollama": "🦙 Ollama (Local)",
                "openrouter": "🌐 OpenRouter",
                "zai": "⚡ z.ai"
            }.get(x, x)
        )
        
        # Get available models for selected provider
        available_models = LLM_MODELS.get(provider, ["default"])
        model = st.selectbox(
            "Model",
            options=available_models,
            index=0
        )
        
        # API Key input (if needed)
        api_key = None
        base_url = None
        
        if provider in ["openai", "anthropic", "openrouter", "zai"]:
            env_key = {
                "openai": settings.OPENAI_API_KEY,
                "anthropic": settings.ANTHROPIC_API_KEY,
                "openrouter": settings.OPENROUTER_API_KEY,
                "zai": settings.ZAI_API_KEY,
            }.get(provider)
            
            if env_key:
                st.info(f"✅ API key loaded from environment")
            else:
                api_key = st.text_input(
                    "API Key",
                    type="password",
                    help=f"Enter your {provider} API key"
                )
        
        if provider == "ollama":
            base_url = st.text_input(
                "Ollama URL",
                value=settings.OLLAMA_BASE_URL,
                help="URL to your Ollama instance"
            )
        
        if provider == "zai" and not settings.ZAI_BASE_URL:
            base_url = st.text_input(
                "z.ai Base URL",
                help="URL to z.ai API"
            )
        
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1,
            help="Higher = more creative, Lower = more focused"
        )
        
        st.markdown("---")
        
        # Analysis Mode
        st.markdown("### 🎯 Analysis Mode")
        mode = st.radio(
            "Select mode",
            options=["ask", "analyze", "docs", "arch"],
            format_func=lambda x: {
                "ask": "💬 Ask Question",
                "analyze": "🔍 Code Review",
                "docs": "📝 Generate Docs",
                "arch": "🏗️ Architecture"
            }.get(x, x),
            help="Choose what type of analysis to perform"
        )
        
        st.markdown("---")
        
        # Initialize/Update Crew button
        if st.button("🚀 Initialize Crew", use_container_width=True, disabled=not path_valid):
            try:
                llm_config = LLMConfig(
                    provider=LLMProvider(provider),
                    model=model,
                    api_key=api_key,
                    base_url=base_url,
                    temperature=temperature
                )
                
                with st.spinner("Initializing agents..."):
                    st.session_state.crew = ProjectAnalyzerCrew(
                        project_path=project_path,
                        llm_config=llm_config
                    )
                    st.session_state.project_configured = True
                    st.session_state.current_mode = mode
                
                st.success("✅ Crew initialized!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        # Show current status
        if st.session_state.project_configured:
            st.markdown("""
            <div class="info-card">
                <span class="status-indicator status-ready"></span>
                <strong>Crew Ready</strong>
            </div>
            """, unsafe_allow_html=True)
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        return mode


def render_chat():
    """Render the chat interface."""
    # Header
    st.markdown('<h1 class="main-header">🏗️ DWH Project Analyzer</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Multi-agent AI system for analyzing Data Warehouse projects</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display messages
        for msg in st.session_state.messages:
            if msg.role == MessageRole.USER:
                with st.chat_message("user", avatar="👤"):
                    st.markdown(msg.content)
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(msg.content)
    
    return chat_container


def process_message(user_input: str, mode: str):
    """Process user message and get response from crew."""
    # Add user message
    user_msg = ChatMessage(
        role=MessageRole.USER,
        content=user_input
    )
    st.session_state.messages.append(user_msg)
    
    # Check if crew is configured
    if not st.session_state.project_configured or st.session_state.crew is None:
        error_msg = ChatMessage(
            role=MessageRole.ASSISTANT,
            content="⚠️ Please configure the project and initialize the crew first using the sidebar settings."
        )
        st.session_state.messages.append(error_msg)
        return
    
    # Create request
    request = CrewRequest(
        query=user_input,
        mode=AnalysisMode(mode)
    )
    
    # Get response
    try:
        with st.spinner("🔄 Agents are working..."):
            response = st.session_state.crew.run(request)
        
        if response.success:
            result_content = response.result
            
            # Add metadata
            metadata = f"\n\n---\n*Agents: {', '.join(response.agents_used)} | Time: {response.execution_time:.1f}s*"
            
            assistant_msg = ChatMessage(
                role=MessageRole.ASSISTANT,
                content=result_content + metadata
            )
        else:
            assistant_msg = ChatMessage(
                role=MessageRole.ASSISTANT,
                content=f"❌ Error: {response.error}"
            )
        
        st.session_state.messages.append(assistant_msg)
        
    except Exception as e:
        error_msg = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=f"❌ An error occurred: {str(e)}"
        )
        st.session_state.messages.append(error_msg)


def main():
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar and get current mode
    current_mode = render_sidebar()
    
    # Render chat interface
    render_chat()
    
    # Chat input
    mode_labels = {
        "ask": "Ask a question about your DWH project...",
        "analyze": "What code should I review?",
        "docs": "What should I document?",
        "arch": "What architecture should I analyze?"
    }
    
    if user_input := st.chat_input(mode_labels.get(current_mode, "Type your message...")):
        process_message(user_input, current_mode)
        st.rerun()


if __name__ == "__main__":
    main()
