$root = (Get-Location).Path

Get-ChildItem -Recurse -Include *.py, *.md, requirements.txt, pyproject.toml |
Where-Object {
    $_.FullName -notmatch '(\.git|__pycache__|venv|env|static)'
} |
ForEach-Object {
    $_.FullName.Replace($root, '').TrimStart('/', '\')
} |
Out-File estructura_minimal.txt
