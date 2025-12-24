#!/usr/bin/env bash
set -e

echo "Welcome to Kaoruko Setup"
echo "Checking dependencies..."

cd ..

if [ -f /.flatpak-info ]; then
    echo "Please run this outside a Flatpak environment"
    exit 1
fi

for cmd in curl git sed; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Missing dependency: $cmd"
        exit 1
    fi
done

if ! command -v pyenv >/dev/null 2>&1; then
    echo "Installing pyenv..."
    curl https://pyenv.run | bash

    echo "Configuring shell for pyenv..."

    SHELL_RC=""
    if [[ "$SHELL" == *bash ]]; then
        SHELL_RC="$HOME/.bashrc"
    elif [[ "$SHELL" == *zsh ]]; then
        SHELL_RC="$HOME/.zshrc"
    fi

    if [ -n "$SHELL_RC" ]; then
        {
            echo ''
            echo '# pyenv'
            echo 'export PYENV_ROOT="$HOME/.pyenv"'
            echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"'
            echo 'eval "$(pyenv init -)"'
        } >> "$SHELL_RC"
    fi

    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
else
    echo "pyenv already installed"
fi

PYTHON_VERSION="3.12.5"

if ! pyenv versions --bare | grep -q "^$PYTHON_VERSION$"; then
    echo "Installing Python $PYTHON_VERSION..."
    pyenv install "$PYTHON_VERSION"
fi

pyenv local "$PYTHON_VERSION"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

source .venv/bin/activate

if [ -f requirements.txt ]; then
    echo "Installing Python dependencies..."
    python -m pip install -r requirements.txt
else
    echo "requirements.txt not found."
fi

if [ ! -f config.yaml ]; then
    if [ -f config.yaml.example ]; then
        cp config.yaml.example config.yaml
        echo "Created config.yaml from example"
    else
        echo "config.yaml.example not found"
    fi
fi

read -rp "Enter Discord Bot Token (or 's' to skip): " BOT_TOKEN
if [[ "$BOT_TOKEN" != "s" && -n "$BOT_TOKEN" ]]; then
    sed -i "s/^token:.*/token: \"$BOT_TOKEN\"/" config.yaml
fi

read -rp "Enter command prefix (default: ?ka): " PREFIX
PREFIX=${PREFIX:-?ka}
sed -i "s|^  prefix:.*|  prefix: \"$PREFIX\"|" config.yaml

read -rp "Enter Discord owner ID (or 's' to skip): " OWNER_ID
if [[ "$OWNER_ID" != "s" && -n "$OWNER_ID" ]]; then
    sed -i "s|^  owner_id:.*|  owner_id: $OWNER_ID|" config.yaml
fi

read -rp "Enable GUILDS intent? (Y/n): " I_GUILDS
read -rp "Enable MESSAGES intent? (Y/n): " I_MESSAGES
read -rp "Enable MESSAGE_CONTENT intent? (Y/n): " I_CONTENT

[[ ! "$I_GUILDS" =~ ^[Nn]$ ]] && GUILDS=true || GUILDS=false
[[ ! "$I_MESSAGES" =~ ^[Nn]$ ]] && MESSAGES=true || MESSAGES=false
[[ ! "$I_CONTENT" =~ ^[Nn]$ ]] && CONTENT=true || CONTENT=false

sed -i "s|^    guilds:.*|    guilds: $GUILDS|" config.yaml
sed -i "s|^    messages:.*|    messages: $MESSAGES|" config.yaml
sed -i "s|^    message_content:.*|    message_content: $CONTENT|" config.yaml

read -rp "Run bot as mobile? (Y/n): " MOBILE
[[ ! "$MOBILE" =~ ^[Nn]$ ]] && MOBILE=true || MOBILE=false

sed -i "s|^  is_mobile:.*|  is_mobile: $MOBILE|" config.yaml

echo ""
echo "✅ Kaoruko setup complete!"
echo "To start:"
echo "  source .venv/bin/activate"
echo "  python main.py"
