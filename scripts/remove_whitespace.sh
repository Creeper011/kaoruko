find . -name "*.py" -type f -print0 | while IFS= read -r -d '' file; do
    sed -i 's/[ \t]*$//' "$file"
done