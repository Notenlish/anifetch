#!/bin/bash

FRAME_DIR="$HOME/.local/share/anifetch/output"

# Check for FRAMERATE input
if [[[ $# -ne 5 ] || [ $# -ne 6 ]]]; then
  echo "Usage: <framerate> <top> <left> <right> <bottom>"
  exit 1
fi

framerate=$1
top=$2
left=$3
right=$4
bottom=$5
soundname=$6

num_lines=$((bottom - top))

# Compute 1 / FRAMERATE using bc
sleep_time=$(echo "scale=4; 1 / $framerate" | bc)

# Adjust sleep time based on number of lines
adjusted_sleep_time=$(echo "$sleep_time / $num_lines" | bc -l)

# used to "lock" the while loop when the terminal is resized, that way it wont try to redraw the static template or clear the screen while the loop hasnt finished updating the entire frame(it updates line by line).
lock=false


# Hide cursor
tput civis

# TODO: the cursor should be placed at end when the user does ctrl + c
trap "tput cnorm; if [ -t 0 ]; then stty echo; fi; tput sgr0; tput cup $(tput lines) 0; exit 0" SIGINT


draw_static_template() {
    tput clear
    tput cup $top 0
    cat "$HOME/.local/share/anifetch/template.txt"
}

# Function to run when the terminal is resized
on_resize() {
    if [ "$lock" = false ];then
        lock=true
        draw_static_template
        lock=false
    fi
}

# Trap the SIGWINCH signal (window size change)
trap 'on_resize' SIGWINCH

# Initial size
on_resize

clear

#for (( i=0; i<top; i++ )); do
#  echo
#done

# draw the static template
draw_static_template

###############################

if [ $# -eq 6 ]; then
ffplay -nodisp -autoexit -loop 0 -loglevel quiet $6 &
fi

# Main loop
i=1
wanted_epoch=0
start_time=$(date +%s.%N)
while true; do
  for frame in $(ls "$FRAME_DIR" | sort -n); do
    lock=true
    current_top=$top
    while IFS= read -r line; do
        tput cup "$current_top" "$left"
        echo -ne "$line"
        current_top=$((current_top + 1))
        if [[ $current_top -gt $bottom ]]; then
            break
        fi
    done < "$FRAME_DIR/$frame"
    lock=false
    
    wanted_epoch=$(echo "$i/$framerate" | bc -l)

    # current time in seconds with fractional part
    now=$(date +%s.%N)

    # Calculate how long to sleep to stay in sync
    sleep_duration=$(echo "$wanted_epoch - ($now - $start_time)" | bc -l)

    # Only sleep if ahead of schedule
    if (( $(echo "$sleep_duration > 0" | bc -l) )); then
        sleep "$sleep_duration"
    fi

    i=$((i + 1))
  done
done
