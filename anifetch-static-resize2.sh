#!/bin/bash

FRAME_DIR="$HOME/.local/share/anifetch/output"
STATIC_TEMPLATE_FILE="$HOME/.local/share/anifetch/template.txt"

# Check for correct arguments
if [[ $# -ne 6 && $# -ne 7 ]]; then
  echo "Usage: $0 <framerate> <top> <left> <right> <bottom> <template_actual_width> [soundname]"
  exit 1
fi

framerate=$1
top=$2
left=$3
right=$4
bottom=$5
template_actual_width=$6
soundname=$7

num_lines=$((bottom - top))
sleep_time=$(echo "scale=4; 1 / $framerate" | bc)
adjusted_sleep_time=$(echo "$sleep_time / $num_lines" | bc -l)

# Buffer for storing processed template - we'll only compute this when needed
declare -a template_buffer
# Track the terminal width when we last processed the template
last_term_width=0

# Hide cursor
tput civis

# Clean exit handler
cleanup() {
  tput cnorm         # Show cursor
  if [ -t 0 ]; then
    stty echo        # Restore echo
  fi
  tput sgr0          # Reset terminal attributes
  tput cup $(tput lines) 0  # Move cursor to bottom
  exit 0
}
trap cleanup SIGINT SIGTERM

# Process the template once and store in memory buffer
process_template() {
  local term_width=$(tput cols)

  # Only reprocess if terminal width has changed
  if [ "$term_width" -ne "$last_term_width" ]; then
    # Clear the buffer
    template_buffer=()

    # Make sure we're working with a valid width
    if [ "$term_width" -lt 1 ]; then
      term_width=1
    fi

    # Process each line and store in buffer
    local line_num=0
		local truncate_size=$((term_width + template_actual_width))
    while IFS= read -r line || [ -n "$line" ]; do
      # Process the line and store in buffer
      template_buffer[$line_num]=$(truncate_line "$line" "$truncate_size")
      ((line_num++))
    done < "$STATIC_TEMPLATE_FILE"

    # Update the last terminal width
    last_term_width=$term_width
  fi
}

# Function to truncate a line preserving ANSI codes
truncate_line() {
  local line="$1"
  local max_width="$2"

  # Avoid processing empty lines
  if [ -z "$line" ]; then
    echo -n ""
    return
  fi

  # Remove ANSI codes to measure visible length
  local stripped=$(printf "%b" "$line" | sed 's/\x1b\[[0-9;]*m//g')

  # Calculate visible length considering Unicode characters
  local visible_length=$(printf "%b" "$stripped" | wc -m)

  if [ "$visible_length" -le "$max_width" ]; then
    # Line is already short enough - add terminal control to prevent wrapping
    printf "%b\r" "$line"
  else
    # Need to truncate - preserve ANSI codes while truncating
    local result=""
    local current_length=0
    local i=0
    local char
    local in_escape=0
    local escape_sequence=""

    while [ $current_length -lt "$max_width" ] && [ $i -lt ${#line} ]; do
      char="${line:$i:1}"

      if [ $in_escape -eq 1 ]; then
        escape_sequence+="$char"
        if [[ "$char" =~ [a-zA-Z] ]]; then
          # End of escape sequence
          result+="$escape_sequence"
          escape_sequence=""
          in_escape=0
        fi
      else
        if [ "$char" = $'\e' ]; then
          # Start of escape sequence
          escape_sequence="$char"
          in_escape=1
        else
          result+="$char"
          ((current_length++))
        fi
      fi

      ((i++))
    done

    # Add any remaining escape sequences
    if [ -n "$escape_sequence" ]; then
      result+="$escape_sequence"
    fi

    # Add reset code at the end to ensure proper termination
    result+="\033[0m"

    # Output with carriage return to prevent wrapping
    printf "%b\r" "$result"
  fi
}

# Draw the static template efficiently - all at once
draw_static_template() {
  # Process template first
  process_template

  # Clear screen and position cursor
  tput clear
  tput cup $top 0

  # Print the buffer in one go - much faster than line-by-line
  for line in "${template_buffer[@]}"; do
    # Clear to end of line before printing to eliminate any potential artifacts
    tput el
    printf "%b\n" "$line"
  done
}

# Improved resize handling with lock and batch processing
resize_requested=false
resize_in_progress=false
resize_delay=0.2  # seconds
last_resize_time=0

on_resize() {
  # Just mark that a resize was requested - don't process now
  resize_requested=true
}

process_resize_if_needed() {
  current_time=$(date +%s.%N)

  # If we're already processing a resize, don't start another one
  if [ "$resize_in_progress" = true ]; then
    return
  fi

  # If no resize is requested, nothing to do
  if [ "$resize_requested" = false ]; then
    return
  fi

  # Check if enough time has passed since last resize
  if [ "$last_resize_time" != "0" ]; then
    time_diff=$(echo "$current_time - $last_resize_time" | bc)
    if (( $(echo "$time_diff < $resize_delay" | bc -l) )); then
      # Not enough time has passed, wait more
      return
    fi
  fi

  # OK to process the resize now
  resize_in_progress=true
  resize_requested=false
  last_resize_time=$current_time

  # Get new dimensions
  new_width=$(tput cols)
  new_height=$(tput lines)

  # Process template with new dimensions
  process_template

  # Clear and redraw
  tput clear
  tput cup $top 0

  # Print buffer all at once with terminal control codes to prevent wrapping
  for line in "${template_buffer[@]}"; do
    # First clear to end of line to ensure no artifacts
    tput el
    printf "%b\n" "$line"
  done

  # Reset flag
  resize_in_progress=false
}

# Trap the SIGWINCH signal (window size change)
trap 'on_resize' SIGWINCH

# Initial draw
draw_static_template

# Start audio if num of args equals 7(sound is provided)
if [ $# -eq 7 ]; then
  ffplay -nodisp -autoexit -loop 0 -loglevel quiet "$soundname" &
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
    
    process_resize_if_needed
  done
  sleep 0.005  # Using your preferred faster check interval
done
