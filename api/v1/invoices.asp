<%@ Language="VBScript" CodePage=65001 %>
<!--#include file="../lib/api.asp"-->
<!--#include file="../lib/json.asp"-->
<!--#include file="../lib/db.asp"-->
<%
' GET /api/v1/invoices.asp?from=2026-01-01&to=2026-01-31&cust_id=123&limit=50
' مثال فقط: SALES_INVOICES وأعمدتها عدّلها حسب الـ schema عندك
ApiInit "GET"
Dim dFrom, dTo, custId, lim, conn, rs, sql, params
dFrom = DateParam("from")
dTo = DateParam("to")
custId = IntParam("cust_id", 0, 0, 2147483647)
lim = IntParam("limit", 50, 1, 200)

sql = "SELECT * FROM (SELECT inv_no, inv_date, cust_id, total_amount, status FROM sales_invoices WHERE 1=1"
params = Array()
If Len(dFrom) > 0 Then
  sql = sql & " AND inv_date >= TO_DATE(?, 'YYYY-MM-DD')"
  ReDim Preserve params(UBound(params) + 1): params(UBound(params)) = dFrom
End If
If Len(dTo) > 0 Then
  sql = sql & " AND inv_date < TO_DATE(?, 'YYYY-MM-DD') + 1"
  ReDim Preserve params(UBound(params) + 1): params(UBound(params)) = dTo
End If
If custId > 0 Then
  sql = sql & " AND cust_id = ?"
  ReDim Preserve params(UBound(params) + 1): params(UBound(params)) = custId
End If
sql = sql & " ORDER BY inv_date DESC) WHERE ROWNUM <= " & lim

On Error Resume Next
Set conn = OpenConn()
If Err.Number <> 0 Then FailServer "invoices: connect"
Set rs = RunQuery(conn, sql, params)
If Err.Number <> 0 Then FailServer "invoices: query"
Response.Write RecordsetToJson(rs, lim)
rs.Close: conn.Close
%>
