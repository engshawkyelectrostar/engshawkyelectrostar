-- PostgreSQL: جدول الطلبات (staging) للكتابة. الـ AI/n8n بيكتب هنا بس، مش في جداول الـ ERP.
CREATE TABLE api_requests (
  id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  req_type     VARCHAR(50)  NOT NULL,
  payload      JSONB        NOT NULL,
  status       VARCHAR(20)  NOT NULL DEFAULT 'PENDING'
               CHECK (status IN ('PENDING','APPROVED','REJECTED','DONE','FAILED')),
  created_by   VARCHAR(50),
  created_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
  approved_by  VARCHAR(50),
  approved_at  TIMESTAMPTZ,
  result_msg   TEXT
);
CREATE INDEX api_requests_status_idx ON api_requests (status, created_at);
-- التنفيذ الفعلي بعد APPROVED: دالة/Procedure (مثال: erp.process_request(id)) بتستدعي نفس منطق الـ ERP.
