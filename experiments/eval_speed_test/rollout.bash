#!/bin/bash

g++ *.cpp -O3 -DIN_SCRIPT -o work

folder_path="cuts"

# Check if the folder exists
if [ ! -d "$folder_path" ]; then
  echo "Folder does not exist: $folder_path"
  exit 1
fi


# Iterate through each file in the folder
for file_path in "$folder_path"/*; do
  if [ -f "$file_path" ]; then
    # Extract two integers from the filename
    filename=$(basename "$file_path")

    if [[ "$filename" =~ ^([0-9]+)\ ([0-9]+)\ ([0-9]+)\.txt$ ]]; then
      threads="${BASH_REMATCH[1]}"
      loss="${BASH_REMATCH[2]}"
      predictedTime="${BASH_REMATCH[3]}"
      
      echo config $threads $loss
      echo predictedtime $predictedTime
      echo result $(./work $file_path)
    else
      echo "Skipping file with invalid format: $filename"
      exit 1
    fi
  fi
done