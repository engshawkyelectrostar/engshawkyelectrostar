<%@ Language="VBScript" CodePage=65001 %>
<!--#include file="../lib/api.asp"-->
<!--#include file="../lib/json.asp"-->
<!--#include file="../lib/db.asp"-->
<%
ApiInit "GET"
Dim conn, rs
On Error Resume Next
Set conn = OpenConn()
If Err.Number <> 0 Then FailServer "health: connect"
Set rs = RunQuery(conn, "SELECT 1 AS ok FROM DUAL", Empty)
If Err.Number <> 0 Then FailServer "health: query"
Response.Write "{""ok"":true,""db"":""up"",""time"":" & JsonStr(Now()) & "}"
rs.Close: conn.Close
%>
