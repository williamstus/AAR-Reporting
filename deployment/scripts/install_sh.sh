#!/bin/bash
# File: deployment/scripts/install.sh
# Installation script for Linux/macOS systems

set -e

echo "🎖️ Enhanced Individual Soldier Report System - Installation"
echo "============================================================"

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8+ required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs reports config

# Copy default configuration if it doesn't exist
if [ ! -f "config/default_settings.json" ]; then
    echo "⚙️ Creating default configuration..."
    cat > config/default_settings.json << 'EOF'
{
  "column_mapping": {
    "callsign": "Callsign",
    "squad": "Platoon",
    "casualtystate": "Casualty_State",
    "processedtimegmt": "Time_Step",
    "heartrate": "Heart_Rate",
    "stepcount": "Step_Count",
    "temp": "Temperature",
    "battery": "Battery",
    "rssi": "RSSI"
  },
  "performance": {
    "activity_weight": 0.3,
    "casualty_penalties": {
      "WOUNDED": 10,
      "KIA": 20
    },
    "battery_thresholds": {
      "critical": 10,
      "low": 20
    }
  },
  "reporting": {
    "output_directory": "reports/enhanced",
    "max_concurrent_reports": 4
  },
  "log_level": "INFO",
  "max_workers": 4
}
EOF
fi

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v --cov=src --cov-report=term-missing

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "🚀 To start the application:"
echo "   source venv/bin/activate"
echo "   python src/main.py"
echo ""
echo "📊 To run tests:"
echo "   python -m pytest tests/ -v"
echo ""
echo "📁 Reports will be saved to: reports/enhanced/"