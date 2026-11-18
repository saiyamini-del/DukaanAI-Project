# Dukaan AI – Voice-Based Smart Digital Ledger for Small Businesses (English Edition)

> **AI-Powered Digital Bookkeeping & Shop Management Platform with English Voice Recognition.**

---

## 🌟 Overview & Solved Problems
Many small shopkeepers and retail merchants track daily sales, customer credit, and debt settlements manually in paper notebooks. This traditional process causes:
- Calculation errors and missing records.
- Difficulty monitoring overdue customer credit balances.
- Time lost writing down entries after every customer visit.

**Dukaan AI** eliminates manual bookkeeping by offering:
1. **English Voice-Based Entry**: Speak naturally into your microphone or type English transaction phrases.
2. **AI Intent & Entity Extraction**: Automatically extracts the Customer Name, Amount (₹), Transaction Type (Credit Given vs Payment Received), and Items/Notes.
3. **Automated Khata & Real-Time Balance**: Recalculates net dues instantly upon saving.
4. **Instant WhatsApp Payment Reminders**: Generates 1-click polite English payment reminders with shop name, balance due, and UPI ID.
5. **Full SQLite Database Persistence**: Relational storage (`dukaan_ai.db`) with zero risk of lost data.

---

## 📁 Project Structure
```
dukaan-ai/
├── app.py               # Main Streamlit Web Application (English UI & Modules)
├── database.py          # SQLite schema, queries, CRUD, KPI calculations & English seed data
├── voice_nlp.py         # English NLP voice & text entity extractor
├── whatsapp_helper.py   # English WhatsApp payment reminder link generator
├── requirements.txt     # Python requirements (streamlit, pandas)
├── dukaan_ai.db         # Persistent SQLite database
└── README.md            # Documentation & user manual
```

---

## 🚀 How to Run the Web Application

### Step 1: Open Terminal / PowerShell
Navigate to the project directory:
```powershell
cd "C:\Users\k naga sai yamini\.gemini\antigravity\scratch\dukaan-ai"
```

### Step 2: Launch Streamlit
Run with Python:
```powershell
& "C:\Users\k naga sai yamini\AppData\Local\Programs\Python\Python313\python.exe" -m streamlit run app.py
```
*(Or simply `streamlit run app.py` if python is on your standard PATH)*

The application will launch and open in your browser at `http://localhost:8501`.

---

## 🗣️ Supported English Voice Commands

| Example Spoken Input | Extracted Type | Extracted Customer | Extracted Amount | Extracted Note |
| :--- | :--- | :--- | :--- | :--- |
| *"Gave 500 to Ramesh for rice and dal"* | 🔴 GIVEN (Credit) | Ramesh | ₹500 | rice dal |
| *"Received 300 from Suresh cash"* | 🟢 RECEIVED (Cash In) | Suresh | ₹300 | cash |
| *"Rahul Sharma credit 450 for groceries"* | 🔴 GIVEN (Credit) | Rahul Sharma | ₹450 | groceries |
| *"Received 1200 from Venkat Rao via UPI"* | 🟢 RECEIVED (Cash In) | Venkat Rao | ₹1,200 | UPI |
| *"Pooja Patel paid 500 complete balance"* | 🟢 RECEIVED (Cash In) | Pooja Patel | ₹500 | complete balance |
| *"Lent 650 to Shiva for cooking oil"* | 🔴 GIVEN (Credit) | Shiva | ₹650 | cooking oil |

---

## 🛠️ Included Core Modules (All in English)

1. **📊 Business Dashboard**:
   - Total Pending Credit to Collect, Cash Collected Today, Credit Given Today, Active Debtors.
   - 7-day trend chart (Credit Given vs Cash Collected) & Top pending customer dues table.
   - Live recent transactions stream.

2. **🎙️ Voice Assistant (AI Voice Khata)**:
   - Microphone Speech Recognition widget (`en-IN`, `en-US`, `en-GB`).
   - Instant NLP entity extraction card showing customer name, amount, type badge, and notes.
   - One-click testing presets for instant testing without a microphone.
   - Review and save directly into the ledger.

3. **👥 Customer Management (Khata Book)**:
   - Customer search by name or phone.
   - Add new customers with phone validation.
   - Complete ledger statement history per customer.
   - 1-click **English WhatsApp Reminder** generator with UPI payment links.

4. **📖 Digital Ledger**:
   - Filter by date range, transaction type (All/Given/Received), or customer.
   - Manual "+ Add Transaction" entry modal.
   - CSV export for accounting and backups.

5. **📈 Reports & Aging Analysis**:
   - Customer balance distribution chart.
   - Overdue credit aging buckets (0–15 days, 16–30 days, 30+ days overdue).

6. **⚙️ Shop Settings & Preloaded Demo Data**:
   - Store name, owner name, contact number, and UPI ID configuration.
   - One-click button to preload realistic retail store demo data in English.
