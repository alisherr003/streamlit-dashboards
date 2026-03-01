# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import time

tab1, = st.tabs(["Revenue"])

with tab1:
    st.title("Revenue Dashboards")

    # 🔹 Google Sheet CSV URL (time param – cache bypass)
    url = f"https://docs.google.com/spreadsheets/d/1uX-olx_6RCQ9K5j0_39Fqt-FIKCC8ag6/export?format=csv&gid=573004352&t={time.time()}"

    # 🔹 Funksiya: Google Sheet’dan data olish va tozalash
    def load_data():
        df = pd.read_csv(url)
        df['created_date'] = pd.to_datetime(df['clean_date'], errors='coerce')  # clean_date ustuni
        df['created_date_only'] = df['created_date'].dt.date
        df = df[df['created_date_only'].notna()]
        return df

    # 🔹 Refresh tugmasi
    if st.button("🔄 Refresh Data"):
        st.session_state['df'] = load_data()
        st.success("Data updated from Google Sheet!")

    # 🔹 Dastlabki yuklash
    if 'df' not in st.session_state:
        st.session_state['df'] = load_data()

    df = st.session_state['df']

    # 🔹 Date range slider
    start_date = df['created_date_only'].min()
    end_date = df['created_date_only'].max()
    selected_start, selected_end = st.slider(
        "Select Date Range",
        min_value=start_date,
        max_value=end_date,
        value=(start_date, end_date)
    )
    df_filtered = df[(df['created_date_only'] >= selected_start) & (df['created_date_only'] <= selected_end)]

    # 🔹 Service Type filter (checkboxes)
    service_options = df['service_type'].unique().tolist()
    selected_services = []
    for service in service_options:
        if st.checkbox(service, value=True):
            selected_services.append(service)
    if not selected_services:
        selected_services = service_options
    df_filtered = df_filtered[df_filtered['service_type'].isin(selected_services)]

    # 🔹 KPIs
    col1, col2 = st.columns(2)
    with col1:
        total_revenue = df_filtered['revenue'].sum()
        st.metric("Total Revenue", f"{total_revenue:,.0f} UZS")
    with col2:
        average_revenue = df_filtered['revenue'].mean()
        st.metric("Daily Average Revenue", f"{average_revenue:,.0f} UZS")

    # 🔹 Stacked Bar Chart: Daily Revenue by Service Type
    df_grouped = df_filtered.groupby(['created_date_only', 'service_type'], as_index=False)['revenue'].sum()
    fig = px.bar(
        df_grouped,
        x='created_date_only',
        y='revenue',
        color='service_type',
        barmode='stack',
        labels={'created_date_only':'Date','revenue':'Revenue','service_type':'Service Type'},
        title="Daily Revenue by Service Type",
        text=df_grouped['revenue'].apply(lambda x: f"{x:,.0f}")
    )
    fig.update_traces(textposition='inside')
    fig.update_layout(yaxis_tickformat=',')  # y-axis financial format
    st.plotly_chart(fig, use_container_width=True)

    # 🔹 Oxirgi satrlarni ko‘rsatish
    st.write(df.tail())