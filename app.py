import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px

# =============================
# DATABASE
# =============================
conn = sqlite3.connect('database.db', check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS inventory (
    date TEXT,
    product TEXT,
    expiry TEXT,
    qty REAL,
    location TEXT,
    aging REAL
)
''')

# =============================
# LOGIN
# =============================
def login():
    st.sidebar.title("🔐 Login")
    user = st.sidebar.text_input("User")
    pwd = st.sidebar.text_input("Password", type="password")

    if user == "admin" and pwd == "123":
        return True
    else:
        return False

if not login():
    st.stop()

st.title("📊 CJ LOGISTICS WMS DASHBOARD")

# =============================
# UPLOAD
# =============================
st.sidebar.header("📤 Upload Data")

file = st.sidebar.file_uploader("Upload Inventory File", type=["xlsx"])
date = st.sidebar.date_input("Select Date")

if file:
    df = pd.read_excel(file)

    for _, row in df.iterrows():
        c.execute("INSERT INTO inventory VALUES (?,?,?,?,?,?)",
                  (str(date),
                   row['PRODUCT CODE'],
                   str(row['EXPIRY DATE']),
                   row['QTY'],
                   row['LOCATION DESC'],
                   row['% of Aging']))

    conn.commit()
    st.success("✅ Data saved!")

# =============================
# LOAD DATA
# =============================
df = pd.read_sql("SELECT * FROM inventory", conn)

if not df.empty:

    # =============================
    # FILTER
    # =============================
    dates = df['date'].unique()
    selected_date = st.selectbox("Select Date", dates)

    data = df[df['date'] == selected_date]

    # =============================
    # SLOB
    # =============================
    data['SLOB'] = data['aging'].apply(lambda x: 'SLOB' if x < 70 else 'NORMAL')

    # =============================
    # KPI
    # =============================
    col1, col2 = st.columns(2)

    col1.metric("Inventory", int(data['qty'].sum()))
    col2.metric("SKU", data['product'].nunique())

    # =============================
    # STATUS
    # =============================
    status = data.groupby('location')['qty'].sum().reset_index()

    fig1 = px.pie(status, names='location', values='qty')
    st.plotly_chart(fig1, use_container_width=True)

    # =============================
    # SLOB
    # =============================
    slob = data.groupby('SLOB')['qty'].sum().reset_index()

    fig2 = px.pie(slob, names='SLOB', values='qty',
                  color_discrete_map={'SLOB':'red','NORMAL':'blue'})
    st.plotly_chart(fig2, use_container_width=True)

    # =============================
    # HISTORY TREND
    # =============================
    trend = df.groupby('date')['qty'].sum().reset_index()

    fig3 = px.line(trend, x='date', y='qty', title="Inventory Trend")
    st.plotly_chart(fig3, use_container_width=True)

    # =============================
    # TABLE
    # =============================
    st.dataframe(data.head(100))

else:
    st.info("Chưa có dữ liệu")