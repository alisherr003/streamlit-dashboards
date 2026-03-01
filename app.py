# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import time
import plotly.express as px


tab1, tab2 = st.tabs(["Revenue","AOV"])

with tab1:
    st.title("Revenue Dashboard")

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
        "Revenue Date Range",
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

with tab2:
    st.title("Average Order Value")
    
    url = f"https://docs.google.com/spreadsheets/d/1QuKlD80GdgBF2Seto7bj4Xm2WoOaMEeH/export?format=csv&gid=285760237&t={time.time()}"
    aov_df = pd.read_csv(url)

    # 1️⃣ to'g'ri DataFrame ustuni bilan ishlash
    aov_df['created_date'] = pd.to_datetime(aov_df['clean_date'], errors='coerce')  # clean_date ustuni bor deb faraz qilamiz
    aov_df['created_date_only'] = aov_df['created_date'].dt.date

    # 2️⃣ Noto‘g‘ri sanalarni olib tashlash
    aov_df = aov_df[aov_df['created_date_only'].notna()]

    # 3️⃣ Slider uchun min va max date
    start_date = aov_df['created_date_only'].min()
    end_date = aov_df['created_date_only'].max()
    selected_start, selected_end = st.slider(
        "AOV Date Range",
        min_value=start_date,
        max_value=end_date,
        value=(start_date, end_date)
    )

    # 4️⃣ Data filterlash
    aov_df_filtered = aov_df[(aov_df['created_date_only'] >= selected_start) &
                         (aov_df['created_date_only'] <= selected_end)]

    # 🔹 KPIs
    col1, col2, col3 = st.columns(3)
    with col1:
        aov = aov_df_filtered['AOV'].mean()
        st.metric("Average Order Value", f"{aov:,.0f} UZS")
    with col2:
        aov_min = aov_df_filtered['AOV'].min()
        st.metric("Minimum AOV", f"{aov_min:,.0f} UZS")
    with col3:
        aov_max = aov_df_filtered['AOV'].max()
        st.metric("Maximum AOV", f"{aov_max:,.0f} UZS")


    aov_df_grouped = aov_df_filtered.groupby(['created_date_only'], as_index=False)['AOV'].sum()
    fig = px.bar(
        aov_df_grouped,
        x='created_date_only',
        y='AOV',  # Average Order Value ustuni
        labels={'created_date_only':'Date','AOV':'Average Order Value'},
        title="Average Order Value by Date",
        text=aov_df_grouped['AOV'].apply(lambda x: f"{x:,.0f}")
    )

    fig.update_traces(textposition='inside')
    fig.update_layout(yaxis_tickformat=',')  # y-axis format

    # Grafik tagida note qo‘shish
    fig.add_annotation(
        xref='paper', yref='paper',
        x=0, y=-0.15,  # paper coordinates: x=0 (chap), y=-0.15 (tagi)
        showarrow=False,
        text="Average Order Value = Daily Revenue / Daily Orders Count",
        font=dict(size=12, color="grey")
    )

    st.plotly_chart(fig, use_container_width=True)

    aov_df_filtered['weekday'] = aov_df_filtered['created_date_only'].apply(lambda x: x.strftime('%A'))
    aov_df_filtered['aov'] = aov_df_filtered['AOV']

    # Hafta kunlari bo'yicha o'rtacha
    weekday_aov = aov_df_filtered.groupby('weekday', as_index=False)['AOV'].mean()

    weekday_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    weekday_aov['weekday'] = pd.Categorical(weekday_aov['weekday'], categories=weekday_order, ordered=True)
    weekday_aov = weekday_aov.sort_values('weekday')

    fig = px.bar(
    weekday_aov,
    x='weekday',
    y='aov',
    labels={'weekday':'Day of Week','aov':'Average Order Value'},
    title='Average Order Value by Weekday',
    text=weekday_aov['AOV'].apply(lambda x: f"{x:,.0f}")
    )
    fig.update_traces(textposition='inside')
    fig.update_layout(yaxis_tickformat=',')
    st.plotly_chart(fig, use_container_width=True)
    
    st.write(aov_df_filtered.tail())
