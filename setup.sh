# Setup script for Unix-based systems (Linux/Mac)

echo "===================================="
echo "   Job Scraper Tool - Setup"
echo "===================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3 from https://www.python.org/"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "===================================="
echo "Setup complete!"
echo "===================================="
echo ""
echo "Quick start examples:"
echo ""
echo "  Remote Python jobs:"
echo "    python main.py --keywords 'python developer' --remote"
echo ""
echo "  Data Scientist in New York:"
echo "    python main.py --keywords 'data scientist' --location 'New York'"
echo ""
echo "  High-paying remote jobs:"
echo "    python main.py --keywords 'software engineer' --remote --min-salary 100000"
echo ""
echo "See README.md for more examples!"
