"""
Streamlit UI for SQL Fight Club - THE VISUAL SPECTACLE
"""
import streamlit as st
import time
from datetime import datetime

from app.config import (
    STREAMLIT_PAGE_TITLE,
    STREAMLIT_PAGE_ICON,
    STREAMLIT_LAYOUT,
    DEFAULT_ROUNDS,
    MAX_ROUNDS,
    MIN_ROUNDS,
    AGENT_A_NAME,
    AGENT_B_NAME,
    OPENAI_API_KEY,
    DB_SEED_SIZE,
)
from app.db.duckdb_init import create_db_connection, seed_database
from app.agents.openai_agent import OpenAIAgent
from app.core.fight_manager import FightManager


# Page config
st.set_page_config(
    page_title=STREAMLIT_PAGE_TITLE,
    page_icon=STREAMLIT_PAGE_ICON,
    layout=STREAMLIT_LAYOUT
)

# Custom CSS for extra drama
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 1rem;
    }
    .round-header {
        font-size: 2rem;
        font-weight: bold;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .agent-a {
        background-color: rgba(255, 107, 107, 0.1);
        border-left: 5px solid #FF6B6B;
    }
    .agent-b {
        background-color: rgba(78, 205, 196, 0.1);
        border-left: 5px solid #4ECDC4;
    }
    .winner-banner {
        font-size: 3rem;
        text-align: center;
        padding: 2rem;
        background: linear-gradient(45deg, gold, orange);
        border-radius: 15px;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    .stButton>button {
        width: 100%;
        height: 4rem;
        font-size: 1.5rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'fight_started' not in st.session_state:
        st.session_state.fight_started = False
    if 'fight_result' not in st.session_state:
        st.session_state.fight_result = None
    if 'db_connection' not in st.session_state:
        st.session_state.db_connection = None


def render_header():
    """Render the dramatic header"""
    st.markdown('<h1 class="main-header">⚔️ SQL FIGHT CLUB 🦆</h1>', unsafe_allow_html=True)
    st.markdown("### *Two AI agents enter. Only SELECT statements leave.*")
    st.markdown("---")


def render_config_sidebar():
    """Render the configuration sidebar"""
    with st.sidebar:
        st.header("⚙️ Fight Configuration")
        
        # API Key check
        api_key = st.text_input(
            "OpenAI API Key",
            value=OPENAI_API_KEY,
            type="password",
            help="Enter your OpenAI API key"
        )
        
        if not api_key:
            st.error("⚠️ No API key found! Add it to .env or enter above.")
            st.stop()
        
        # Fight settings
        num_rounds = st.slider(
            "Number of Rounds",
            min_value=MIN_ROUNDS,
            max_value=MAX_ROUNDS,
            value=DEFAULT_ROUNDS,
            help="How many rounds should the agents battle?"
        )
        
        db_size = st.number_input(
            "Database Size (rows per table)",
            min_value=100,
            max_value=10000,
            value=DB_SEED_SIZE,
            step=100,
            help="More data = more chaos"
        )
        
        random_seed = st.number_input(
            "Random Seed",
            min_value=0,
            max_value=99999,
            value=42,
            help="For reproducible chaos"
        )
        
        st.markdown("---")
        st.markdown("### 🎭 The Fighters")
        st.markdown(f"**{AGENT_A_NAME}**")
        st.markdown(f"**{AGENT_B_NAME}**")
        
        return api_key, num_rounds, db_size, random_seed


def render_round(round_data, agent_color):
    """Render a single round's results"""
    with st.container():
        st.markdown(f'<div class="round-header {agent_color}">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"**Round {round_data.round_number}: {round_data.agent_name}**")
        
        with col2:
            if round_data.success:
                st.markdown(f"✅ **Score: {round_data.score}**")
            else:
                st.markdown("💀 **FAILED**")
        
        with col3:
            if round_data.success:
                st.markdown(f"⏱️ {round_data.execution_time:.2f}s")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Query
        if round_data.query:
            with st.expander("📜 SQL Query", expanded=round_data.success):
                st.code(round_data.query, language="sql")
        
        # Results or error
        if round_data.success:
            st.success(f"✨ Returned {round_data.result_row_count} rows")
            
            if round_data.result_preview:
                with st.expander("🔍 Result Preview (first 10 rows)"):
                    st.dataframe(round_data.result_preview)
        else:
            st.error(f"💥 {round_data.error}")
        
        st.markdown("---")


def run_fight_with_live_updates(manager: FightManager):
    """Run the fight and show live updates"""
    
    # Create containers for live updates
    status_container = st.empty()
    rounds_container = st.container()
    
    # Score tracking
    score_col1, score_col2 = st.columns(2)
    score_a = score_col1.empty()
    score_b = score_col2.empty()
    
    agent_a_total = 0
    agent_b_total = 0
    
    status_container.info("🔥 FIGHT STARTING...")
    time.sleep(1)
    
    # Run rounds
    for round_num in range(1, manager.num_rounds + 1):
        # Agent A
        status_container.warning(f"⚔️ Round {round_num} - {AGENT_A_NAME} is thinking...")
        
        challenge_a = manager._generate_challenge(round_num, "A", None)
        round_a = manager.execute_round(
            round_num=round_num,
            agent=manager.agent_a,
            agent_name=AGENT_A_NAME,
            challenge=challenge_a
        )
        
        agent_a_total += round_a.score
        
        with rounds_container:
            render_round(round_a, "agent-a")
        
        score_a.metric(AGENT_A_NAME, agent_a_total, round_a.score)
        time.sleep(0.5)
        
        # Agent B
        status_container.info(f"⚔️ Round {round_num} - {AGENT_B_NAME} is thinking...")
        
        challenge_b = manager._generate_challenge(round_num, "B", round_a.query if round_a.success else None)
        round_b = manager.execute_round(
            round_num=round_num,
            agent=manager.agent_b,
            agent_name=AGENT_B_NAME,
            challenge=challenge_b,
            previous_query=round_a.query if round_a.success else None
        )
        
        agent_b_total += round_b.score
        
        with rounds_container:
            render_round(round_b, "agent-b")
        
        score_b.metric(AGENT_B_NAME, agent_b_total, round_b.score)
        time.sleep(0.5)
    
    # Determine winner
    status_container.empty()
    
    if agent_a_total > agent_b_total:
        winner = AGENT_A_NAME
        emoji = "🔴"
    elif agent_b_total > agent_a_total:
        winner = AGENT_B_NAME
        emoji = "🔵"
    else:
        winner = "IT'S A TIE"
        emoji = "🤝"
    
    st.markdown(f'<div class="winner-banner">{emoji} {winner} WINS! {emoji}</div>', unsafe_allow_html=True)
    st.balloons()


def main():
    """Main Streamlit app"""
    init_session_state()
    render_header()
    
    # Sidebar config
    api_key, num_rounds, db_size, random_seed = render_config_sidebar()
    
    # Main area
    if not st.session_state.fight_started:
        st.info("👈 Configure your fight in the sidebar, then hit START FIGHT!")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🚀 START FIGHT", type="primary"):
                with st.spinner("🦆 Initializing DuckDB arena..."):
                    # Create database
                    st.session_state.db_connection = create_db_connection()
                    seed_database(st.session_state.db_connection, db_size, random_seed)
                    
                    # Create agents
                    agent_a = OpenAIAgent(api_key=api_key, agent_name=AGENT_A_NAME)
                    agent_b = OpenAIAgent(api_key=api_key, agent_name=AGENT_B_NAME)
                    
                    # Create fight manager
                    manager = FightManager(
                        agent_a=agent_a,
                        agent_b=agent_b,
                        db_connection=st.session_state.db_connection,
                        num_rounds=num_rounds
                    )
                    
                    st.session_state.fight_started = True
                    st.rerun()
    
    else:
        # Fight is running
        agent_a = OpenAIAgent(api_key=api_key, agent_name=AGENT_A_NAME)
        agent_b = OpenAIAgent(api_key=api_key, agent_name=AGENT_B_NAME)
        
        manager = FightManager(
            agent_a=agent_a,
            agent_b=agent_b,
            db_connection=st.session_state.db_connection,
            num_rounds=num_rounds
        )
        
        run_fight_with_live_updates(manager)
        
        # Reset button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 NEW FIGHT", type="primary"):
                st.session_state.fight_started = False
                st.session_state.fight_result = None
                if st.session_state.db_connection:
                    st.session_state.db_connection.close()
                st.session_state.db_connection = None
                st.rerun()


if __name__ == "__main__":
    main()
