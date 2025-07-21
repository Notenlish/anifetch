#!/bin/bash

. /etc/os-release

echo "Detected OS ID: $ID"
echo "Detected OS ID_LIKE: $ID_LIKE"

install_pipx_anifetch() {
    echo "Installing pipx and anifetch..."
    if ! command -v pipx &> /dev/null; then
        echo "pipx not found, installing..."
        python3 -m pip install --user pipx
        pipx ensurepath
    fi

    if pipx upgrade anifetch &> /dev/null; then
        echo "anifetch upgraded successfully (or was already at the latest version from GitHub)."
    else
        echo "anifetch not found or upgrade failed. Performing initial installation from GitHub..."
        pipx install git+https://github.com/Notenlish/anifetch.git
        echo "anifetch installed successfully."
    fi
    echo "anifetch installation/upgrade process completed."
}

if [[ "$ID" == "debian" || "$ID" == "ubuntu" || "$ID" == "linuxmint" || "$ID_LIKE" =~ "debian" || "$ID_LIKE" =~ "ubuntu" ]]; then
    echo "Detected Debian/Ubuntu-based distribution. Using apt."
    sudo apt update
    sudo apt install -y bc chafa ffmpeg python3-pip
    install_pipx_anifetch

elif [[ "$ID" == "arch" || "$ID" == "manjaro" || "$ID_LIKE" =~ "arch" ]]; then
    echo "Detected Arch-based distribution. Using pacman."
    sudo pacman -Sy --noconfirm bc chafa ffmpeg python-pip
    install_pipx_anifetch

elif [[ "$ID" == "fedora" || "$ID" == "rhel" || "$ID" == "centos" || "$ID" == "rocky" || "$ID" == "almalinux" || "$ID_LIKE" =~ "fedora" || "$ID_LIKE" =~ "rhel" ]]; then
    echo "Detected Fedora/RHEL-based distribution. Using dnf."
    sudo dnf install -y bc chafa ffmpeg python3-pip
    install_pipx_anifetch

elif [[ "$ID" == "opensuse" || "$ID_LIKE" =~ "suse" ]]; then
    echo "Detected openSUSE-based distribution. Using zypper."
    sudo zypper install -y bc chafa ffmpeg python3-pip
    install_pipx_anifetch

# Generic Linux fallback
else
    echo "Detected other Linux distribution ($ID). Attempting to install common packages."
    echo "Please ensure you have a package manager like apt, pacman, or dnf installed."
    echo "Trying to install bc, chafa, ffmpeg, and pipx. This might require manual intervention."

    # Attempt to install common tools, assuming one of the package managers might be present
    if command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y bc chafa ffmpeg python3-pip
    elif command -v pacman &> /dev/null; then
        sudo pacman -Sy --noconfirm bc chafa ffmpeg python-pip
    elif command -v dnf &> /dev/dev/null; then
        sudo dnf install -y bc chafa ffmpeg python3-pip
    elif command -v zypper &> /dev/null; then
        sudo zypper install -y bc chafa ffmpeg python3-pip
    else
        echo "No common package manager found. Please install bc, chafa, ffmpeg, and pipx manually."
        echo "You might need to install Python 3 and pip first."
    fi
    install_pipx_anifetch
fi

echo "Installation script finished."
