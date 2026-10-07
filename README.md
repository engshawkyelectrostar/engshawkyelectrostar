# ربط ERP (ASP Classic + Oracle 11g) بالـ AI عن طريق n8n

## المعمارية

```
المستخدم ──> n8n (AI Agent + HTTP Request Tools) ──HTTPS + X-API-Key──> IIS (api/v1/*.asp) ──OraOLEDB──> Oracle 11g (AIX)
```

- **مفيش AI بيكلم الداتابيز مباشرة.** الـ AI بيستدعي endpoints محددة ومعرّفة مسبقًا (whitelist)، وكل endpoint فيه SQL ثابت بـ bind parameters.
- نفس الـ endpoints بتتستخدم من n8n، من أي نظام تاني، أو من تطبيق موبايل.
- الـ ERP القديم بيفضل شغال زي ما هو؛ الـ API مجرد طبقة جنبه (`/api/`) على نفس الـ IIS.

## اللي في الريبو

| المسار | الوظيفة |
|---|---|
| `api/lib/api.asp` | الإعدادات، التحقق من `X-API-Key` وIP، معالجة الأخطاء، فحص الباراميترات |
| `api/lib/json.asp` | تحويل Recordset لـ JSON (بيدعم العربي والتواريخ والأرقام بدون مكتبات) |
| `api/lib/db.asp` | اتصال أوراكل + `RunQuery` بـ bind parameters |
| `api/v1/health.asp` | فحص الـ API والداتابيز |
| `api/v1/customers.asp`, `invoices.asp` | **أمثلة** — غيّر أسماء الجداول/الأعمدة لجداولك |
| `api/web.config` | إخفاء `lib/`، السماح بـ GET/POST بس، headers أمان |
| `api/openapi.yaml` | وصف الـ API (مفيد لتوثيق الأدوات وتعريفها للـ AI) |
| `n8n/erp-ai-agent.workflow.json` | Workflow جاهز: Chat → AI Agent + أداتين (استورده من n8n: Import from File) |

## خطوات التركيب على السيرفر

1. **Oracle Client على سيرفر IIS**: ثبّت Oracle Data Access Components (ODAC / OraOLEDB). لازم bitness الـ Client يطابق الـ Application Pool (لو الـ ERP على Pool 32-bit استخدم Client 32-bit، وفعّل *Enable 32-Bit Applications*). عرّف الـ TNS أو استخدم Easy Connect: `host:1521/SERVICE`.
2. **يوزر أوراكل مخصص للـ API** (قراءة فقط):
   ```sql
   CREATE USER api_ro IDENTIFIED BY "<strong-password>";
   GRANT CREATE SESSION TO api_ro;
   GRANT SELECT ON erp.customers TO api_ro;      -- جدول جدول، مش SELECT ANY TABLE
   GRANT SELECT ON erp.sales_invoices TO api_ro;
   -- الأفضل: Views مخصصة تخفي الأعمدة الحساسة ثم GRANT على الـ Views
   ```
3. **انسخ مجلد `api/`** إلى موقع جديد/Application على IIS (مثلًا `Default Web Site/api`) وفعّل HTTPS (شهادة صالحة) — بدون HTTPS مفتاح الـ API هيعدي clear text.
4. **Environment Variables (System)** ثم `iisreset`:
   ```
   ERP_API_KEY          = <مفتاح عشوائي 32+ حرف>
   ERP_API_ALLOWED_IPS  = <IP سيرفر n8n>
   ERP_ORA_CONN         = Provider=OraOLEDB.Oracle;Data Source=aixhost:1521/ORCL;User Id=api_ro;Password=...;
   ERP_API_LOG          = D:\logs\erp-api.log     (خارج wwwroot، والـ App Pool identity لها صلاحية Write)
   ```
5. في IIS Manager → ASP → **Send Errors to Browser = False**.
6. جرّب: `curl -H "X-API-Key: ..." https://erp.example.com/api/v1/health.asp`
7. **n8n**: Import للـ workflow، أنشئ Credential من نوع *Header Auth* (`X-API-Key`)، اربطه بالأداتين، وحط الـ Anthropic API key، وغيّر الـ URL.

## ملاحظات أوراكل 11g / AIX

- **الترقيم**: `ROWNUM` (مفيش `FETCH FIRST`/`OFFSET` في 11g).
- **العربي**: الـ API بيرد UTF-8 (`CodePage=65001`). لو قاعدة البيانات `AR8MSWIN1256` الـ Client بيحوّل تلقائيًا؛ لو ظهرت علامات استفهام اضبط `NLS_LANG` على سيرفر IIS (مثلًا `ARABIC_EGYPT.AR8MSWIN1256` أو `.AL32UTF8` حسب الداتابيز).
- **Oracle NUMBER** بيتحول لأرقام JSON، والـ DATE لـ `"YYYY-MM-DD HH:MM:SS"`.
- أسماء الأعمدة في الـ JSON بتطلع lowercase.
- لو الداتابيز مش مفتوحة من سيرفر IIS افتح بورت الـ Listener (1521) بين الاتنين بس.

## الأمان (مهم جدًا لأن فيه AI)

- ✅ قراءة فقط كبداية؛ اليوزر مالوش INSERT/UPDATE/DELETE.
- ✅ مفيش endpoint بياخد SQL أو أسماء جداول من بره.
- ✅ كل القيم bind parameters + حدود على الـ limit والنصوص.
- ✅ مفتاح API + IP allowlist + HTTPS. لا تعرض الـ API على الإنترنت مباشرة؛ الأفضل VPN أو Reverse Proxy مع IP restriction.
- ✅ أخطاء أوراكل ما بترجعش للعميل (بتتسجل في اللوج بس).
- ⚠️ **الكتابة** (إنشاء أمر بيع/سند…): متخليش الـ AI يكتب مباشرة في جداول الـ ERP. اعمل endpoint يكتب في جدول staging + خطوة موافقة بشرية (n8n *Wait* node / Form)، أو استدعي نفس Stored Procedures اللي الـ ERP بيستخدمها.
- ⚠️ بيانات حساسة (رواتب، أسعار تكلفة): متديهاش للـ API أصلًا — GRANT على Views محدودة.

## إضافة Endpoint جديد

1. انسخ `customers.asp` بالاسم الجديد.
2. عدّل الـ SQL (بعلامات `?` للقيم) والباراميترات.
3. أضفه في `openapi.yaml` وأضف HTTP Request Tool جديد في n8n بوصف واضح (الـ AI بيختار الأداة من الوصف).

## بدائل

- **Oracle REST Data Services (ORDS)**: بيعمل REST من غير ASP، لكن النسخ الحديثة بتطلب Java حديث ومش كلها بتدعم 11g، وبتحتاج تثبيت على سيرفر مناسب — الحل الحالي أخف وبيستغل الـ IIS الموجود.
- **n8n متصل بأوراكل مباشرة**: n8n مفيهوش Oracle node رسمي؛ ده كمان بيفتح الداتابيز للـ AI Workflows، فمش مُفضّل.

## اللي محتاجه منك عشان نكمّل

1. أهم 10–20 وظيفة عايز الـ AI يجاوب عليها (مبيعات، مخزون، أرصدة عملاء…).
2. أسماء الجداول/الـ Views المعنية وأعمدتها (أو DDL).
3. هل n8n مثبّت فين (Docker على Linux؟ cloud؟) وهل بيوصل لسيرفر IIS داخليًا؟
4. هل المطلوب قراءة بس ولا فيه عمليات كتابة؟
