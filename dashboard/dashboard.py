import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json

st.set_page_config(
    page_title="Bot Detection Dashboard",
    page_icon="🤖",
    layout="wide"
)

class BotDetectionDashboard:
    def __init__(self):
        self.db_path = '../backend/data/interactions.db'
        self.api_url = 'http://localhost:5000/api/stats'

    def get_data_from_db(self):
        """Get data directly from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get interactions
            interactions_df = pd.read_sql_query('''
                SELECT * FROM interactions 
                WHERE timestamp > datetime('now', '-7 days')
                ORDER BY timestamp DESC
            ''', conn)
            
            # Get alerts
            alerts_df = pd.read_sql_query('''
                SELECT * FROM alerts 
                WHERE timestamp > datetime('now', '-7 days')
                ORDER BY timestamp DESC
            ''', conn)
            
            conn.close()
            return interactions_df, alerts_df
            
        except Exception as e:
            st.error(f"Database connection error: {e}")
            return pd.DataFrame(), pd.DataFrame()

    def get_stats_from_api(self):
        """Get statistics from API"""
        try:
            response = requests.get(self.api_url, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except:
            return None

    def create_metrics_cards(self, interactions_df, alerts_df):
        """Create metric cards"""
        col1, col2, col3, col4 = st.columns(4)
        
        total_sessions = len(interactions_df['session_id'].unique()) if not interactions_df.empty else 0
        bot_sessions = len(interactions_df[interactions_df['prediction'] == 'bot']['session_id'].unique()) if not interactions_df.empty else 0
        human_sessions = total_sessions - bot_sessions
        total_alerts = len(alerts_df) if not alerts_df.empty else 0
        
        with col1:
            st.metric("Total Sessions", total_sessions)
        
        with col2:
            st.metric("Bot Sessions", bot_sessions, delta=f"{(bot_sessions/total_sessions*100):.1f}%" if total_sessions > 0 else "0%")
        
        with col3:
            st.metric("Human Sessions", human_sessions, delta=f"{(human_sessions/total_sessions*100):.1f}%" if total_sessions > 0 else "0%")
        
        with col4:
            st.metric("Security Alerts", total_alerts)

    def create_prediction_chart(self, interactions_df):
        """Create prediction distribution chart"""
        if interactions_df.empty:
            st.warning("No interaction data available")
            return
            
        prediction_counts = interactions_df['prediction'].value_counts()
        
        fig = px.pie(
            values=prediction_counts.values,
            names=prediction_counts.index,
            title="Human vs Bot Detection",
            color_discrete_map={'human': '#28a745', 'bot': '#dc3545'}
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def create_confidence_distribution(self, interactions_df):
        """Create confidence score distribution"""
        if interactions_df.empty:
            st.warning("No interaction data available")
            return
            
        fig = px.histogram(
            interactions_df,
            x='confidence',
            color='prediction',
            title="Confidence Score Distribution",
            nbins=20,
            color_discrete_map={'human': '#28a745', 'bot': '#dc3545'}
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def create_risk_score_chart(self, interactions_df):
        """Create risk score analysis"""
        if interactions_df.empty:
            st.warning("No interaction data available")
            return
            
        fig = px.scatter(
            interactions_df,
            x='confidence',
            y='risk_score',
            color='prediction',
            title="Risk Score vs Confidence",
            color_discrete_map={'human': '#28a745', 'bot': '#dc3545'}
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def create_timeline_chart(self, interactions_df):
        """Create timeline of detections"""
        if interactions_df.empty:
            st.warning("No interaction data available")
            return
            
        interactions_df['timestamp'] = pd.to_datetime(interactions_df['timestamp'])
        interactions_df['hour'] = interactions_df['timestamp'].dt.floor('H')
        
        hourly_counts = interactions_df.groupby(['hour', 'prediction']).size().reset_index(name='count')
        
        fig = px.line(
            hourly_counts,
            x='hour',
            y='count',
            color='prediction',
            title="Detection Timeline (Hourly)",
            color_discrete_map={'human': '#28a745', 'bot': '#dc3545'}
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def create_alerts_chart(self, alerts_df):
        """Create alerts analysis"""
        if alerts_df.empty:
            st.warning("No alert data available")
            return
            
        alert_counts = alerts_df['alert_type'].value_counts()
        
        fig = px.bar(
            x=alert_counts.index,
            y=alert_counts.values,
            title="Security Alerts by Type",
            color=alert_counts.values,
            color_continuous_scale='Reds'
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def show_recent_sessions(self, interactions_df):
        """Show recent session data"""
        if interactions_df.empty:
            st.warning("No session data available")
            return
            
        # Get latest session for each session_id
        latest_sessions = interactions_df.groupby('session_id').last().reset_index()
        latest_sessions = latest_sessions.sort_values('timestamp', ascending=False).head(10)
        
        # Display table
        display_df = latest_sessions[['session_id', 'prediction', 'confidence', 'risk_score', 'timestamp']].copy()
        display_df['confidence'] = display_df['confidence'].round(3)
        display_df['risk_score'] = display_df['risk_score'].round(3)
        
        st.dataframe(display_df, use_container_width=True)

    def show_flagged_devices(self, api_stats):
        """Show flagged devices section"""
        if not api_stats or 'flaggedDevices' not in api_stats:
            st.warning("No flagged device data available")
            return
            
        flagged_devices = api_stats['flaggedDevices']
        
        if not flagged_devices:
            st.info("No devices currently flagged")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(flagged_devices, columns=[
            'Device ID', 'IP Address', 'Reason', 'Bot Count', 
            'First Detected', 'Last Detected', 'Blocked'
        ])
        
        # Style the dataframe
        def highlight_blocked(row):
            return ['background-color: #ffebee' if row['Blocked'] else '' for _ in row]
        
        styled_df = df.style.apply(highlight_blocked, axis=1)
        st.dataframe(styled_df, use_container_width=True)
    
    def show_admin_alerts(self, api_stats):
        """Show recent admin alerts"""
        if not api_stats or 'recentAlerts' not in api_stats:
            st.warning("No alert data available")
            return
            
        recent_alerts = api_stats['recentAlerts']
        
        if not recent_alerts:
            st.info("No recent alerts")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(recent_alerts, columns=[
            'Session ID', 'Alert Type', 'Message', 'Device', 'IP Address', 'Timestamp', 'Severity'
        ])
        
        # Color code by severity
        def highlight_severity(row):
            if row['Severity'] == 'HIGH':
                return ['background-color: #ffcdd2' for _ in row]
            elif row['Severity'] == 'MEDIUM':
                return ['background-color: #fff3e0' for _ in row]
            else:
                return ['' for _ in row]
        
        styled_df = df.style.apply(highlight_severity, axis=1)
        st.dataframe(styled_df, use_container_width=True)

# Initialize dashboard
dashboard = BotDetectionDashboard()

# Main dashboard
st.title("🤖 AI-Based Bot Detection Dashboard")
st.markdown("Real-time monitoring of human vs bot interactions")

# Refresh button
if st.button("🔄 Refresh Data"):
    st.rerun()

# Get data
interactions_df, alerts_df = dashboard.get_data_from_db()
api_stats = dashboard.get_stats_from_api()

# Metrics
st.header("Key Metrics")
dashboard.create_metrics_cards(interactions_df, alerts_df)

# Flagged Devices Alert
if api_stats and api_stats.get('flaggedDevices'):
    flagged_count = len(api_stats['flaggedDevices'])
    if flagged_count > 0:
        st.error(f"ALERT: {flagged_count} device(s) flagged for bot activity!")

# Charts
col1, col2 = st.columns(2)

with col1:
    st.header("Detection Results")
    dashboard.create_prediction_chart(interactions_df)

with col2:
    st.header("Confidence Distribution")
    dashboard.create_confidence_distribution(interactions_df)

# Risk analysis
st.header("Risk Analysis")
dashboard.create_risk_score_chart(interactions_df)

# Timeline
st.header("Detection Timeline")
dashboard.create_timeline_chart(interactions_df)

# Alerts
st.header("Security Alerts")
dashboard.create_alerts_chart(alerts_df)

# Flagged Devices Section
st.header("Flagged Devices")
dashboard.show_flagged_devices(api_stats)

# Admin Alerts Section
st.header("Admin Alerts")
dashboard.show_admin_alerts(api_stats)

# Recent data tables
col1, col2 = st.columns(2)

with col1:
    st.header("Recent Sessions")
    dashboard.show_recent_sessions(interactions_df)

with col2:
    st.header("Recent Database Alerts")
    if not alerts_df.empty:
        recent_alerts = alerts_df.head(10)
        st.dataframe(recent_alerts[['session_id', 'alert_type', 'message', 'timestamp']], use_container_width=True)
    else:
        st.info("No database alerts")

# System status
st.header("🔧 System Status")
api_stats = dashboard.get_stats_from_api()
if api_stats:
    st.success("✅ Backend API is running")
    st.json(api_stats)
else:
    st.error("❌ Backend API is not responding")

# Auto-refresh
st.markdown("---")
st.markdown("Dashboard auto-refreshes every 30 seconds")

# Add some CSS for better styling
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
}
</style>
""", unsafe_allow_html=True)