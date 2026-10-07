<%
' json.asp - تحويل Recordset إلى JSON بدون أي مكتبات خارجية

Function JsonStr(s)
  If IsNull(s) Or IsEmpty(s) Then JsonStr = "null": Exit Function
  Dim i, c, code, o
  s = CStr(s)
  o = ""
  For i = 1 To Len(s)
    c = Mid(s, i, 1)
    code = AscW(c)
    Select Case code
      Case 34: o = o & "\"""
      Case 92: o = o & "\\"
      Case 8:  o = o & "\b"
      Case 9:  o = o & "\t"
      Case 10: o = o & "\n"
      Case 12: o = o & "\f"
      Case 13: o = o & "\r"
      Case Else
        ' AscW بترجع قيم سالبة للحروف العربية - لازم نتأكد إنها >= 0
        If code >= 0 And code < 32 Then
          o = o & "\u" & Right("0000" & Hex(code), 4)
        Else
          o = o & c
        End If
    End Select
  Next
  JsonStr = """" & o & """"
End Function

Function Pad2(n)
  Pad2 = Right("0" & n, 2)
End Function

Function JsonValue(v, ftype)
  If IsNull(v) Then JsonValue = "null": Exit Function
  Select Case ftype
    Case 2, 3, 4, 5, 6, 14, 16, 17, 18, 19, 20, 21, 131, 139
      ' أرقام - نضمن النقطة العشرية بغض النظر عن Regional Settings
      JsonValue = Replace(CStr(v), ",", ".")
    Case 11
      If v Then JsonValue = "true" Else JsonValue = "false"
    Case 7, 133, 135
      JsonValue = """" & Year(v) & "-" & Pad2(Month(v)) & "-" & Pad2(Day(v)) & _
                  " " & Pad2(Hour(v)) & ":" & Pad2(Minute(v)) & ":" & Pad2(Second(v)) & """"
    Case Else
      JsonValue = JsonStr(v)
  End Select
End Function

' بيرجع {"ok":true,"count":N,"truncated":false,"data":[...]}
Function RecordsetToJson(rs, maxRows)
  Dim cols(), types(), n, i, rowsArr(), cnt, parts(), truncated
  n = rs.Fields.Count
  ReDim cols(n - 1): ReDim types(n - 1): ReDim parts(n - 1)
  For i = 0 To n - 1
    cols(i) = """" & LCase(rs.Fields(i).Name) & """:"
    types(i) = rs.Fields(i).Type
  Next

  cnt = 0
  ReDim rowsArr(maxRows)
  Do While Not rs.EOF And cnt < maxRows
    For i = 0 To n - 1
      parts(i) = cols(i) & JsonValue(rs.Fields(i).Value, types(i))
    Next
    rowsArr(cnt) = "{" & Join(parts, ",") & "}"
    cnt = cnt + 1
    rs.MoveNext
  Loop
  truncated = Not rs.EOF

  If cnt = 0 Then
    RecordsetToJson = "{""ok"":true,""count"":0,""truncated"":false,""data"":[]}"
  Else
    ReDim Preserve rowsArr(cnt - 1)
    RecordsetToJson = "{""ok"":true,""count"":" & cnt & ",""truncated"":" & LCase(CStr(truncated)) & _
                      ",""data"":[" & Join(rowsArr, ",") & "]}"
  End If
End Function
%>
