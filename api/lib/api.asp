<%
Option Explicit
' ---------------------------------------------------------------
' api.asp - الإعدادات + المصادقة + دوال الرد المشتركة
' الإعدادات بتتقرا من Environment Variables (System) على السيرفر:
'   ERP_API_KEY          مفتاح الـ API (مطلوب، 32+ حرف عشوائي)
'   ERP_API_ALLOWED_IPS  IPs مسموحة مفصولة بفاصلة (اختياري بس مُفضّل - IP بتاع n8n)
'   ERP_ORA_CONN         connection string لأوراكل
'   ERP_API_LOG          مسار ملف لوج خارج الـ wwwroot (اختياري)
' بعد تغيير أي متغير: iisreset
' ---------------------------------------------------------------

Function EnvVar(name)
  Dim sh: Set sh = Server.CreateObject("WScript.Shell")
  EnvVar = sh.Environment("SYSTEM")(name)
End Function

Function StatusText(code)
  Select Case code
    Case 400: StatusText = "Bad Request"
    Case 401: StatusText = "Unauthorized"
    Case 403: StatusText = "Forbidden"
    Case 405: StatusText = "Method Not Allowed"
    Case Else: StatusText = "Internal Server Error"
  End Select
End Function

Sub LogError(msg)
  On Error Resume Next
  Dim path: path = EnvVar("ERP_API_LOG")
  If Len(path) = 0 Then Exit Sub
  Dim fso, f
  Set fso = Server.CreateObject("Scripting.FileSystemObject")
  Set f = fso.OpenTextFile(path, 8, True)
  f.WriteLine Now() & " | " & Request.ServerVariables("REMOTE_ADDR") & " | " & Request.ServerVariables("URL") & " | " & msg
  f.Close
End Sub

Sub SendError(code, msg)
  Response.Status = code & " " & StatusText(code)
  Response.Write "{""ok"":false,""error"":""" & Replace(msg, """", "'") & """}"
  Response.End
End Sub

' خطأ داخلي: التفاصيل في اللوج بس، والعميل (والـ AI) ياخد رسالة عامة
Sub FailServer(context)
  LogError context & " | " & Err.Number & " | " & Err.Description
  SendError 500, "internal error"
End Sub

Function SafeEqual(a, b)
  Dim i, diff
  If Len(a) <> Len(b) Then SafeEqual = False: Exit Function
  diff = 0
  For i = 1 To Len(a)
    diff = diff Or (AscW(Mid(a, i, 1)) Xor AscW(Mid(b, i, 1)))
  Next
  SafeEqual = (diff = 0)
End Function

Function IpAllowed()
  Dim list, parts, i, ip
  list = EnvVar("ERP_API_ALLOWED_IPS")
  If Len(list) = 0 Then IpAllowed = True: Exit Function
  ip = Request.ServerVariables("REMOTE_ADDR")
  parts = Split(Replace(list, " ", ""), ",")
  For i = 0 To UBound(parts)
    If parts(i) = ip Then IpAllowed = True: Exit Function
  Next
  IpAllowed = False
End Function

' أول سطر في كل endpoint: ApiInit "GET"
Sub ApiInit(allowedMethod)
  Response.CodePage = 65001
  Response.Charset = "utf-8"
  Response.ContentType = "application/json"
  Response.CacheControl = "no-store"

  If Request.ServerVariables("REQUEST_METHOD") <> allowedMethod Then SendError 405, "method not allowed"
  If Not IpAllowed() Then SendError 403, "forbidden"

  Dim key: key = EnvVar("ERP_API_KEY")
  If Len(key) < 16 Then LogError "ERP_API_KEY not configured": SendError 500, "internal error"
  If Not SafeEqual(Request.ServerVariables("HTTP_X_API_KEY"), key) Then SendError 401, "unauthorized"
End Sub

' قراءة باراميتر رقمي بحدود آمنة (ضد قيم غريبة جاية من الـ AI)
Function IntParam(name, defaultVal, minVal, maxVal)
  Dim v: v = Trim(Request.QueryString(name))
  If Len(v) = 0 Or Len(v) > 9 Or Not IsNumeric(v) Then IntParam = defaultVal: Exit Function
  v = CLng(v)
  If v < minVal Then v = minVal
  If v > maxVal Then v = maxVal
  IntParam = v
End Function

' تاريخ بصيغة YYYY-MM-DD أو فاضي
Function DateParam(name)
  Dim v: v = Trim(Request.QueryString(name))
  If Len(v) = 10 And Mid(v, 5, 1) = "-" And Mid(v, 8, 1) = "-" And IsNumeric(Left(v, 4)) And IsNumeric(Mid(v, 6, 2)) And IsNumeric(Right(v, 2)) Then
    DateParam = v
  Else
    DateParam = ""
  End If
End Function
%>
