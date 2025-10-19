# app.py
import json
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Miracles MAP App — MAP 1 + MAP 2",
    page_icon="🧭",
    layout="wide",
)

# ─────────────────────────────────────────────
# STYLE
# ─────────────────────────────────────────────
st.markdown("""
<style>
.block-container {padding-top:1rem;padding-bottom:1.5rem;}
.table-header{background:#1E4878;color:#fff;padding:8px 6px;font-weight:700;
 font-size:0.8rem;white-space:nowrap;text-align:center;border-radius:6px;}
.level-bar{background:#eaf2ff;color:#0d47a1;font-weight:700;font-size:0.9rem;
 padding:6px 10px;border:1px solid #cfe0ff;border-radius:6px;text-align:center;}
input[type="text"]{background:#f5f6f8;border:1px solid #ced4da;border-radius:8px;
 height:36px;width:100%;text-align:center;font-size:0.9rem;color:#333;}
.total-bar{background:#1E4878;color:#fff;font-weight:700;padding:6px 10px;
 border-radius:6px;font-size:0.9rem;text-align:center;}
[data-testid="column"]{padding-left:0.25rem;padding-right:0.25rem;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
SEGMENTS = [
    "HDB","Private Resale","Landed","New Launch",
    "Top Projects","Referral","Indus/Comm","Social Media",
]
LEVELS = [
    "Interest","Knowledge","Confidence","Market",
    "Investment","Commitment","Support","Income","Willingness",
]
DATA_PATH = Path("data_store.json")
SEGMENT_COLORS = {
    "HDB": "#1E4878","Private Resale": "#C65D00","Landed": "#B5B5B5",
    "New Launch": "#D9A600","Top Projects": "#2E6BAA",
    "Referral": "#2F8B47","Indus/Comm": "#5B5B5B","Social Media": "#6E4A4A",
}

# abbreviated ACTIVITIES dictionary omitted here for brevity
# paste your full ACTIVITIES mapping from previous version ↓
ACTIVITIES = {...}  # same as before

# ─────────────────────────────────────────────
# DATA STORAGE
# ─────────────────────────────────────────────
@st.cache_resource
def _init_store()->dict:
    if DATA_PATH.exists():
        try:return json.loads(DATA_PATH.read_text(encoding="utf-8"))
        except Exception:return {}
    return {}
def save_store(store:dict):DATA_PATH.write_text(json.dumps(store,indent=2),encoding="utf-8")
STORE=_init_store()
def empty_scores_dict():return {lvl:{seg:"" for seg in SEGMENTS} for lvl in LEVELS}

def sanitize_cell(v:str)->str:
    v=(v or "").strip()
    if not v.isdigit():return""
    n=int(v);return str(n) if 1<=n<=8 else""
def validate_row_unique(row:dict)->dict:
    seen=set();out={}
    for seg,v in row.items():
        vv=sanitize_cell(v)
        if vv and vv in seen:out[seg]=""
        else:
            out[seg]=vv
            if vv:seen.add(vv)
    return out
def compute_totals(scores:dict)->dict:
    totals={seg:0 for seg in SEGMENTS}
    for lvl in LEVELS:
        for seg in SEGMENTS:
            v=scores[lvl][seg]
            if v:totals[seg]+=int(v)
    return totals

# ─────────────────────────────────────────────
# UI — SELECT ASSOCIATE
# ─────────────────────────────────────────────
st.title("🧭 Miracles MAP App — MAP 1 + MAP 2")
associate_names=sorted(STORE.keys())
c1,c2,c3,c4=st.columns([2,3,3,2])
with c1:mode=st.selectbox("Mode",["Select associate","New associate"],index=1 if not associate_names else 0)
with c2:selected=st.selectbox("Existing",["—"]+associate_names,disabled=(mode!="Select associate"))
with c3:entered=st.text_input("Associate name",placeholder="Full name")
with c4:load=st.button("Load / Start")
current=None
if mode=="Select associate" and selected!="—" and load:current=selected
elif mode=="New associate" and entered.strip() and load:current=entered.strip()
if "current" not in st.session_state and current:st.session_state["current"]=current
elif current:st.session_state["current"]=current
if "current" not in st.session_state:st.info("Select or create an associate to begin.");st.stop()
current=st.session_state["current"]
if current not in STORE:
    STORE[current]={"profile":{"name":current,"mobile":"","email":"","manager":""},"scores":empty_scores_dict()}
    save_store(STORE)
profile=STORE[current]["profile"];scores=STORE[current]["scores"]

# ─────────────────────────────────────────────
# DETAILS + PIE
# ─────────────────────────────────────────────
t1,t2=st.columns([1.1,1])
with t1:
    st.subheader("Associate Details")
    x1,x2=st.columns(2)
    with x1:
        profile["name"]=st.text_input("Name",value=profile.get("name",""))
        profile["mobile"]=st.text_input("Mobile",value=profile.get("mobile",""))
    with x2:
        profile["email"]=st.text_input("Email",value=profile.get("email",""))
        profile["manager"]=st.text_input("Manager",value=profile.get("manager",""))
with t2:
    st.subheader("FOCUS SEGMENTATION")
    totals_prev=compute_totals(scores)
    pie_img=None
    if sum(totals_prev.values())>0:
        fig,ax=plt.subplots(figsize=(4,4))
        ax.pie([totals_prev[s] for s in SEGMENTS],labels=SEGMENTS,autopct="%1.0f%%",
               startangle=90,colors=[SEGMENT_COLORS[s] for s in SEGMENTS])
        ax.axis("equal")
        pie_img=BytesIO();plt.savefig(pie_img,format="png",bbox_inches="tight")
        st.pyplot(fig)
    else:st.caption("Totals will appear once you enter scores.")
st.markdown("---")

# ─────────────────────────────────────────────
# MAP 1 GRID
# ─────────────────────────────────────────────
hdr=st.columns([1.2]+[1]*8)
with hdr[0]:st.markdown('<div class="table-header">Level</div>',unsafe_allow_html=True)
for i,s in enumerate(SEGMENTS,start=1):
    with hdr[i]:st.markdown(f'<div class="table-header">{s}</div>',unsafe_allow_html=True)
for lvl in LEVELS:
    r=st.columns([1.2]+[1]*8)
    with r[0]:st.markdown(f'<div class="level-bar">{lvl}</div>',unsafe_allow_html=True)
    row={}; 
    for i,s in enumerate(SEGMENTS,start=1):
        with r[i]:
            k=f"cell::{current}::{lvl}::{s}"
            v=st.text_input(" ",value=scores[lvl][s],key=k,label_visibility="collapsed",max_chars=1,placeholder=" ")
            row[s]=v
    scores[lvl]=validate_row_unique(row)
st.markdown("---")

# totals
totals=compute_totals(scores)
ft=st.columns([1.2]+[1]*8)
with ft[0]:st.markdown('<div class="total-bar">TOTAL</div>',unsafe_allow_html=True)
for i,s in enumerate(SEGMENTS,start=1):
    with ft[i]:st.markdown(f'<div class="total-bar">{totals[s]}</div>',unsafe_allow_html=True)
st.markdown("---")

# ─────────────────────────────────────────────
# MAP 2 RECOMMENDATIONS
# ─────────────────────────────────────────────
st.markdown("## 🎯 MAP 2 — Recommended Activities for Top 3 Segments")
tops=sorted(totals.items(),key=lambda x:x[1],reverse=True)
top3=[s for s,_ in tops[:3]]
if not any(totals.values()):st.info("Fill in MAP 1 to see recommendations.")
else:
    st.write(f"Your Top 3 Focus Segments: **{', '.join(top3)}**")
    cols=st.columns(3)
    for i,s in enumerate(top3):
        with cols[i]:
            color=SEGMENT_COLORS.get(s,"#333")
            st.markdown(
                f"""
                <div style="background:{color};color:white;padding:8px 10px;border-radius:5px;
                font-weight:700;text-align:center;">{s.upper()}</div>
                <div style="border:1px solid #ccc;padding:10px;min-height:300px;">
                <table style="width:100%;font-size:0.85rem;">
                <tr><th align="left">Activities</th><th align="right">Done</th></tr>
                {"".join([f"<tr><td>{a}</td><td align='right'>✓</td></tr>" for a in ACTIVITIES.get(s,[])])}
                </table></div>""",unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PDF EXPORT (WITH MAP 1 TABLE)
# ─────────────────────────────────────────────
if any(totals.values()):
    buf=BytesIO()
    c=canvas.Canvas(buf,pagesize=A4)
    w,h=A4
    c.setFont("Helvetica-Bold",16)
    c.drawString(50,h-50,"Miracles MAP 1 & MAP 2 Report")
    c.setFont("Helvetica",11)
    c.drawString(50,h-70,f"Associate: {profile.get('name','')}")
    c.drawString(50,h-85,f"Manager: {profile.get('manager','')}")
    c.drawString(50,h-100,f"Mobile: {profile.get('mobile','')}")
    c.drawString(50,h-115,f"Email: {profile.get('email','')}")
    if pie_img:c.drawImage(ImageReader(BytesIO(pie_img.getvalue())),350,h-330,width=200,preserveAspectRatio=True,mask='auto')
    c.setFont("Helvetica-Bold",12)
    c.drawString(50,h-145,"MAP 1 Scores Table")
    y=h-160
    c.setFont("Helvetica",9)
    c.setFillColor(colors.black)
    row_height=12
    # header
    c.setFillColor(colors.HexColor("#1E4878"));c.rect(50,y-10,500,row_height,fill=1,stroke=0)
    c.setFillColor(colors.white);c.drawString(55,y-8,"Level")
    for i,s in enumerate(SEGMENTS):
        c.drawString(100+50*i,y-8,s[:10])
    y-=row_height
    # data rows
    c.setFillColor(colors.black)
    for lvl in LEVELS:
        c.drawString(55,y-8,lvl)
        for i,s in enumerate(SEGMENTS):
            v=scores[lvl][s] or ""
            c.drawString(100+50*i,y-8,v)
        y-=row_height
    # totals
    c.setFillColor(colors.HexColor("#1E4878"))
    c.rect(50,y-10,500,row_height,fill=1,stroke=0)
    c.setFillColor(colors.white);c.drawString(55,y-8,"TOTAL")
    for i,s in enumerate(SEGMENTS):
        c.drawString(100+50*i,y-8,str(totals[s]))
    y-=25
    c.setFont("Helvetica-Bold",12)
    c.drawString(50,y,"Top 3 Segments & Recommendations")
    y-=15
    for s in top3:
        r,g,b=[int(sv,16)/255 for sv in [SEGMENT_COLORS[s][1:3],SEGMENT_COLORS[s][3:5],SEGMENT_COLORS[s][5:7]]]
        c.setFillColorRGB(r,g,b);c.rect(50,y-12,120,12,fill=1,stroke=0)
        c.setFillColor(colors.white);c.drawString(55,y-10,s)
        c.setFillColor(colors.black)
        y-=15
        for a in ACTIVITIES[s][:6]:
            c.drawString(70,y,f"• {a}");y-=11
        y-=6
    c.save()
    st.download_button("📄 Download Full Report (PDF)",
        data=buf.getvalue(),file_name=f"{current.replace(' ','_')}_MAP_Report.pdf",
        mime="application/pdf")
