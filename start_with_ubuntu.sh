

echo "Starting Docker Compose..."
docker compose up -d

echo "Creating Python virtual environment..."
python3.12 -m venv .venv

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing Python dependencies..."
pip install -r requirements.txt 

echo "Running Assignment1Tester.py..."
python3 Assignment1Tester.py

echo "Script finished."