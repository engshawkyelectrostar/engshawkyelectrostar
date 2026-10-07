<%
' db.asp - اتصال أوراكل + تنفيذ استعلامات بـ Bind Parameters (مفيش string concatenation للقيم أبدًا)

Function OpenConn()
  Dim c, cs
  cs = EnvVar("ERP_ORA_CONN")
  Set c = Server.CreateObject("ADODB.Connection")
  c.ConnectionTimeout = 10
  c.Open cs
  c.CommandTimeout = 30
  Set OpenConn = c
End Function

' params = Array(v1, v2, ...) بترتيب علامات الاستفهام (?) في الـ SQL
Function RunQuery(conn, sql, params)
  Dim cmd, i, v, sz
  Set cmd = Server.CreateObject("ADODB.Command")
  Set cmd.ActiveConnection = conn
  cmd.CommandText = sql
  cmd.CommandType = 1
  If IsArray(params) Then
    For i = 0 To UBound(params)
      v = params(i)
      If VarType(v) = 8 Then
        sz = Len(v): If sz < 1 Then sz = 1
        cmd.Parameters.Append cmd.CreateParameter("p" & i, 200, 1, sz, v)
      Else
        cmd.Parameters.Append cmd.CreateParameter("p" & i, 5, 1, , CDbl(v))
      End If
    Next
  End If
  Set RunQuery = cmd.Execute
End Function
%>
