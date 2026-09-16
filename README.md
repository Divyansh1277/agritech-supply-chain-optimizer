# AgriTech — "Mandi-to-Market Supply Chain Optimizer"

**TransOrg AgentIQ Datathon — Track 3: AgriTech**

## Project Overview
This project provides a complete, production-quality solution for monitoring and analyzing agricultural supply chains from Mandis to Warehouses. It ingests messy synthetic data, standardizes it, stores it in an SQLite database, and exposes insights through a dynamic Streamlit dashboard and a Graph-first AI agent.

## Business Problem
The State Agriculture Board requires a unified analytics system to:
- Monitor daily crop arrivals.
- Track wholesale prices against Minimum Support Price (MSP) and identify price crashes.
- Analyze weather conditions affecting crop arrivals.
- Monitor transportation logistics and detect delays.
- Allow natural language queries via an AgentIQ Graph Assistant.

## Architecture
1. **Raw Data**: Messy JSON, CSV, and Excel logs.
2. **ETL Pipeline**: Python (`pandas`) based ingestion, cleaning, and standardization. Outputs clean datasets and exception logs.
3. **Database**: SQLite (`agritech.db`) with normalized schema and analytical SQL views.
4. **Dashboard**: Interactive `Streamlit` application.
5. **AI Agent**: Graph-first orchestration detecting intent, generating read-only SQL, selecting optimal Plotly charts, and producing text summaries.

## Installation & Configuration
1. Clone this repository.
2. Ensure you have Python 3.10+ installed.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment:
   ```bash
   cp .env.example .env
   # Add your GEMINI_API_KEY to .env
   ```

## Running the Pipeline
To clean the raw data and generate processed files:
```bash
python src/cleaning/pipeline.py
```
To load the processed data into SQLite and create analytical views:
```bash
python src/database/load_data.py
```

## Running the Dashboard
```bash
streamlit run app.py
```

## Agent Queries
The AgentIQ Graph Assistant handles queries like:
> "Plot the daily arrival trend of Wheat in Amritsar mandi vs MSP for the last 30 days."

## Future Scope
- Predictive forecasting for arrivals and prices.
- Real-time Kafka integration for IoT sensor logs.
- Direct connection to cloud data warehouses (e.g., Snowflake, BigQuery).

## Team
*Your Team Name Here*
