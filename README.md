# Pachinko Manager (Ocean 4 SP)

This application calculates expectation values based on a time-limit model and manages machine data.

## Prerequisites

- Python 3.8+
- Streamlit, Pandas, Matplotlib

## Installation

1. Install dependencies:
   ```bash
   pip install streamlit pandas matplotlib
   ```

2. Navigate to the project directory:
   ```bash
   cd pachinko_manager
   ```

## Usage

Run the application with Streamlit:

```bash
streamlit run app.py
```

## Features

- **Expectation Calculator**: 
  - Calculates value based on Base and Remaining Spins.
  - Accounts for "Decay" in value as time runs out.
  - Includes "Technical Intervention" bonus (+500 yen).
- **Data Management**:
  - Store Machine Data (Total Spins, Total Out).
  - Calculates Machine Average Output (Weighted Average).
- **Visualization**:
  - Graphs Expectation vs Base.
  - Matrix view of Expectation vs Spins.

## Database

The app uses `pachinko.db` (SQLite). It is automatically created on first run.
