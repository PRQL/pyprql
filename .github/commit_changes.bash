#!/bin/bash

set -eu

STAGED_FILES=$(git diff --name-only --diff-filter=M)

if [[ $STAGED_FILES != "" ]]; then
  git add $STAGED_FILES &&
  git commit -m "refactor(*): blacken files"
fi
