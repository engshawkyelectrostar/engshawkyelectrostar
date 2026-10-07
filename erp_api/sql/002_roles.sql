-- يوزر الـ API: قراءة من Views/جداول محددة + INSERT على api_requests بس. مفيش صلاحية على جداول الـ ERP للكتابة.
CREATE ROLE api_rw LOGIN PASSWORD 'change-me';
GRANT CONNECT ON DATABASE erp TO api_rw;
GRANT USAGE ON SCHEMA public TO api_rw;
-- GRANT SELECT ON customers, sales_invoices, sales_invoice_lines, stock_view TO api_rw;   -- جدول جدول، أو Views تخفي الأعمدة الحساسة
GRANT SELECT, INSERT ON api_requests TO api_rw;
