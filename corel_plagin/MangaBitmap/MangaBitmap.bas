Attribute VB_Name = "MangaBitmapPlagin"
' Manga Bitmap - CorelDRAW uchun plagin
' Rasmlarni (yoki barcha obyektlarni) bitmap qiladi: RGB / CMYK / Kulrang,
' istalgan razreshenie (DPI), har birini alohida yoki listdagi hammasini bitta
' bitmap qilib, yorqinlikni ochroq / to'qroq qilish imkoniyati bilan.
'
' Ishga tushirish: Tools > Macros > Run Macro > MangaBitmapPlagin.MangaBitmap
' (yoki shu makrosga tugma / tezkor tugma biriktiring).

Public Sub MangaBitmap()
    If Documents.Count = 0 Then
        MsgBox "Avval hujjat oching.", vbExclamation, "Manga Bitmap"
        Exit Sub
    End If
    frmMangaBitmap.Show vbModeless
End Sub
