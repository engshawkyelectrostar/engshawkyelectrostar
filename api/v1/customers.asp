<%@ Language="VBScript" CodePage=65001 %>
<!--#include file="../lib/api.asp"-->
<!--#include file="../lib/json.asp"-->
<!--#include file="../lib/db.asp"-->
<%
' GET /api/v1/customers.asp?q=<جزء من الاسم>&limit=20
' مثال فقط: CUSTOMERS / CUST_ID / CUST_NAME / PHONE / BALANCE عدّلهم حسب الـ schema عندك
ApiInit "GET"
Dim q, lim, conn, rs, sql
q = Trim(Request.QueryString("q"))
If Len(q) > 60 Then q = Left(q, 60)
lim = IntParam("limit", 20, 1, 100)

sql = "SELECT * FROM (" & _
      "  SELECT cust_id, cust_name, phone, balance FROM customers" & _
      "  WHERE UPPER(cust_name) LIKE UPPER(?) ORDER BY cust_name" & _
      ") WHERE ROWNUM <= " & lim      ' Oracle 11g: مفيش FETCH FIRST، بنستخدم ROWNUM (lim رقم متحقق منه)

On Error Resume Next
Set conn = OpenConn()
If Err.Number <> 0 Then FailServer "customers: connect"
Set rs = RunQuery(conn, sql, Array("%" & q & "%"))
If Err.Number <> 0 Then FailServer "customers: query"
Response.Write RecordsetToJson(rs, lim)
rs.Close: conn.Close
%>
