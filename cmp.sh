#!/bin/bash

# Generate the commit message using git diff and Ollama
commit_message=$(git diff --cached | ollama run llama3.2 "output must not be less than 10 words. explain what changed in the code. output only 10 words.")
# Check if a commit message was generated
if [ -z "$commit_message" ]; then
  echo "No commit message generated. Aborting."
  exit 1
fi

# Display the generated commit message and ask for approval
echo "Generated commit message:"
echo "\"$commit_message\""
read -p "Do you want to proceed with this commit? (yes/no): " user_input

if [[ "$user_input" != "yes" ]]; then
  echo "Commit aborted by user."
  exit 0
fi

# Perform the commit with the generated message
git commit -m "$commit_message"

# Check if commit was successful
if [ $? -ne 0 ]; then
  echo "Commit failed. Not pushing."
  exit 1
fi


# Push the changes
git push
if [ $? -eq 0 ]; then
  echo "Changes pushed successfully."
else
  echo "Push failed."
  exit 1
fi