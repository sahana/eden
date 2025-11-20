#!/bin/bash

# Exit on error
set -e

echo "Starting Sahana Eden installation..."

# Check if we are in the eden directory
if [ ! -f "controllers/default.py" ]; then
    echo "Error: Please run this script from the root of the Eden repository."
    exit 1
fi

EDEN_DIR=$(pwd)
WEB2PY_DIR="../web2py"

# Clone Web2py if it doesn't exist
if [ ! -d "$WEB2PY_DIR" ]; then
    echo "Cloning Web2py..."
    git clone --recursive https://github.com/web2py/web2py.git "$WEB2PY_DIR"
else
    echo "Web2py directory already exists."
fi

# Link Eden to Web2py applications
if [ ! -d "$WEB2PY_DIR/applications/eden" ]; then
    echo "Linking Eden to Web2py applications..."
    ln -s "$EDEN_DIR" "$WEB2PY_DIR/applications/eden"
else
    echo "Eden is already linked in Web2py applications."
fi

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt
pip install -r optional_requirements.txt

# Configure Eden
if [ ! -f "models/000_config.py" ]; then
    echo "Configuring Eden..."
    cp modules/templates/000_config.py models/000_config.py
    # Update configuration to mark as edited
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' 's/FINISHED_EDITING_CONFIG_FILE = False/FINISHED_EDITING_CONFIG_FILE = True/' models/000_config.py
    else
        sed -i 's/FINISHED_EDITING_CONFIG_FILE = False/FINISHED_EDITING_CONFIG_FILE = True/' models/000_config.py
    fi
else
    echo "Configuration file already exists."
fi

# Create VERSION file in Web2py if missing
if [ ! -f "$WEB2PY_DIR/VERSION" ]; then
    echo "Creating VERSION file in Web2py..."
    echo "Version 2.21.2-stable+timestamp.2021.10.15.07.44.23" > "$WEB2PY_DIR/VERSION"
fi

echo "Installation complete!"
echo "To start the server, run:"
echo "cd $WEB2PY_DIR"
echo "python web2py.py -a password -i 0.0.0.0 -p 8000"
