#Requires AutoHotkey v2.0

#HotIf WinActive("ahk_class CabinetWClass") || WinActive("ahk_class ExploreWClass")

^+c::
{
    paths := GetExplorerSelection()

    if !paths.Length
        return

    A_Clipboard := JoinPaths(paths)
}

#HotIf


GetExplorerSelection()
{
    paths := []

    shell := ComObject("Shell.Application")

    for window in shell.Windows
    {
        try
        {
            ; Obtener el HWND de la ventana COM
            if window.HWND != WinExist("A")
                continue

            ; Elementos actualmente seleccionados
            selection := window.Document.SelectedItems

            for item in selection
            {
                try
                {
                    paths.Push(item.Path)
                }
            }

            break
        }
        catch
        {
            ; Ignorar ventanas que no sean accesibles
        }
    }

    return paths
}


JoinPaths(paths)
{
    result := ""

    for index, path in paths
    {
        ; Cambiar "\" por "/"
        path := StrReplace(path, "\", "/")

        ; Añadir salto de línea entre rutas
        if index > 1
            result .= "`r`n"

        ; Añadir comillas alrededor de la ruta
        result .= '"' path '"'
    }

    return result
}