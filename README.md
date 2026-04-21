# Smart-Dynamic-Load-Balancer-with-Server-Health-Monitoring-and-Interactive-Dashboard
This project implements a custom software load balancer in Python that routes HTTP requests to multiple Flask backend servers, monitors their health and performance, logs metrics to a database, and provides an interactive dashboard for visualization and analysis.


## Setup and Execution Instructions

### 1. Prerequisites

- **Python**: 3.10+ recommended
- **pip** package manager
- (Optional) **virtualenv** for isolated environment

### 2. Clone / Open the Project

Place the project folder on your machine (e.g. `C:\\Users\\mitsa\\OneDrive\\Desktop\\CN_cp`).

### 3. Create and Activate Virtual Environment (Recommended)

Windows (PowerShell):

```bash
cd C:\Users\mitsa\OneDrive\Desktop\CN_cp
python -m venv venv
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Initialize the Database

SQLite DB file will be created automatically on first run. No manual migrations are required for the basic demo schema.

### 6. Start Backend Servers

Run three backend Flask servers on different ports:

```bash
cd C:\Users\mitsa\OneDrive\Desktop\CN_cp
python src\backend_servers\run_servers.py
```

This script will start servers on ports `5001`, `5002`, and `5003`.

### 7. Start the Load Balancer

In a new terminal (with virtualenv activated):

```bash
cd C:\Users\mitsa\OneDrive\Desktop\CN_cp
python src\load_balancer\balancer.py --algorithm round_robin
```

By default the load balancer listens on `http://127.0.0.1:8000`.

You can change algorithm:

```bash
python src\load_balancer\balancer.py --algorithm least_connections
python src\load_balancer\balancer.py --algorithm cpu_based
```

### 8. Start the Dashboard

In another terminal:

```bash
cd C:\Users\mitsa\OneDrive\Desktop\CN_cp
streamlit run src\dashboard\app.py
```

Open the link shown in the terminal (default `http://localhost:8501`).

### 9. Simulate Traffic

Use the built-in traffic generator:

```bash
cd C:\Users\mitsa\OneDrive\Desktop\CN_cp
python src\simulation\traffic_generator.py --concurrency 20 --requests 200 --algorithm round_robin
```

Or see `src\simulation\ab_instructions.txt` for using Apache Benchmark.

### 10. View Logs & Reports

- Logs: `logs/` folder
- SQLite DB file: `db/load_balancer.db`
- Dashboard visualizations: Streamlit UI
- Written report: `docs/report.md`

