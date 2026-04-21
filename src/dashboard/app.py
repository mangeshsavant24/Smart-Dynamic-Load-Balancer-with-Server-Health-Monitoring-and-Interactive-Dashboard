import time
from pathlib import Path
import sys
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine

# Ensure project root is on sys.path so that `src.*` imports work
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.monitoring.db import DATABASE_URL, init_db


# Make sure tables exist before querying
init_db()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def load_data():
    req_df = pd.read_sql("SELECT * FROM request_logs ORDER BY timestamp DESC LIMIT 1000", engine)
    health_df = pd.read_sql("SELECT * FROM health_logs ORDER BY timestamp DESC LIMIT 1000", engine)
    return req_df, health_df


def generate_health_report(req_df, health_df):
    """Generate a detailed server health report in layman's terms."""
    
    report = []
    report.append("=" * 80)
    report.append("SMART LOAD BALANCER - DETAILED SERVER HEALTH REPORT")
    report.append("=" * 80)
    report.append("")
    report.append(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Executive Summary
    report.append("EXECUTIVE SUMMARY")
    report.append("-" * 80)
    report.append("In simple terms: This report shows how well your servers are performing and")
    report.append("how traffic is being distributed among them.")
    report.append("")
    
    if not req_df.empty:
        total_requests = len(req_df)
        report.append(f"Total Requests Processed: {total_requests}")
        report.append(f"  → Think of it as: {total_requests} customer requests were handled by your servers.")
        report.append("")
    
    # Request Distribution
    report.append("REQUEST DISTRIBUTION - WHO HANDLED WHAT?")
    report.append("-" * 80)
    report.append("This shows how fairly traffic was split among your servers.")
    report.append("")
    
    if not req_df.empty:
        backend_counts = req_df['backend_name'].value_counts()
        total = len(req_df)
        for backend, count in backend_counts.items():
            percentage = (count / total) * 100
            report.append(f"{backend}:")
            report.append(f"  → Handled {count} requests ({percentage:.1f}% of total traffic)")
            report.append(f"  → This is {'✓ Fair distribution' if 25 < percentage < 40 else '⚠ Check load balancing'}")
            report.append("")
    
    # Response Time Analysis
    report.append("RESPONSE TIME - HOW FAST WERE THE RESPONSES?")
    report.append("-" * 80)
    report.append("Response time = How quickly servers answered requests (in milliseconds).")
    report.append("Lower is better (faster = happier customers).")
    report.append("")
    
    if not req_df.empty:
        avg_response = req_df['response_time_ms'].mean()
        min_response = req_df['response_time_ms'].min()
        max_response = req_df['response_time_ms'].max()
        
        report.append(f"Average Response Time: {avg_response:.2f} ms")
        if avg_response < 100:
            report.append("  → EXCELLENT! ✓ This is very fast.")
        elif avg_response < 500:
            report.append("  → GOOD. This is acceptable for most uses.")
        else:
            report.append("  → WARNING ⚠ This might be slow for users.")
        report.append("")
        
        report.append(f"Fastest Response: {min_response:.2f} ms (best case)")
        report.append(f"Slowest Response: {max_response:.2f} ms (worst case)")
        report.append("")
    
    # Per-Backend Response Times
    report.append("RESPONSE TIME BY SERVER:")
    report.append("")
    if not req_df.empty:
        backend_response = req_df.groupby('backend_name')['response_time_ms'].agg(['mean', 'min', 'max', 'count'])
        for backend, row in backend_response.iterrows():
            report.append(f"{backend}:")
            report.append(f"  → Average: {row['mean']:.2f} ms")
            report.append(f"  → Fastest: {row['min']:.2f} ms | Slowest: {row['max']:.2f} ms")
            report.append(f"  → Processed {int(row['count'])} requests")
            report.append("")
    
    # Server Health Metrics
    report.append("SERVER HEALTH METRICS - IS YOUR SERVER BREATHING OK?")
    report.append("-" * 80)
    report.append("CPU = How hard the server is working (0% = idle, 100% = fully loaded)")
    report.append("Memory = How much of the server's brain is being used")
    report.append("")
    
    if not health_df.empty:
        avg_cpu = health_df['cpu_percent'].mean()
        avg_memory = health_df['memory_rss_mb'].mean()
        max_cpu = health_df['cpu_percent'].max()
        max_memory = health_df['memory_rss_mb'].max()
        
        report.append(f"Average CPU Usage: {avg_cpu:.2f}%")
        if avg_cpu < 30:
            report.append("  → HEALTHY ✓ Your servers have plenty of room to handle more traffic.")
        elif avg_cpu < 70:
            report.append("  → NORMAL. Servers are working well but getting busier.")
        else:
            report.append("  → WARNING ⚠ Servers are overworked! Consider upgrading.")
        report.append("")
        
        report.append(f"Peak CPU Usage: {max_cpu:.2f}%")
        report.append("")
        
        report.append(f"Average Memory: {avg_memory:.2f} MB (~{avg_memory/1024:.2f} GB)")
        report.append(f"Peak Memory: {max_memory:.2f} MB (~{max_memory/1024:.2f} GB)")
        report.append("  → Memory usage is normal if under a few GB per server.")
        report.append("")
        
        # Per-Backend Health
        report.append("HEALTH PER SERVER:")
        report.append("")
        backend_health = health_df.groupby('backend_name').agg({
            'cpu_percent': ['mean', 'max'],
            'memory_rss_mb': ['mean', 'max']
        }).round(2)
        
        for backend in health_df['backend_name'].unique():
            backend_data = health_df[health_df['backend_name'] == backend]
            avg_cpu = backend_data['cpu_percent'].mean()
            max_cpu = backend_data['cpu_percent'].max()
            avg_mem = backend_data['memory_rss_mb'].mean()
            max_mem = backend_data['memory_rss_mb'].max()
            
            report.append(f"{backend}:")
            report.append(f"  → CPU: Average {avg_cpu:.2f}% | Peak {max_cpu:.2f}%")
            report.append(f"  → Memory: Average {avg_mem:.2f} MB | Peak {max_mem:.2f} MB")
            
            # Health status
            if avg_cpu < 50 and avg_mem < 500:
                status = "✓ HEALTHY"
            elif avg_cpu < 70 and avg_mem < 1000:
                status = "⚠ NORMAL (a bit busy)"
            else:
                status = "❌ STRESSED"
            report.append(f"  → Status: {status}")
            report.append("")
    
    # Recommendations
    report.append("RECOMMENDATIONS & WHAT TO DO")
    report.append("-" * 80)
    
    recommendations = []
    
    if not req_df.empty:
        # Check load balance fairness
        backend_counts = req_df['backend_name'].value_counts()
        percentages = (backend_counts / len(req_df)) * 100
        if percentages.std() > 5:
            recommendations.append("⚠ Load distribution is uneven. Check your load balancer algorithm.")
    
    if not health_df.empty:
        avg_cpu = health_df['cpu_percent'].mean()
        if avg_cpu > 70:
            recommendations.append("⚠ CPU usage is high. Consider: a) More servers, b) Optimizing code, c) Upgrading hardware")
    
    if not req_df.empty:
        avg_response = req_df['response_time_ms'].mean()
        if avg_response > 500:
            recommendations.append("⚠ Response times are slow. Check for: database queries, network issues, or code bottlenecks")
    
    if recommendations:
        for rec in recommendations:
            report.append(rec)
    else:
        report.append("✓ Everything looks good! Your system is performing well.\n")
    
    report.append("")
    report.append("=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)
    
    return "\n".join(report)


def generate_html_report_with_charts(req_df, health_df):
    """Generate an HTML report with embedded visualizations and charts."""
    
    html_parts = []
    
    # HTML Header
    html_parts.append("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Load Balancer Health Report</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 8px;
                margin-bottom: 30px;
            }
            .section {
                background: white;
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .section h2 {
                color: #667eea;
                border-bottom: 3px solid #667eea;
                padding-bottom: 10px;
            }
            .chart-container {
                width: 100%;
                height: 500px;
                margin: 20px 0;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }
            .stat-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }
            .stat-card .value {
                font-size: 32px;
                font-weight: bold;
                margin: 10px 0;
            }
            .stat-card .label {
                font-size: 14px;
                opacity: 0.9;
            }
            .recommendation {
                padding: 10px;
                margin: 10px 0;
                border-left: 4px solid #ff9800;
                background-color: #fff8f3;
            }
            .recommendation.good {
                border-left-color: #4caf50;
                background-color: #f1f8f4;
            }
            .recommendation.warning {
                border-left-color: #ff9800;
                background-color: #fff8f3;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #667eea;
                color: white;
            }
            tr:hover {
                background-color: #f5f5f5;
            }
            .footer {
                text-align: center;
                color: #666;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
            }
        </style>
    </head>
    <body>
    """)
    
    # Header
    html_parts.append(f"""
    <div class="header">
        <h1>🚀 Smart Load Balancer - Health Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    """)
    
    # Executive Summary
    html_parts.append("""
    <div class="section">
        <h2>📊 Executive Summary</h2>
        <p>This report shows how well your servers are performing and how traffic is being distributed among them.</p>
    """)
    
    if not req_df.empty:
        total_requests = len(req_df)
        avg_response = req_df['response_time_ms'].mean()
        
        html_parts.append(f"""
        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">Total Requests</div>
                <div class="value">{total_requests}</div>
            </div>
            <div class="stat-card">
                <div class="label">Avg Response Time</div>
                <div class="value">{avg_response:.2f} ms</div>
            </div>
        """)
        
        if not health_df.empty:
            avg_cpu = health_df['cpu_percent'].mean()
            html_parts.append(f"""
            <div class="stat-card">
                <div class="label">Avg CPU Usage</div>
                <div class="value">{avg_cpu:.1f}%</div>
            </div>
            """)
        
        html_parts.append("</div>")
    html_parts.append("</div>")
    
    # Request Distribution Chart
    if not req_df.empty:
        html_parts.append('<div class="section">')
        html_parts.append('<h2>📈 Request Distribution by Backend</h2>')
        
        fig1 = px.bar(
            req_df.groupby(["backend_name", "algorithm"])["id"]
            .count()
            .reset_index()
            .rename(columns={"id": "request_count"}),
            x="backend_name",
            y="request_count",
            color="algorithm",
            title="Requests per Backend (by Algorithm)",
        )
        html_parts.append(f'<div class="chart-container">{fig1.to_html(include_plotlyjs=False, div_id="fig1")}</div>')
        html_parts.append('</div>')
    
    # Response Time Analysis
    if not req_df.empty:
        html_parts.append('<div class="section">')
        html_parts.append('<h2>⏱️ Response Time Analysis</h2>')
        
        avg_response = req_df['response_time_ms'].mean()
        min_response = req_df['response_time_ms'].min()
        max_response = req_df['response_time_ms'].max()
        
        if avg_response < 100:
            status = "✓ EXCELLENT! Very fast."
        elif avg_response < 500:
            status = "✓ GOOD. Acceptable for most uses."
        else:
            status = "⚠ WARNING. This might be slow."
        
        html_parts.append(f"""
        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">Average Response</div>
                <div class="value">{avg_response:.2f} ms</div>
                <div class="label">{status}</div>
            </div>
            <div class="stat-card">
                <div class="label">Fastest Response</div>
                <div class="value">{min_response:.2f} ms</div>
            </div>
            <div class="stat-card">
                <div class="label">Slowest Response</div>
                <div class="value">{max_response:.2f} ms</div>
            </div>
        </div>
        """)
        
        # Response time distribution
        fig2 = px.box(
            req_df,
            x="algorithm",
            y="response_time_ms",
            color="backend_name",
            title="Response Time Distribution by Backend",
        )
        html_parts.append(f'<div class="chart-container">{fig2.to_html(include_plotlyjs=False, div_id="fig2")}</div>')
        
        # Response time over time
        fig3 = px.line(
            req_df.sort_values("timestamp"),
            x="timestamp",
            y="response_time_ms",
            color="algorithm",
            title="Response Time Over Time",
        )
        html_parts.append(f'<div class="chart-container">{fig3.to_html(include_plotlyjs=False, div_id="fig3")}</div>')
        html_parts.append('</div>')
    
    # Per-Backend Statistics Table
    if not req_df.empty:
        html_parts.append('<div class="section">')
        html_parts.append('<h2>📋 Per-Server Response Time Statistics</h2>')
        html_parts.append('<table>')
        html_parts.append('<tr><th>Server</th><th>Requests</th><th>Avg Response (ms)</th><th>Min (ms)</th><th>Max (ms)</th></tr>')
        
        backend_response = req_df.groupby('backend_name')['response_time_ms'].agg(['count', 'mean', 'min', 'max'])
        for backend, row in backend_response.iterrows():
            html_parts.append(f"""
            <tr>
                <td>{backend}</td>
                <td>{int(row['count'])}</td>
                <td>{row['mean']:.2f}</td>
                <td>{row['min']:.2f}</td>
                <td>{row['max']:.2f}</td>
            </tr>
            """)
        html_parts.append('</table>')
        html_parts.append('</div>')
    
    # Server Health Section
    if not health_df.empty:
        html_parts.append('<div class="section">')
        html_parts.append('<h2>💪 Server Health Metrics</h2>')
        
        avg_cpu = health_df['cpu_percent'].mean()
        avg_memory = health_df['memory_rss_mb'].mean()
        max_cpu = health_df['cpu_percent'].max()
        max_memory = health_df['memory_rss_mb'].max()
        
        if avg_cpu < 30:
            cpu_status = "✓ HEALTHY - Plenty of capacity"
        elif avg_cpu < 70:
            cpu_status = "✓ NORMAL - Working well"
        else:
            cpu_status = "⚠ WARNING - Servers overworked"
        
        html_parts.append(f"""
        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">Average CPU Usage</div>
                <div class="value">{avg_cpu:.1f}%</div>
                <div class="label">{cpu_status}</div>
            </div>
            <div class="stat-card">
                <div class="label">Peak CPU Usage</div>
                <div class="value">{max_cpu:.1f}%</div>
            </div>
            <div class="stat-card">
                <div class="label">Average Memory</div>
                <div class="value">{avg_memory:.0f} MB</div>
            </div>
            <div class="stat-card">
                <div class="label">Peak Memory</div>
                <div class="value">{max_memory:.0f} MB</div>
            </div>
        </div>
        """)
        
        # CPU chart
        fig4 = px.line(
            health_df.sort_values("timestamp"),
            x="timestamp",
            y="cpu_percent",
            color="backend_name",
            title="CPU Usage Over Time (%)",
        )
        html_parts.append(f'<div class="chart-container">{fig4.to_html(include_plotlyjs=False, div_id="fig4")}</div>')
        
        # Memory chart
        fig5 = px.line(
            health_df.sort_values("timestamp"),
            x="timestamp",
            y="memory_rss_mb",
            color="backend_name",
            title="Memory Usage Over Time (MB)",
        )
        html_parts.append(f'<div class="chart-container">{fig5.to_html(include_plotlyjs=False, div_id="fig5")}</div>')
        
        # Health table
        html_parts.append('<h3>Per-Server Health Status</h3>')
        html_parts.append('<table>')
        html_parts.append('<tr><th>Server</th><th>Avg CPU</th><th>Max CPU</th><th>Avg Memory</th><th>Max Memory</th><th>Status</th></tr>')
        
        for backend in health_df['backend_name'].unique():
            backend_data = health_df[health_df['backend_name'] == backend]
            avg_cpu_s = backend_data['cpu_percent'].mean()
            max_cpu_s = backend_data['cpu_percent'].max()
            avg_mem_s = backend_data['memory_rss_mb'].mean()
            max_mem_s = backend_data['memory_rss_mb'].max()
            
            if avg_cpu_s < 50 and avg_mem_s < 500:
                status = "✓ Healthy"
            elif avg_cpu_s < 70 and avg_mem_s < 1000:
                status = "⚠ Normal"
            else:
                status = "❌ Stressed"
            
            html_parts.append(f"""
            <tr>
                <td>{backend}</td>
                <td>{avg_cpu_s:.1f}%</td>
                <td>{max_cpu_s:.1f}%</td>
                <td>{avg_mem_s:.0f} MB</td>
                <td>{max_mem_s:.0f} MB</td>
                <td>{status}</td>
            </tr>
            """)
        html_parts.append('</table>')
        html_parts.append('</div>')
    
    # Recommendations
    html_parts.append('<div class="section">')
    html_parts.append('<h2>🎯 Recommendations</h2>')
    
    recommendations = []
    
    if not req_df.empty:
        backend_counts = req_df['backend_name'].value_counts()
        percentages = (backend_counts / len(req_df)) * 100
        if percentages.std() > 5:
            recommendations.append(("warning", "⚠ Load distribution is uneven. Check your load balancer algorithm."))
    
    if not health_df.empty:
        avg_cpu = health_df['cpu_percent'].mean()
        if avg_cpu > 70:
            recommendations.append(("warning", "⚠ High CPU usage. Consider: More servers, code optimization, or hardware upgrade."))
    
    if not req_df.empty:
        avg_response = req_df['response_time_ms'].mean()
        if avg_response > 500:
            recommendations.append(("warning", "⚠ Slow response times. Check database queries, network, or code bottlenecks."))
    
    if not recommendations:
        recommendations.append(("good", "✓ Everything looks good! Your system is performing well."))
    
    for rec_type, rec_text in recommendations:
        html_parts.append(f'<div class="recommendation {rec_type}">{rec_text}</div>')
    
    html_parts.append('</div>')
    
    # Footer
    html_parts.append("""
    <div class="footer">
        <p>Smart Load Balancer Health Report</p>
        <p><small>For more details, visit the dashboard or contact your system administrator.</small></p>
    </div>
    
    </body>
    </html>
    """)
    
    return "\n".join(html_parts)


def main():
    st.set_page_config(page_title="Smart Load Balancer Dashboard", layout="wide")
    st.title("Smart Dynamic Load Balancer Dashboard")

    refresh_interval = st.sidebar.slider("Auto-refresh interval (seconds)", 2, 30, 5)

    st.subheader("Request Metrics")
    try:
        req_df, health_df = load_data()
    except Exception as e:  # noqa: BLE001
        st.warning(f"Waiting for data... ({e})")
        st.stop()

    # Add Download Report Button
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Reports")
    
    report_content = generate_health_report(req_df, health_df)
    html_report = generate_html_report_with_charts(req_df, health_df)
    
    col1, col2, col3 = st.sidebar.columns(3)
    with col1:
        st.download_button(
            label="📥 Report (TXT)",
            data=report_content,
            file_name=f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
    
    with col2:
        st.download_button(
            label="📥 Report (HTML)",
            data=html_report,
            file_name=f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            mime="text/html"
        )
    
    with col3:
        # CSV export of raw data
        if not req_df.empty:
            csv_data = req_df.to_csv(index=False)
            st.download_button(
                label="📥 Data (CSV)",
                data=csv_data,
                file_name=f"request_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    st.sidebar.markdown("---")

    if not req_df.empty:
        col1, col2 = st.columns(2)

        with col1:
            fig1 = px.bar(
                req_df.groupby(["backend_name", "algorithm"])["id"]
                .count()
                .reset_index()
                .rename(columns={"id": "request_count"}),
                x="backend_name",
                y="request_count",
                color="algorithm",
                title="Requests per Backend (by Algorithm)",
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            fig2 = px.box(
                req_df,
                x="algorithm",
                y="response_time_ms",
                color="backend_name",
                title="Response Time Distribution (ms)",
            )
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Time Series")
        fig3 = px.line(
            req_df.sort_values("timestamp"),
            x="timestamp",
            y="response_time_ms",
            color="algorithm",
            title="Response Time Over Time",
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No request data yet. Generate traffic to see metrics.")

    st.subheader("Server Health (CPU & Memory)")
    if not health_df.empty:
        fig4 = px.line(
            health_df.sort_values("timestamp"),
            x="timestamp",
            y="cpu_percent",
            color="backend_name",
            title="CPU Usage Over Time",
        )
        st.plotly_chart(fig4, use_container_width=True)

        fig5 = px.line(
            health_df.sort_values("timestamp"),
            x="timestamp",
            y="memory_rss_mb",
            color="backend_name",
            title="Memory Usage Over Time (MB)",
        )
        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.info("No health data yet. The load balancer will record its own metrics automatically.")

    # Detailed Report Section
    st.markdown("---")
    if st.checkbox("📋 Show Detailed Health Report (Layman's Terms)"):
        st.subheader("Detailed Server Health Report")
        st.text(report_content)

    st.markdown(f"*Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    st.rerun()


if __name__ == "__main__":
    main()

