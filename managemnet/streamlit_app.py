import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path

from config import APP_CONFIG, OLLAMA_CONFIG
from ollama_client import OllamaClient
from repo_analyzer import RepoAnalyzer
from ai_insights import AIInsights
from data_manager import DataManager

# Configure page
st.set_page_config(
    page_title=APP_CONFIG.page_title,
    page_icon=APP_CONFIG.page_icon,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
@st.cache_resource
def init_components():
    return {
        'ollama': OllamaClient(),
        'ai_insights': AIInsights(),
        'data_manager': DataManager()
    }

components = init_components()

def main():
    st.title("🔍 CodeClarity AI")
    st.markdown("*AI-Powered Repository Analysis & Developer Insights*")
    
    # Sidebar
    st.sidebar.title("Configuration")
    
    # Check Ollama status
    if components['ollama'].check_availability():
        st.sidebar.success("✅ Ollama Connected")
        available_models = components['ollama'].get_available_models()
        if available_models:
            st.sidebar.info(f"Models: {len(available_models)} available")
    else:
        st.sidebar.error("❌ Ollama Not Available")
        st.sidebar.markdown("Please ensure Ollama is running on localhost:11434")
        return
    
    # Main interface
    tabs = st.tabs(["📊 Repository Analysis", "👥 Developer Insights", "🤖 AI Chat", "📈 Reports"])
    
    with tabs[0]:
        repository_analysis()
    
    with tabs[1]:
        developer_insights()
    
    with tabs[2]:
        ai_chat_interface()
    
    with tabs[3]:
        reports_interface()

def repository_analysis():
    """Repository analysis interface"""
    st.header("Repository Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        repo_url = st.text_input(
            "GitHub Repository URL",
            placeholder="https://github.com/user/repository",
            help="Enter the GitHub repository URL to analyze"
        )
    
    with col2:
        max_commits = st.number_input("Max Commits", min_value=10, max_value=500, value=100)
    
    if st.button("🔍 Analyze Repository", type="primary"):
        if not repo_url:
            st.error("Please enter a repository URL")
            return
        
        analyze_repository(repo_url, max_commits)

def analyze_repository(repo_url: str, max_commits: int):
    """Perform repository analysis"""
    # Extract repo name
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    repo_path = Path(APP_CONFIG.repos_dir) / repo_name
    
    with st.spinner(f"Analyzing repository: {repo_name}..."):
        # Initialize analyzer
        analyzer = RepoAnalyzer(str(repo_path))
        
        # Clone/open repository
        if not analyzer.clone_or_open_repo(repo_url):
            st.error("Failed to clone repository. Please check the URL and try again.")
            return
        
        # Get analysis data
        commits_df = analyzer.get_commits_data(max_commits)
        dev_stats = analyzer.get_developer_stats()
        file_analysis = analyzer.get_file_analysis()
        recent_activity = analyzer.get_recent_activity()
        
        # Cache results
        components['data_manager'].save_analysis_data(repo_name, commits_df, dev_stats, file_analysis)
        
        # Store in session state
        st.session_state.current_repo = repo_name
        st.session_state.commits_df = commits_df
        st.session_state.dev_stats = dev_stats
        st.session_state.file_analysis = file_analysis
        st.session_state.recent_activity = recent_activity
    
    st.success(f"✅ Analysis complete for {repo_name}")
    display_repository_overview()

def display_repository_overview():
    """Display repository analysis results"""
    if 'commits_df' not in st.session_state:
        st.info("No repository data loaded. Please analyze a repository first.")
        return
    
    commits_df = st.session_state.commits_df
    dev_stats = st.session_state.dev_stats
    file_analysis = st.session_state.file_analysis
    recent_activity = st.session_state.recent_activity
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Commits", len(commits_df))
    with col2:
        st.metric("Contributors", commits_df['author'].nunique() if not commits_df.empty else 0)
    with col3:
        st.metric("Files Types", len(file_analysis))
    with col4:
        st.metric("Recent Commits (30d)", recent_activity.get('total_commits', 0))
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Commit timeline
        if not commits_df.empty:
            # Fix timezone issue in visualization
            daily_commits = commits_df.groupby(commits_df['date'].dt.date).size()
            fig = px.line(x=daily_commits.index, y=daily_commits.values,
                         title="Commit Activity Over Time",
                         labels={'x': 'Date', 'y': 'Commits'})
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # File types distribution
        if file_analysis:
            fig = px.pie(values=list(file_analysis.values()), 
                        names=list(file_analysis.keys()),
                        title="File Types Distribution")
            st.plotly_chart(fig, use_container_width=True)
    
    # Developer contributions
    if not dev_stats.empty:
        st.subheader("👥 Developer Contributions")
        
        # Top contributors chart
        top_devs = dev_stats.head(10)
        fig = px.bar(x=top_devs.index, y=top_devs['commits'],
                    title="Top Contributors by Commits",
                    labels={'x': 'Developer', 'y': 'Commits'})
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed stats table
        st.dataframe(dev_stats, use_container_width=True)

def developer_insights():
    """Developer insights interface"""
    st.header("Developer Insights")
    
    if 'dev_stats' not in st.session_state or 'commits_df' not in st.session_state:
        st.info("Please analyze a repository first to see developer insights.")
        return
    
    dev_stats = st.session_state.dev_stats
    commits_df = st.session_state.commits_df
    
    if dev_stats.empty:
        st.warning("No developer data available.")
        return
    
    # Developer selection
    selected_dev = st.selectbox("Select Developer", dev_stats.index.tolist())
    
    if selected_dev:
        display_developer_details(selected_dev, dev_stats, commits_df)
    
    # Generate AI insights for all developers
    if st.button("🤖 Generate AI Insights", type="primary"):
        with st.spinner("Analyzing developer work patterns..."):
            insights = components['ai_insights'].analyze_developer_work(dev_stats, commits_df)
            
            st.subheader("🧠 AI Analysis of Developer Work")
            for dev, insight in insights.items():
                with st.expander(f"👤 {dev}"):
                    st.write(insight)

def display_developer_details(developer: str, dev_stats: pd.DataFrame, commits_df: pd.DataFrame):
    """Display detailed information for selected developer"""
    stats = dev_stats.loc[developer]
    dev_commits = commits_df[commits_df['author'] == developer].head(20)
    
    # Developer metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Commits", int(stats['commits']))
    with col2:
        st.metric("Lines Added", int(stats['insertions']))
    with col3:
        st.metric("Lines Removed", int(stats['deletions']))
    with col4:
        st.metric("Files Modified", int(stats['files_modified']))
    
    # Recent commits
    st.subheader(f"Recent Commits by {developer}")
    if not dev_commits.empty:
        for _, commit in dev_commits.iterrows():
            # Fix timezone display issue
            commit_date = commit['date']
            if pd.isna(commit_date):
                date_str = "Unknown date"
            else:
                date_str = pd.to_datetime(commit_date).strftime('%Y-%m-%d %H:%M')
            
            with st.expander(f"📸 {commit['hash']} - {date_str}"):
                st.write(f"**Message:** {commit['message']}")
                st.write(f"**Changes:** +{commit['insertions']} -{commit['deletions']} lines")
                st.write(f"**Files:** {commit['files_changed']} modified")

def ai_chat_interface():
    """AI chat interface for repository Q&A"""
    st.header("🤖 Ask About Your Repository")
    
    if 'commits_df' not in st.session_state:
        st.info("Please analyze a repository first to enable AI chat.")
        return
    
    # Chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for i, (question, answer) in enumerate(st.session_state.chat_history):
        st.write(f"**You:** {question}")
        st.write(f"**AI:** {answer}")
        st.divider()
    
    # New question input
    question = st.text_input("Ask a question about the repository:", 
                           placeholder="e.g., What has been the main focus of development recently?")
    
    if st.button("Ask AI", type="primary") and question:
        with st.spinner("Thinking..."):
            answer = generate_ai_answer(question)
            st.session_state.chat_history.append((question, answer))
            st.rerun()

def generate_ai_answer(question: str) -> str:
    """Generate AI answer based on repository data"""
    commits_df = st.session_state.commits_df
    dev_stats = st.session_state.dev_stats
    recent_activity = st.session_state.recent_activity
    
    # Prepare context
    context = f"""
    Repository Context:
    - Total commits: {len(commits_df)}
    - Contributors: {commits_df['author'].nunique()}
    - Recent activity: {recent_activity.get('total_commits', 0)} commits in last 30 days
    - Top contributor: {dev_stats.index[0] if not dev_stats.empty else 'Unknown'}
    
    Recent commits:
    {commits_df.head(5)[['author', 'date', 'message']].to_string()}
    
    Question: {question}
    
    Please provide a helpful answer based on the repository data above.
    """
    
    response = components['ollama'].generate(context, task_type="balanced")
    return response or "I'm unable to provide an answer at this time."

def reports_interface():
    """Reports generation interface"""
    st.header("📈 Generate Reports")
    
    if 'commits_df' not in st.session_state:
        st.info("Please analyze a repository first to generate reports.")
        return
    
    # Report type selection
    report_type = st.selectbox(
        "Select Report Type",
        ["Executive Summary", "Developer Performance", "Project Health", "Team Activity"]
    )
    
    if st.button("📄 Generate Report", type="primary"):
        with st.spinner(f"Generating {report_type} report..."):
            report_content = generate_report(report_type)
            
            if report_content:
                st.subheader(f"📋 {report_type} Report")
                st.markdown(report_content)
                
                # Download option
                st.download_button(
                    label="Download Report (Markdown)",
                    data=report_content,
                    file_name=f"{report_type.lower().replace(' ', '_')}_report.md",
                    mime="text/markdown"
                )

def generate_report(report_type: str) -> str:
    """Generate different types of reports"""
    commits_df = st.session_state.commits_df
    dev_stats = st.session_state.dev_stats
    recent_activity = st.session_state.recent_activity
    file_analysis = st.session_state.file_analysis
    repo_name = st.session_state.get('current_repo', 'Repository')
    
    if report_type == "Executive Summary":
        return components['ai_insights'].generate_project_summary(
            commits_df, file_analysis, recent_activity
        )
    
    elif report_type == "Developer Performance":
        insights = components['ai_insights'].analyze_developer_work(dev_stats, commits_df)
        
        report = f"# Developer Performance Report - {repo_name}\n\n"
        report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        
        for dev, insight in insights.items():
            stats = dev_stats.loc[dev]
            report += f"## {dev}\n\n"
            report += f"- **Commits:** {int(stats['commits'])}\n"
            report += f"- **Lines Added:** {int(stats['insertions'])}\n"
            report += f"- **Lines Removed:** {int(stats['deletions'])}\n"
            report += f"- **Files Modified:** {int(stats['files_modified'])}\n\n"
            report += f"**AI Analysis:** {insight}\n\n---\n\n"
        
        return report
    
    elif report_type == "Project Health":
        # Generate project health metrics
        total_commits = len(commits_df)
        active_devs = recent_activity.get('active_developers', 0)
        commit_frequency = recent_activity.get('total_commits', 0) / 30  # per day
        
        health_prompt = f"""
        Assess the health of this software project:
        
        Metrics:
        - Total commits analyzed: {total_commits}
        - Active developers (30d): {active_devs}
        - Average commits per day: {commit_frequency:.1f}
        - Recent lines added: {recent_activity.get('lines_added', 0)}
        - Recent lines removed: {recent_activity.get('lines_removed', 0)}
        
        File types: {', '.join(file_analysis.keys())}
        
        Provide a project health assessment with:
        1. Overall health score (1-10)
        2. Key strengths
        3. Areas of concern
        4. Recommendations
        
        Format as a professional report.
        """
        
        return components['ollama'].generate(health_prompt, task_type="detailed") or "Unable to generate health report."
    
    elif report_type == "Team Activity":
        activity_prompt = f"""
        Generate a team activity report based on this data:
        
        Team Overview:
        - Total contributors: {commits_df['author'].nunique()}
        - Most active: {recent_activity.get('most_active_dev', 'Unknown')}
        - Commits in last 30 days: {recent_activity.get('total_commits', 0)}
        
        Top Contributors:
        {dev_stats.head(5)[['commits', 'insertions', 'deletions']].to_string()}
        
        Provide insights on:
        1. Team collaboration patterns
        2. Workload distribution
        3. Development velocity
        4. Team dynamics observations
        
        Keep it professional and actionable.
        """
        
        return components['ollama'].generate(activity_prompt, task_type="balanced") or "Unable to generate activity report."
    
    return "Report type not supported."

if __name__ == "__main__":
    main()