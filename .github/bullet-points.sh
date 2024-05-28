#!/bin/bash

# Check there is an empty line between lines ending in : and starting with - as mkdocs needs an empty line for bullet point formatting to work
check_file() {
  local file="$1"
  local prev_line=""
  local line_number=0
  local prev_line_number=0
  local empty_line=false
  local in_code_block=false

  while IFS= read -r line || [[ -n "$line" ]]; do
    line_number=$((line_number + 1))

    # Check if entering or exiting a code block
    if [[ $line == \`\`\`* ]]; then
      if [[ $in_code_block == false ]]; then
        in_code_block=true
      else
        in_code_block=false
      fi
    fi

    # Skip the check if within a code block
    if [[ $in_code_block == false ]]; then
      if [[ $prev_line == *: ]] && [[ $line == -* ]]; then
        if [[ $empty_line == false ]]; then
          echo "Error in file $file: Line $line_number - A line ending with ':' (line $prev_line_number) is immediately followed by a line starting with '-' without an empty line in between."
          exit 1
        fi
      fi
    fi

    if [[ -z $line ]]; then
      empty_line=true
    else
      empty_line=false
    fi

    prev_line="$line"
    prev_line_number=$line_number
  done < "$file"
}

# Check ../README.md
if [[ -f ../README.md ]]; then
  check_file "../README.md"
fi

# Check all .md files in the ../docs/docs folder
for file in $(find ../docs/docs -type f -name "*.md"); do
  check_file "$file"
done

echo "All specified .md files are properly formatted."