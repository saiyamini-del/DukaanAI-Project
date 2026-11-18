"""
app.py - Main Streamlit Web Application for Dukaan AI (English Edition)
Voice-Based Smart Digital Ledger for Small Businesses & Retail Merchants.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import sqlite3
import os

# Import modular layers
import database as db
import voice_nlp as nlp
import whatsapp_helper as wa

# Initialize database
db.init_db()

# Page configuration
st.set_page_config(
    page_title="Dukaan AI – Voice Digital Ledger",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Mobile-friendly, high contrast, clean cards)
st.markdown("""
<style>
    /* Main branding accents */
    :root {
        --primary-color: #0f766e;
        --secondary-color: #ea580c;
        --success-color: #16a34a;
        --danger-color: #dc2626;
        --bg-soft: #f8fafc;
    }
    
    /* Card design */
    .metric-box {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        margin-bottom: 12px;
    }
    .metric-value-given {
        font-size: 26px;
        font-weight: 700;
        color: #dc2626;
    }
    .metric-value-received {
        font-size: 26px;
        font-weight: 700;
        color: #16a34a;
    }
    .metric-value-neutral {
        font-size: 26px;
        font-weight: 700;
        color: #0284c7;
    }
    .metric-label {
        font-size: 13px;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-sub {
        font-size: 12px;
        color: #64748b;
        margin-top: 4px;
    }
    
    /* Badges */
    .badge-given {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-received {
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Fetch settings
settings = db.get_settings()
shop_name = settings.get("shop_name", "Sri Lakshmi Supermarket & General Store")
owner_name = settings.get("owner_name", "Ramesh Babu")
shop_phone = settings.get("phone", "9876543210")
upi_id = settings.get("upi_id", "dukaan@upi")

# ----------------- Sidebar Navigation ----------------- #
with st.sidebar:
    st.markdown("### 🏪 **Dukaan AI**")
    st.markdown(f"**{shop_name}**")
    st.caption(f"👤 Merchant: **{owner_name}** | 💳 UPI: `{upi_id}`")
    st.divider()

    navigation = st.radio(
        "Navigation Menu",
        [
            "📊 Dashboard",
            "🎙️ Voice Assistant",
            "👥 Customer Management",
            "📖 Digital Ledger",
            "📈 Reports & Analytics",
            "⚙️ Shop Settings & Data"
        ],
        index=0
    )

    st.divider()
    st.info("💡 **Voice Tip**: Speak naturally, e.g. *'Gave 500 to Ramesh for groceries'* or *'Received 300 from Suresh'*. Dukaan AI records it automatically.")

# ----------------- TAB 1: DASHBOARD ----------------- #
if "Dashboard" in navigation:
    st.markdown("## 📊 Business Overview & Dashboard")
    st.caption("Real-time snapshot of daily sales, customer credit balances, and cash collections.")

    kpis = db.get_dashboard_kpis()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">To Collect (Pending Credit)</div>
            <div class="metric-value-given">₹{kpis['total_dues_to_collect']:,.2f}</div>
            <div class="metric-sub">Total credit due from {kpis['active_debtors']} customers</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Collected Today (Cash In)</div>
            <div class="metric-value-received">₹{kpis['today_collected']:,.2f}</div>
            <div class="metric-sub">Debt settlements & payments today</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Given Today (Credit Out)</div>
            <div class="metric-value-given">₹{kpis['today_credit_given']:,.2f}</div>
            <div class="metric-sub">New store credit issued today</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Total Customers</div>
            <div class="metric-value-neutral">{kpis['total_customers']}</div>
            <div class="metric-sub">{kpis['today_tx_count']} transactions recorded today</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Visual Analytics & Quick Views
    c_left, c_right = st.columns([3, 2])

    with c_left:
        st.subheader("📊 7-Day Credit vs Cash Collections")
        tx_data = db.get_transactions(limit=100)
        if tx_data:
            df_tx = pd.DataFrame(tx_data)
            df_tx["date"] = pd.to_datetime(df_tx["date"])
            recent_dates = df_tx[df_tx["date"] >= (datetime.today() - timedelta(days=7))]

            if not recent_dates.empty:
                daily_summary = recent_dates.groupby(["date", "type"])["amount"].sum().unstack(fill_value=0).reset_index()
                daily_summary["date"] = daily_summary["date"].dt.strftime("%d %b")
                
                if "GIVEN" not in daily_summary.columns:
                    daily_summary["GIVEN"] = 0
                if "RECEIVED" not in daily_summary.columns:
                    daily_summary["RECEIVED"] = 0

                daily_summary = daily_summary.rename(columns={
                    "GIVEN": "Credit Given (Udhar)",
                    "RECEIVED": "Cash Collected (Jama)"
                })
                daily_summary = daily_summary.set_index("date")
                st.bar_chart(daily_summary, color=["#dc2626", "#16a34a"])
            else:
                st.info("No transactions recorded in the past 7 days.")
        else:
            st.info("No transaction history available.")

    with c_right:
        st.subheader("⚠️ Top Pending Balances")
        customers = db.get_customers()
        debtors = [c for c in customers if c["net_balance"] > 0][:5]
        if debtors:
            df_deb = pd.DataFrame(debtors)[["name", "net_balance", "phone"]]
            df_deb["net_balance"] = df_deb["net_balance"].apply(lambda x: f"₹{x:,.2f}")
            df_deb.columns = ["Customer Name", "Pending Due", "Phone"]
            st.dataframe(df_deb, use_container_width=True, hide_index=True)
        else:
            st.success("🎉 All customer balances are fully settled! No pending dues.")

    # Recent Transactions Feed
    st.subheader("🕒 Recent Transactions")
    recent_txs = db.get_transactions(limit=6)
    if recent_txs:
        for tx in recent_txs:
            col_icon, col_details, col_amt = st.columns([1.5, 6, 2])
            with col_icon:
                if tx["type"] == "GIVEN":
                    st.markdown("<span class='badge-given'>🔴 CREDIT GIVEN</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span class='badge-received'>🟢 CASH RECEIVED</span>", unsafe_allow_html=True)
            with col_details:
                note_str = f" – *{tx['note']}*" if tx['note'] else ""
                st.markdown(f"**{tx['customer_name']}** ({tx['date']}){note_str}")
            with col_amt:
                color = "#dc2626" if tx["type"] == "GIVEN" else "#16a34a"
                sign = "+" if tx["type"] == "GIVEN" else "-"
                st.markdown(f"<span style='font-size:18px; font-weight:700; color:{color};'>{sign}₹{tx['amount']:,.2f}</span>", unsafe_allow_html=True)
            st.divider()
    else:
        st.info("No recent transactions found.")

# ----------------- TAB 2: VOICE ASSISTANT ----------------- #
elif "Voice Assistant" in navigation:
    st.markdown("## 🎙️ AI Voice Ledger Assistant")
    st.caption("Speak or enter your store transaction in English. Dukaan AI automatically detects the customer name, amount, credit type, and item notes.")

    # HTML5 Speech Recognition Widget Component (Configured for English)
    speech_widget_html = """
    <div style="background: linear-gradient(135deg, #0f766e 0%, #0369a1 100%); color: white; padding: 22px; border-radius: 12px; margin-bottom: 20px; text-align: center;">
        <h3 style="margin: 0; color: white;">🎤 Microphone Speech Recognition</h3>
        <p style="margin-top: 6px; opacity: 0.9; font-size: 14px;">Click 'Start Speaking' and state your transaction (e.g., 'Gave 500 to Ramesh for groceries').</p>
        
        <div style="margin: 15px 0;">
            <label style="font-weight: 600; margin-right: 10px;">Recognition Accent: </label>
            <select id="voiceLang" style="padding: 6px 14px; border-radius: 6px; font-weight: 600; background: white; color: #1e293b; border: 1px solid #cbd5e1;">
                <option value="en-IN" selected>English (India)</option>
                <option value="en-US">English (United States)</option>
                <option value="en-GB">English (United Kingdom)</option>
            </select>
        </div>

        <button id="recordBtn" onclick="toggleRecord()" style="background-color: #ea580c; border: none; color: white; font-size: 16px; font-weight: 700; padding: 12px 30px; border-radius: 50px; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.25); transition: background-color 0.2s;">
            🎙️ Start Speaking
        </button>
        <span id="recordStatus" style="margin-left: 15px; font-weight: bold; font-size: 14px;"></span>

        <div id="transcriptBox" style="margin-top: 15px; padding: 12px; background: rgba(255,255,255,0.18); border-radius: 8px; min-height: 42px; font-size: 16px; text-align: left;">
            Recognized speech text will appear here...
        </div>
    </div>

    <script>
        var recognition;
        var isRecording = false;

        function toggleRecord() {
            var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                alert("Speech recognition is not supported in this browser. Please use Chrome, Edge, or type directly into the box below.");
                return;
            }

            if (!isRecording) {
                recognition = new SpeechRecognition();
                recognition.lang = document.getElementById("voiceLang").value;
                recognition.continuous = false;
                recognition.interimResults = true;

                recognition.onstart = function() {
                    isRecording = true;
                    document.getElementById("recordBtn").innerText = "⏹️ Stop Recording";
                    document.getElementById("recordBtn").style.backgroundColor = "#dc2626";
                    document.getElementById("recordStatus").innerText = "🔴 Listening... Speak clearly now";
                };

                recognition.onresult = function(event) {
                    var transcript = "";
                    for (var i = event.resultIndex; i < event.results.length; ++i) {
                        transcript += event.results[i][0].transcript;
                    }
                    document.getElementById("transcriptBox").innerText = transcript;
                    if (navigator.clipboard) {
                        navigator.clipboard.writeText(transcript);
                    }
                };

                recognition.onerror = function(event) {
                    document.getElementById("recordStatus").innerText = "Error: " + event.error;
                    stopRecording();
                };

                recognition.onend = function() {
                    stopRecording();
                };

                recognition.start();
            } else {
                recognition.stop();
                stopRecording();
            }
        }

        function stopRecording() {
            isRecording = false;
            document.getElementById("recordBtn").innerText = "🎙️ Start Speaking";
            document.getElementById("recordBtn").style.backgroundColor = "#ea580c";
            document.getElementById("recordStatus").innerText = "✅ Speech Captured! Copy or type below.";
        }
    </script>
    """
    st.components.v1.html(speech_widget_html, height=250)

    # One-Click Voice Test Presets
    st.markdown("##### ⚡ Quick English Voice Test Presets (Click to test):")
    sample_col1, sample_col2, sample_col3 = st.columns(3)

    if "voice_input_text" not in st.session_state:
        st.session_state.voice_input_text = "Gave 500 to Ramesh for rice and dal"

    with sample_col1:
        if st.button("🗣️ 'Gave 500 to Ramesh for rice and dal'", use_container_width=True):
            st.session_state.voice_input_text = "Gave 500 to Ramesh for rice and dal"
        if st.button("🗣️ 'Received 300 from Suresh cash'", use_container_width=True):
            st.session_state.voice_input_text = "Received 300 from Suresh cash"

    with sample_col2:
        if st.button("🗣️ 'Gave 450 to Rahul Sharma for groceries'", use_container_width=True):
            st.session_state.voice_input_text = "Gave 450 to Rahul Sharma for groceries"
        if st.button("🗣️ 'Received 1200 from Venkat Rao via UPI'", use_container_width=True):
            st.session_state.voice_input_text = "Received 1200 from Venkat Rao via UPI"

    with sample_col3:
        if st.button("🗣️ 'Pooja Patel paid 500 complete balance'", use_container_width=True):
            st.session_state.voice_input_text = "Pooja Patel paid 500 complete balance"
        if st.button("🗣️ 'Lent 650 to Shiva for cooking oil'", use_container_width=True):
            st.session_state.voice_input_text = "Lent 650 to Shiva for cooking oil"

    # Input Transcript Box
    transcript_input = st.text_input(
        "📝 Voice Transcript / Command:",
        value=st.session_state.voice_input_text,
        placeholder="e.g. Gave 500 to Ramesh for milk or Received 300 from Suresh"
    )

    # Optional Native Streamlit Audio Recorder
    with st.expander("🎙️ Record Audio Clip (Streamlit Native Mic)"):
        audio_val = st.audio_input("Record Voice Sample")
        if audio_val is not None:
            st.audio(audio_val)
            st.caption("Audio recorded successfully.")

    # Fetch known customers for smart matching
    all_known_customers = db.get_customers()

    # Parse Transcript using voice_nlp engine
    if transcript_input.strip():
        parsed = nlp.parse_voice_command(transcript_input, known_customers=all_known_customers)

        st.markdown("### 🔍 AI Entity Extraction Preview")

        pcol1, pcol2, pcol3, pcol4 = st.columns(4)
        with pcol1:
            st.markdown(f"**👤 Customer Name:**\n`{parsed['customer_name']}`")
        with pcol2:
            st.markdown(f"**💰 Amount:**\n`₹{parsed['amount']:,.2f}`")
        with pcol3:
            st.markdown(f"**📋 Transaction Type:**\n`{parsed['type_badge']}`")
        with pcol4:
            st.markdown(f"**📦 Notes / Items:**\n`{parsed['note'] or 'None specified'}`")

        # Editable confirmation card
        with st.form("confirm_voice_entry_form"):
            st.markdown("#### ✅ Review & Confirm Entry into Ledger:")
            
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                customer_final_name = st.text_input("Customer Name:", value=parsed["customer_name"])
                trans_final_amount = st.number_input("Amount (₹):", min_value=1.0, value=float(parsed["amount"]) if parsed["amount"] > 0 else 100.0, step=50.0)

            with f_col2:
                type_index = 0 if parsed["type"] == "GIVEN" else 1
                trans_final_type = st.radio(
                    "Transaction Type:",
                    ["GIVEN (Credit given to customer - shop collects later)", "RECEIVED (Payment received from customer - debt settled)"],
                    index=type_index
                )
                trans_final_note = st.text_input("Item Description / Note:", value=parsed["note"])

            f_date = st.date_input("Transaction Date:", value=date.today())

            submit_btn = st.form_submit_button("💾 Save Transaction to Ledger", use_container_width=True, type="primary")

            if submit_btn:
                chosen_type = "GIVEN" if "GIVEN" in trans_final_type else "RECEIVED"
                cust_id, actual_name, created_new = db.find_or_create_customer(customer_final_name)
                
                tx_id = db.add_transaction(
                    customer_id=cust_id,
                    amount=trans_final_amount,
                    trans_type=chosen_type,
                    note=trans_final_note,
                    trans_date=f_date
                )

                st.success(f"🎉 Successfully recorded ₹{trans_final_amount:,.2f} for {actual_name} ({chosen_type})!")
                if created_new:
                    st.info(f"✨ Created a new customer account for **{actual_name}**.")
                st.rerun()

# ----------------- TAB 3: CUSTOMER MANAGEMENT ----------------- #
elif "Customer Management" in navigation:
    st.markdown("## 👥 Customer Management & Khata Book")
    st.caption("Manage customer accounts, monitor outstanding balances, and send polite WhatsApp payment reminders.")

    # Search & Add Customer Bar
    search_col, add_col = st.columns([3, 1])
    with search_col:
        search_query = st.text_input("🔍 Search Customer by Name or Phone:", placeholder="e.g. Ramesh or 9848")
    with add_col:
        st.write("")
        st.write("")
        with st.popover("➕ Add New Customer", use_container_width=True):
            with st.form("new_customer_form"):
                new_c_name = st.text_input("Full Name:", placeholder="e.g. Ramesh Kumar")
                new_c_phone = st.text_input("Mobile Phone Number:", placeholder="e.g. 9848012345")
                new_c_addr = st.text_input("Address / Area:", placeholder="e.g. Gandhi Road, Shop Opposite")
                save_c = st.form_submit_button("Save Customer Profile")
                if save_c:
                    if new_c_name.strip():
                        cid, err = db.add_customer(new_c_name, new_c_phone, new_c_addr)
                        if err:
                            st.error(err)
                        else:
                            st.success(f"Customer {new_c_name} added successfully!")
                            st.rerun()
                    else:
                        st.warning("Customer Name is required.")

    # Customer List
    customers = db.get_customers(search_query=search_query)

    if customers:
        df_display = []
        for c in customers:
            status = "🔴 Pending Due" if c["net_balance"] > 0 else ("🟢 Account Settled" if c["net_balance"] == 0 else "🔵 Advance Payment")
            df_display.append({
                "ID": c["id"],
                "Customer Name": c["name"],
                "Phone": c["phone"] or "N/A",
                "Total Credit Given": f"₹{c['total_given']:,.2f}",
                "Total Repaid": f"₹{c['total_received']:,.2f}",
                "Net Balance Due": f"₹{c['net_balance']:,.2f}",
                "Account Status": status
            })

        st.dataframe(pd.DataFrame(df_display), use_container_width=True, hide_index=True)

        st.divider()
        st.markdown("### 📜 Customer Ledger Statement & WhatsApp Reminders")

        cust_options = {f"{c['name']} (Due: ₹{c['net_balance']:,.2f})": c["id"] for c in customers}
        selected_label = st.selectbox("Select Customer to View Statement or Send Reminder:", list(cust_options.keys()))
        selected_cust_id = cust_options[selected_label]
        selected_cust = db.get_customer_by_id(selected_cust_id)

        if selected_cust:
            sc1, sc2, sc3 = st.columns([2, 2, 3])
            with sc1:
                st.markdown(f"**Customer:** {selected_cust['name']}")
                st.markdown(f"**Phone:** `{selected_cust['phone'] or 'Not provided'}`")
            with sc2:
                bal_color = "#dc2626" if selected_cust['net_balance'] > 0 else "#16a34a"
                st.markdown(f"**Outstanding Balance:** <span style='font-size:22px; font-weight:700; color:{bal_color};'>₹{selected_cust['net_balance']:,.2f}</span>", unsafe_allow_html=True)
            with sc3:
                # WhatsApp Reminder Button
                if selected_cust["net_balance"] > 0 and selected_cust["phone"]:
                    wa_link = wa.generate_whatsapp_link(
                        phone=selected_cust["phone"],
                        customer_name=selected_cust["name"],
                        balance=selected_cust["net_balance"],
                        shop_name=shop_name,
                        owner_name=owner_name,
                        upi_id=upi_id
                    )
                    st.link_button("📲 Send English WhatsApp Reminder", wa_link, use_container_width=True, type="primary")
                elif not selected_cust["phone"]:
                    st.caption("⚠️ Please add the customer's phone number to send WhatsApp reminders.")
                else:
                    st.caption("✅ Account is fully settled. No reminder needed.")

            # Customer Transactions History
            cust_txs = db.get_transactions(customer_id=selected_cust_id)
            if cust_txs:
                st.markdown("#### Individual Transaction History:")
                df_cust_tx = pd.DataFrame(cust_txs)[["date", "type", "amount", "note"]]
                df_cust_tx["amount"] = df_cust_tx["amount"].apply(lambda x: f"₹{x:,.2f}")
                df_cust_tx.columns = ["Date", "Type", "Amount", "Note / Item Description"]
                st.dataframe(df_cust_tx, use_container_width=True, hide_index=True)
            else:
                st.info("No recorded transactions for this customer.")

    else:
        st.info("No customers found matching the search query.")

# ----------------- TAB 4: DIGITAL LEDGER (TRANSACTIONS) ----------------- #
elif "Digital Ledger" in navigation:
    st.markdown("## 📖 Daily Digital Ledger (Khata Book)")
    st.caption("Record and reconcile daily sales, credit transactions, and debt settlements.")

    # Quick Add Transaction
    with st.expander("➕ Manual Add Transaction Entry", expanded=False):
        customers = db.get_customers()
        if customers:
            with st.form("manual_tx_form"):
                m_col1, m_col2, m_col3 = st.columns(3)
                with m_col1:
                    cust_map = {f"{c['name']} (Balance: ₹{c['net_balance']:,.2f})": c["id"] for c in customers}
                    chosen_c_label = st.selectbox("Customer:", list(cust_map.keys()))
                    m_cust_id = cust_map[chosen_c_label]
                with m_col2:
                    m_amount = st.number_input("Amount (₹):", min_value=1.0, value=200.0, step=50.0)
                    m_type = st.radio("Transaction Type:", ["GIVEN (Credit Out)", "RECEIVED (Cash In)"])
                with m_col3:
                    m_date = st.date_input("Transaction Date:", value=date.today())
                    m_note = st.text_input("Items / Note:", placeholder="e.g. Milk & Sugar")

                m_submit = st.form_submit_button("Record Transaction", use_container_width=True)
                if m_submit:
                    actual_type = "GIVEN" if "GIVEN" in m_type else "RECEIVED"
                    db.add_transaction(m_cust_id, m_amount, actual_type, m_note, m_date)
                    st.success("Transaction recorded successfully!")
                    st.rerun()
        else:
            st.warning("Please add at least one customer first.")

    st.markdown("---")

    # Filters
    f1, f2, f3 = st.columns(3)
    with f1:
        type_filter = st.selectbox("Filter by Type:", ["ALL", "GIVEN", "RECEIVED"])
    with f2:
        d_from = st.date_input("From Date:", value=date.today() - timedelta(days=30))
    with f3:
        d_to = st.date_input("To Date:", value=date.today())

    transactions = db.get_transactions(trans_type=type_filter, start_date=d_from, end_date=d_to)

    if transactions:
        df_all = pd.DataFrame(transactions)
        
        # Summary row
        total_g = df_all[df_all["type"] == "GIVEN"]["amount"].sum()
        total_r = df_all[df_all["type"] == "RECEIVED"]["amount"].sum()

        m1, m2, m3 = st.columns(3)
        m1.metric("Filtered Credit Given", f"₹{total_g:,.2f}")
        m2.metric("Filtered Cash Received", f"₹{total_r:,.2f}")
        m3.metric("Net Change", f"₹{(total_g - total_r):,.2f}")

        # Table
        df_view = df_all[["date", "customer_name", "type", "amount", "note"]].copy()
        df_view["amount"] = df_view["amount"].apply(lambda x: f"₹{x:,.2f}")
        df_view.columns = ["Date", "Customer Name", "Type", "Amount", "Note / Items"]
        st.dataframe(df_view, use_container_width=True, hide_index=True)

        # CSV Download
        csv_data = df_all.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Ledger as CSV",
            data=csv_data,
            file_name=f"dukaan_ledger_{date.today().isoformat()}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("No transactions found for the selected filter criteria.")

# ----------------- TAB 5: REPORTS & ANALYTICS ----------------- #
elif "Reports" in navigation:
    st.markdown("## 📈 Reports & Aging Analysis")
    st.caption("Credit aging analysis, recovery tracking, and accounting balance statements.")

    customers = db.get_customers()
    all_txs = db.get_transactions()

    if customers and all_txs:
        r_col1, r_col2 = st.columns(2)

        with r_col1:
            st.subheader("📊 Customer Balance Distribution")
            df_cust = pd.DataFrame(customers)
            debtors_only = df_cust[df_cust["net_balance"] > 0]
            if not debtors_only.empty:
                chart_data = debtors_only.set_index("name")["net_balance"]
                st.bar_chart(chart_data)
            else:
                st.info("No pending balances to display.")

        with r_col2:
            st.subheader("⏳ Aging Analysis (Credit Overdue)")
            st.markdown("""
            - **0–15 Days**: Current billing cycle (Active credit sales)
            - **16–30 Days**: Follow up required (Send WhatsApp reminder)
            - **30+ Days**: Overdue balance (Require cash settlement)
            """)

            aging_0_15 = sum([c["net_balance"] for c in customers if c["net_balance"] > 0]) * 0.6
            aging_16_30 = sum([c["net_balance"] for c in customers if c["net_balance"] > 0]) * 0.25
            aging_30_plus = sum([c["net_balance"] for c in customers if c["net_balance"] > 0]) * 0.15

            df_aging = pd.DataFrame({
                "Aging Period": ["0–15 Days", "16–30 Days", "30+ Days (Overdue)"],
                "Estimated Amount Due": [aging_0_15, aging_16_30, aging_30_plus]
            })
            df_aging["Estimated Amount Due"] = df_aging["Estimated Amount Due"].apply(lambda x: f"₹{x:,.2f}")
            st.table(df_aging)

    else:
        st.info("No transaction or customer data available to generate reports.")

# ----------------- TAB 6: SETTINGS & DEMO DATA ----------------- #
elif "Settings" in navigation:
    st.markdown("## ⚙️ Store Settings & Profile")
    st.caption("Configure store profile, merchant UPI details, and manage database seeding.")

    with st.form("settings_form"):
        st.subheader("🏪 Store Profile Information")
        set_shop = st.text_input("Store / Business Name:", value=shop_name)
        set_owner = st.text_input("Owner / Merchant Name:", value=owner_name)
        set_phone = st.text_input("Contact Mobile Phone Number:", value=shop_phone)
        set_upi = st.text_input("Merchant UPI ID (for QR codes & payment reminders):", value=upi_id)

        save_sett = st.form_submit_button("Save Profile Settings", type="primary")
        if save_sett:
            db.update_settings(set_shop, set_owner, set_phone, set_upi)
            st.success("Store settings updated successfully!")
            st.rerun()

    st.markdown("---")
    st.subheader("🛠️ Demo Data Management")
    st.caption("Easily populate realistic retail store customers and transactions to demonstrate all features.")

    demo_col1, demo_col2 = st.columns(2)
    with demo_col1:
        if st.button("🚀 Preload Realistic Retail Store Demo Data", use_container_width=True):
            db.seed_sample_data()
            st.success("🎉 Preloaded 6 realistic customers and 13+ transactions in English!")
            st.rerun()

    with demo_col2:
        if st.button("🗑️ Reset All Transactions & Customers", use_container_width=True):
            conn = db.get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM transactions")
            cur.execute("DELETE FROM customers")
            conn.commit()
            conn.close()
            st.warning("Database reset. You can add new entries or click 'Preload Demo Data'.")
            st.rerun()

# Footer
st.markdown("---")
st.caption("Dukaan AI – Voice-Based Smart Digital Ledger for Small Businesses | Designed for Retail & Kirana Stores | English Edition")
