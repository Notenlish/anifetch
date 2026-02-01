#!/bin/bash

. /etc/os-release

echo "Detected OS ID: $ID"
echo "Detected OS ID_LIKE: $ID_LIKE"

install_anifetch() {
    echo "Installing anifetch..."

    if pipx upgrade anifetch &> /dev/null; then
        echo "anifetch upgraded successfully (or was already at the latest version from GitHub)."
    else
        echo "anifetch not found or upgrade failed. Performing initial installation from GitHub..."
        pipx install git+https://github.com/Notenlish/anifetch.git#egg=anifetch
        echo "anifetch installed successfully."
    fi
    echo "anifetch installation/upgrade process completed."
}

if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    echo "You should use choco to install it for windows."

elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Use homebrew to install anifetch for macos."

elif [[ "$ID" == "debian" || "$ID" == "ubuntu" || "$ID" == "linuxmint" || "$ID_LIKE" =~ "debian" || "$ID_LIKE" =~ "ubuntu" ]]; then
    echo "Detected Debian/Ubuntu-based distribution. Using apt."
    sudo apt update
    sudo apt install -y chafa ffmpeg python3-pip git
    sudo apt install -y pipx
    # what is -y
    pipx ensurepath
    install_anifetch

elif [[ "$ID" == "arch" || "$ID" == "manjaro" || "$ID_LIKE" =~ "arch" ]]; then
    echo "Detected Arch-based distribution. Using pacman."
    sudo pacman -Sy --noconfirm chafa ffmpeg python-pip git
    sudo pacman -Sy --noconfirm python-pipx
    # what is -Sy and --noconfirm
    pipx ensurepath
    install_anifetch

elif [[ "$ID" == "fedora" || "$ID" == "rhel" || "$ID" == "centos" || "$ID" == "rocky" || "$ID" == "almalinux" || "$ID_LIKE" =~ "fedora" || "$ID_LIKE" =~ "rhel" ]]; then
    echo "Detected Fedora/RHEL-based distribution. Using dnf."
    sudo dnf install -y chafa ffmpeg python3-pip git
    sudo dnf install -y neofetch
    sudo dnf install -y fastfetch
    sudo dnf install -y pipx
    # what is -y
    pipx ensurepath
    install_anifetch

elif [[ "$ID" == "opensuse" || "$ID_LIKE" =~ "suse" ]]; then
    echo "Detected openSUSE-based distribution. Using zypper."
    sudo zypper --non-interactive install chafa ffmpeg python3-pip git
    sudo zypper --non-interactive install  python3-pipx
    # what is -y
    pipx ensurepath
    install_anifetch

# Generic Linux fallback
else
    echo "Detected other Linux distribution ($ID). Attempting to install common packages."
    echo "Please ensure you have a package manager like apt, pacman, or dnf installed."
    echo "Trying to install chafa, ffmpeg, and pipx. This might require manual intervention."

    # Attempt to install common tools, assuming one of the package managers might be present
    if command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y chafa ffmpeg python3-pip git
        sudo apt install -y pipx
    elif command -v pacman &> /dev/null; then
        sudo pacman -Sy --noconfirm chafa ffmpeg git python-pip
        sudo pacman -Sy --noconfirm python-pipx
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y chafa ffmpeg python3-pip git
        sudo dnf install -y neofetch
        sudo dnf install -y fastfetch
        sudo dnf install -y pipx
    elif command -v zypper &> /dev/null; then
        sudo zypper --non-interactive install chafa ffmpeg python3-pip git
        sudo zypper --non-interactive install python3-pipx
    else
        echo "No common package manager found. Please install chafa, ffmpeg, git, and pipx manually."
        echo "You might need to install Python 3 and pip first."
    fi

    pipx ensurepath
    install_anifetch
fi

echo "Installation script finished."
