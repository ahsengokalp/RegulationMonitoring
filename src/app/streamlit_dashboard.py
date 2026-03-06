from __future__ import annotations

import streamlit as st
from src.db.storage import get_latest_items


st.set_page_config(page_title="Regulation Monitor - Latest Items", layout="wide")

st.title("En Son Çekilen Başlıklar")

count = st.sidebar.number_input("Gösterilecek satır", min_value=1, max_value=500, value=100)
refresh = st.sidebar.button("Yenile")

def load_items(limit: int):
    return get_latest_items(limit)


items = load_items(count)

st.write(f"Toplam kayıt: {len(items)}")

for row in items:
    run_date = row.get("run_date")
    title = row.get("title")
    url = row.get("url")
    section = row.get("section")
    subsection = row.get("subsection")
    with st.expander(f"{title} — {run_date}"):
        st.write(f"URL: {url}")
        st.write(f"Bölüm: {section} — Alt: {subsection}")
