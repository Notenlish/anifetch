#!/bin/bash


# Check for FRAMERATE input
if [[ $# -ne 6 && $# -ne 7 ]]; then
  echo "Usage: <cache_path> <framerate> <top> <left> <right> <bottom>"
  exit 1
fi

cache_path=$1
framerate=$2
top=$3
left=$4
right=$5
bottom=$6
soundname=$7

num_lines=$((bottom - top))

# Hide cursor
tput civis

# TODO: the cursor should be placed at end when the user does ctrl + c
trap "tput cnorm; if [ -t 0 ]; then stty echo; fi; tput sgr0; tput cup $(tput lines) 0; exit 0" SIGINT
stty -echo  # won't allow ^C to be printed when SIGINT signal comes.

clear

for (( i=0; i<top; i++ )); do
  echo
done

# draw the static template
cat "$HOME/.local/share/anifetch/template.txt"

###############################

if [[ $# -eq 7 ]]; then
    ffplay -nodisp -autoexit -loop 0 -loglevel quiet $soundname &
fi

# Main loop
i=1
wanted_epoch=0
start_time=$(date +%s.%N)
while true; do
  for frame in $(ls "$cache_path" | sort -n); do
    current_top=$top
    while IFS= read -r line; do
        tput cup "$current_top" "$left"
        echo -ne "$line"
        current_top=$((current_top + 1))
        if [[ $current_top -gt $bottom ]]; then
            break
        fi
    done < "$cache_path/$frame"
    
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
