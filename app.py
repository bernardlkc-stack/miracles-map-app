import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Miracles Agent Profiling (MAP 1)", page_icon="🧭", layout="wide")

DB = "map.db"

SEGMENTS = ["HDB", "Private Resale", "Landed", "New Launch", "Top Projects", "Referral", "Indus/Comm", "Social Media"]
LEVELS = ["Interest", "Knowledge", "Confidence", "Market", "Investment", "Commitment", "Support", "Income", "Willingness"]

# ---------------- DB helpers ----------------
def conn():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    c = conn()
    cur = c.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS associates(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            mobile TEXT,
            email TEXT,
            manager TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS map1(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            associate_name TEXT NOT NULL,
            data_json TEXT NOT NULL,
            totals_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    c.commit(); c.close()

def upsert_associate(name, mobile="", email="", manager=""):
    c = conn(); cur = c.cursor()
    cur.execute("SELECT id FROM associates WHERE name=?", (name,))
    row = cur.fetchone()
    if row is None:
        cur.execute("INSERT INTO associates(name, mobile, email, manager) VALUES(?,?,?,?)",
                    (name, mobile, email, manager))
    else:
        cur.execute("UPDATE associates SET mobile=?, email=?, manager=? WHERE name=?",
                    (mobile, email, manager, name))
    c.commit(); c.close()

def list_associates():
    c = conn()
    df = pd.read_sql_query("SELECT name, mobile, email, manager FROM associates ORDER BY name", c)
    c.close()
    return df

def save_map1(associate_name, data, totals):
    c = conn(); cur = c.cursor()
    now = datetime.now().isoformat(timespec="seconds")
    cur.execute(
        "INSERT INTO map1(associate_name, data_json, totals_json, created_at) VALUES(?,?,?,?)",
        (associate_name, json.dumps(data), json.dumps(totals), now)
    )
    c.commit(); c.close()

def history_map1(associate_name):
    c = conn()
    df = pd.read_sql_query(
        "SELECT id, associate_name, data_json, totals_json, created_at FROM map1 WHERE associate_name=? ORDER BY created_at DESC",
        c, params=(associate_name,)
    )
    c.close()
    return df

# --------------- UI -----------------
init_db()

st.title("🧭 Miracles Agent Profiling (MAP 1)")
st.caption("Rate each segment (1–8) across the nine levels. Totals and chart update live.")

with st.sidebar:
    st.header("Associate")
    assoc_df = list_associates()
    choices = ["— New —"] + assoc_df["name"].tolist()
    selected = st.selectbox("Select associate", choices)

    if selected == "— New —":
        name = st.text_input("Name*")
        mobile = st.text_input("Mobile")
        email = st.text_input("Email")
        manager = st.text_input("Manager", value="Bernard Lau")
        if st.button("Save Associate"):
            if name.strip():
                upsert_associate(name.strip(), mobile.strip(), email.strip(), manager.strip())
                st.success("Associate saved. Choose from the list to begin scoring.")
                st.rerun()
            else:
                st.error("Name is required.")
    else:
        rec = assoc_df[assoc_df["name"] == selected].iloc[0]
        st.write(f"**Mobile:** {rec['mobile'] or '-'}")
        st.write(f"**Email:** {rec['email'] or '-'}")
        st.write(f"**Manager:** {rec['manager'] or '-'}")
        if st.button("Refresh"):
            st.rerun()

if selected == "— New —":
    st.info("➡️ Add or select an associate from the sidebar to start.")
    st.stop()

st.subheader(f"Scoring Grid — {selected}")
st.markdown("Use 1 (lowest) to 8 (highest). Fill each cell below the segment.")

# Build editable grid: columns by segment
cols = st.columns(len(SEGMENTS), gap="small")
values = {seg: {} for seg in SEGMENTS}
totals = {seg: 0 for seg in SEGMENTS}

# Render header row (segment names)
for i, seg in enumerate(SEGMENTS):
    with cols[i]:
        st.markdown(f"**{seg}**")

# Render level inputs per segment
for lvl in LEVELS:
    row_cols = st.columns(len(SEGMENTS), gap="small")
    for i, seg in enumerate(SEGMENTS):
        with row_cols[i]:
            key = f"{seg}-{lvl}"
            default = 0
            values[seg][lvl] = st.number_input(
                label=lvl if i == 0 else " ",  # show the level label only in first column of each row
                min_value=0, max_value=8, step=1, value=default, key=key
            )

# Totals (below each segment)
tot_cols = st.columns(len(SEGMENTS), gap="small")
for i, seg in enumerate(SEGMENTS):
    seg_total = sum(values[seg][lvl] for lvl in LEVELS)
    totals[seg] = seg_total
    with tot_cols[i]:
        st.markdown(f"**Total: {seg_total}**")

st.markdown("---")

# Pie chart
labels = list(totals.keys())
sizes = [totals[k] for k in labels]

if sum(sizes) > 0:
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.0f%%')
    ax.axis('equal')
    st.pyplot(fig)
else:
    st.info("Enter some scores to see the chart.")

# Instructions
with st.expander("Instructions", expanded=True):
    st.markdown(
        """
1) Start from each level of measurement and rate them across the Segments.  
2) Rate each Segment using a scale **1 to 8**, 1 being lowest and 8 being highest.  
3) Complete the mapping based on your own analysis.  
4) Aim to complete within **10 minutes**.  
5) Do this mapping in the presence of a District Head.
        """
    )

st.markdown("---")
c1, c2, c3 = st.columns([1,1,2])
if c1.button("💾 Save Mapping", type="primary"):
    save_map1(selected, values, totals)
    st.success("Saved! (MAP 1)")
    st.balloons()

if c2.button("📜 View History"):
    df = history_map1(selected)
    if df.empty:
        st.info("No history yet.")
    else:
        # show totals expanded for quick review
        out_rows = []
        for _, r in df.iterrows():
            t = json.loads(r["totals_json"])
            row = {"created_at": r["created_at"], **t}
            out_rows.append(row)
        st.dataframe(pd.DataFrame(out_rows))

with c3:
    df_export = pd.DataFrame([{"Segment": k, "Total": v} for k, v in totals.items()])
    st.download_button("⬇️ Export current totals (CSV)", data=df_export.to_csv(index=False).encode("utf-8"),
                       file_name=f"{selected.replace(' ','_')}_map1_totals.csv", mime="text/csv")
    st.download_button("⬇️ Export current mapping (JSON)", data=json.dumps(values, indent=2).encode("utf-8"),
                       file_name=f"{selected.replace(' ','_')}_map1_values.json", mime="application/json")
