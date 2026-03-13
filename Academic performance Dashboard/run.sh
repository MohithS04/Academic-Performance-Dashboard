#!/bin/bash

echo "Installing requirements..."
pip install -r requirements.txt

echo "Starting data simulator in the background..."
python data_simulator.py &
SIMULATOR_PID=$!

echo "Starting Streamlit dashboard..."
python -m streamlit run app.py

# When Streamlit exits, kill the simulator too
kill $SIMULATOR_PID
