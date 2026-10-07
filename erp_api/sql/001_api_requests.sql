-- Oracle 11g: جدول الطلبات (staging) للكتابة + سجل تدقيق
CREATE SEQUENCE api_requests_seq START WITH 1 INCREMENT BY 1 NOCACHE;

CREATE TABLE api_requests (
  id           NUMBER PRIMARY KEY,
  req_type     VARCHAR2(50)  NOT NULL,
  payload      CLOB          NOT NULL,
  status       VARCHAR2(20)  DEFAULT 'PENDING' NOT NULL
               CONSTRAINT api_requests_status_ck CHECK (status IN ('PENDING','APPROVED','REJECTED','DONE','FAILED')),
  created_by   VARCHAR2(50),
  created_at   DATE DEFAULT SYSDATE,
  approved_by  VARCHAR2(50),
  approved_at  DATE,
  result_msg   VARCHAR2(4000)
);
-- التنفيذ الفعلي بعد APPROVED: Stored Procedure (مثال: erp_pkg.process_request(id)) بتستدعي نفس منطق الـ ERP.
