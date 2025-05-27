#!/bin/bash

REPO_URL="https://github.com/jonas52/systek.git"
INSTALL_DIR="/opt/systek"
SERVICE_NAME="systek"
ENTRY_POINT="systek.py"
SYMLINK_PATH="/usr/local/bin/systek"

# Clone or update repo
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "╰─╼ Updating existing repo..."
    git -C "$INSTALL_DIR" pull
else
    echo "│ Cloning repo to $INSTALL_DIR..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

# Make sure script is executable
chmod +x "$INSTALL_DIR/$ENTRY_POINT"

# Create systemd service
echo "│ Creating systemd service..."
cat <<EOF | sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null
[Unit]
Description=Systek Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 $INSTALL_DIR/$ENTRY_POINT
WorkingDirectory=$INSTALL_DIR
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

# Create symlink
echo "│ Creating symlink: $SYMLINK_PATH"
sudo ln -sf "$INSTALL_DIR/$ENTRY_POINT" "$SYMLINK_PATH"

echo "╰─╼ Installation complete. Use 'systek --update' or 'systek --remove'."
