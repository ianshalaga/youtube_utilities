$root = (Get-Location).Path
$output = "estructura_ia.txt"

if (Test-Path $output) {
    Remove-Item $output
}

Get-ChildItem -Recurse -File | ForEach-Object {

    if ($_.FullName -match ".git") { return }
    if ($_.FullName -match "__pycache__") { return }

    $rel = $_.FullName.Substring($root.Length)
    if ($rel.StartsWith("\")) {
        $rel = $rel.Substring(1)
    }

    Add-Content $output "FILE $rel"
    Add-Content $output "-----"
    Get-Content $_.FullName | Add-Content $output
    Add-Content $output ""
}
