import streamlit as st
import pandas as pd
import os
import re

st.set_page_config(page_title="BFSI Call Dashboard", layout="wide")

st.title("📞 BFSI Gold Loan Call Dashboard")
st.markdown("View live call transcripts and extracted lead data.")

CSV_FILE = "data/calls_data.csv"

if not os.path.exists(CSV_FILE):
    st.warning("No call data found yet. Please make a test call via VAPI.")
else:
    df = pd.read_csv(CSV_FILE)

    if df.empty:
        st.info("CSV found but no call records yet.")
        st.stop()

    # Normalize types
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    df["Interested"] = df["Interested"].astype(str).str.lower().isin(["true", "1", "yes"])
    df["Has Gold"] = df["Has Gold"].astype(str).str.lower().isin(["true", "1", "yes"])
    df["Loan Amount"] = pd.to_numeric(df["Loan Amount"], errors="coerce").fillna(0.0)
    df["Qualification Status"] = df.get("Qualification Status", "Unknown").astype(str)
    df["Status"] = df.get("Status", "Completed").astype(str)
    df["Transcript"] = df.get("Transcript", "").astype(str)
    df["Recording URL"] = df.get("Recording URL", "").astype(str)
    df["Stereo Recording URL"] = df.get("Stereo Recording URL", "").astype(str)
    df["Recording File"] = df.get("Recording File", "").astype(str)
    df["Stereo Recording File"] = df.get("Stereo Recording File", "").astype(str)
    df["Compliance Flag"] = df["Transcript"].str.contains(
        re.compile(r"\b(otp|pan|cvv|pin|aadhaar|aadhar)\b", re.IGNORECASE),
        na=False,
    )

    # Filters
    st.subheader("🔎 Filters")
    f1, f2, f3, f4, f5 = st.columns(5)
    date_range = f1.date_input(
        "Date Range",
        value=(
            df["Timestamp"].min().date() if pd.notnull(df["Timestamp"].min()) else None,
            df["Timestamp"].max().date() if pd.notnull(df["Timestamp"].max()) else None
        ),
    )
    interest_filter = f2.selectbox("Interest", ["All", "Interested", "Not Interested"])
    min_amount = f3.number_input("Minimum Loan Amount", min_value=0, value=0, step=10000)
    qualification_filter = f4.selectbox(
        "Qualification",
        ["All"] + sorted(df["Qualification Status"].dropna().unique().tolist())
    )
    compliance_filter = f5.selectbox("Compliance Keyword", ["All", "Matched", "Not Matched"])

    filtered_df = df.copy()
    if isinstance(date_range, tuple) and len(date_range) == 2 and all(date_range):
        start_dt = pd.to_datetime(date_range[0])
        end_dt = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1)
        filtered_df = filtered_df[
            (filtered_df["Timestamp"] >= start_dt) & (filtered_df["Timestamp"] < end_dt)
        ]

    if interest_filter == "Interested":
        filtered_df = filtered_df[filtered_df["Interested"]]
    elif interest_filter == "Not Interested":
        filtered_df = filtered_df[~filtered_df["Interested"]]

    filtered_df = filtered_df[filtered_df["Loan Amount"] >= min_amount]
    if qualification_filter != "All":
        filtered_df = filtered_df[filtered_df["Qualification Status"] == qualification_filter]
    if compliance_filter == "Matched":
        filtered_df = filtered_df[filtered_df["Compliance Flag"]]
    elif compliance_filter == "Not Matched":
        filtered_df = filtered_df[~filtered_df["Compliance Flag"]]

    # Metrics
    total_calls = len(filtered_df)
    interested_leads = int(filtered_df["Interested"].sum()) if total_calls else 0
    success_rate = round((interested_leads / total_calls) * 100, 2) if total_calls else 0.0
    avg_loan_amount = round(filtered_df["Loan Amount"].mean(), 2) if total_calls else 0.0

    compliance_hits = int(filtered_df["Compliance Flag"].sum()) if total_calls else 0
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Calls", total_calls)
    col2.metric("Interested Leads", interested_leads)
    col3.metric("Success Rate", f"{success_rate}%")
    col4.metric("Avg Loan Amount", f"₹{avg_loan_amount:,.0f}")
    col5.metric("Compliance Keyword Hits", compliance_hits)

    st.markdown("---")

    # Data Table
    st.subheader("📋 Recent Calls")

    display_df = filtered_df.drop(columns=["Transcript"], errors="ignore")
    st.dataframe(display_df, use_container_width=True)

    st.markdown("---")

    # Charts
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Interested vs Not Interested")
        interest_counts = filtered_df["Interested"].map({True: "Interested", False: "Not Interested"}).value_counts()
        st.bar_chart(interest_counts)

    with c2:
        st.subheader("💰 Loan Amount Trend")
        trend_df = filtered_df.dropna(subset=["Timestamp"]).sort_values("Timestamp")
        if not trend_df.empty:
            st.line_chart(trend_df.set_index("Timestamp")["Loan Amount"])
        else:
            st.info("No timestamped records available for trend.")

    st.subheader("✅ Qualification Breakdown")
    qual_counts = filtered_df["Qualification Status"].value_counts()
    if not qual_counts.empty:
        st.bar_chart(qual_counts)

    st.markdown("---")

    # Transcript Viewer
    st.subheader("📝 Call Transcripts")
    call_ids = filtered_df["Call ID"].tolist()
    if call_ids:
        selected_call = st.selectbox("Select Call ID to view transcript:", list(reversed(call_ids)))
        call_row = filtered_df[filtered_df["Call ID"] == selected_call].iloc[0]
        st.info(f"Customer: {call_row['Customer Name']} | Amount: ₹{call_row['Loan Amount']:,.0f}")
        rec_url = str(call_row.get("Recording URL", "")).strip()
        stereo_url = str(call_row.get("Stereo Recording URL", "")).strip()
        if rec_url:
            st.markdown(f"[Recording URL]({rec_url})")
        if stereo_url:
            st.markdown(f"[Stereo Recording URL]({stereo_url})")
        local_rec = str(call_row.get("Recording File", "")).strip()
        local_stereo = str(call_row.get("Stereo Recording File", "")).strip()
        if local_rec:
            st.caption(f"Local mono file: {local_rec}")
            if os.path.exists(local_rec):
                st.audio(local_rec, format="audio/wav")
            else:
                st.warning("Local mono recording file not found on disk.")
        if local_stereo:
            st.caption(f"Local stereo file: {local_stereo}")
            if os.path.exists(local_stereo):
                st.audio(local_stereo, format="audio/wav")
            else:
                st.warning("Local stereo recording file not found on disk.")
        st.text_area("Full Transcript", str(call_row.get("Transcript", "")), height=300)
    else:
        st.info("No records match current filters.")
