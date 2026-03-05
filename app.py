# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import time
import plotly.express as px


tab1, tab2, tab3, tab4 = st.tabs(["Revenue","AOV","Revenue per Driver","Driver Top-Ups"])

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
        color_discrete_map={
            'Pochta': 'yellow',   # birinchi service type sariq
            'Yolovchi': '#1f77b4'      # ikkinchi service type ko‘k
        },
        barmode='stack',
        labels={'created_date_only':'Date','revenue':'Revenue','service_type':'Service Type'},
        title="Daily Revenue by Service Type",
        text=df_grouped['revenue'].apply(lambda x: f"{x:,.0f}")
    )

    fig.update_traces(textposition='inside')
    fig.update_layout(yaxis_tickformat=',')  # y-axis financial format
    st.plotly_chart(fig, use_container_width=True)

    #### WEEKLY STATISTICS#####

    df_filtered['weekday'] = df_filtered['created_date_only'].apply(lambda x: x.strftime('%A'))
    df_filtered['revenue'] = df_filtered['revenue']

    # Hafta kunlari bo'yicha o'rtacha
    # 1️⃣ Haftaning kunini aniqlash
    df_filtered['weekday'] = df_filtered['created_date'].dt.day_name()  # English weekdays

    # 2️⃣ Haftaning kunlari bo'yicha AOV ni hisoblash
    weekday_rev = df_filtered.groupby('weekday', as_index=False).agg({'revenue':'mean'})

    # 3️⃣ KPI ko'rinishida chiqarish
    st.subheader("Average Revenue by Weekdays")

    # Hafta kunlarini tartiblab olish (Monday -> Sunday)
    weekday_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    weekday_rev['weekday'] = pd.Categorical(weekday_rev['weekday'], categories=weekday_order, ordered=True)
    weekday_rev = weekday_rev.sort_values('weekday')

    # 4️⃣ Bar chart chizish
    fig = px.bar(
        weekday_rev,
        x='weekday',
        y='revenue',
        labels={'weekday':'Day of Week','AOV':'Average Order Value'},
        title='Average revenue by Weekdays',
        text=weekday_rev['revenue'].apply(lambda x: f"{x:,.0f}")
    )

    # Textni bar ichida ko‘rsatish
    fig.update_traces(textposition='inside')  

    # Y-axis formatini chiroyli qilish
    fig.update_layout(
        yaxis_tickformat=',',
        xaxis_tickangle=-45,      # hafta kunlarini diagonal qilib yozish
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )

    st.plotly_chart(fig, use_container_width=True)

    #### STATISTICS BY MONTH ##### 

    # Oy + yil ustunini yaratish
    df_filtered['month_year'] = pd.to_datetime(df_filtered['created_date_only']).dt.strftime('%b %Y')  # Jan 2025

    # Oylar va yil bo'yicha revenue ni hisoblash
    monthly_rev = df_filtered.groupby('month_year', as_index=False).agg({'revenue':'sum'})

    # Oylarni tartiblash (datetime qilib)
    monthly_rev['month_year_dt'] = pd.to_datetime(monthly_rev['month_year'], format='%b %Y')
    monthly_rev = monthly_rev.sort_values('month_year_dt')

    # Bar chart chizish
    fig = px.bar(
        monthly_rev,
        x='month_year',
        y='revenue',
        labels={'month_year':'Month & Year','revenue':'Revenue'},
        title='Monthly Revenue by Year',
        color_discrete_sequence=['#1f77b4'],
        text=monthly_rev['revenue'].apply(lambda x: f"{x:,.0f}")
    )

    fig.update_traces(textposition='inside')
    fig.update_layout(
        yaxis_tickformat=',',
        xaxis_tickangle=-45,
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )

    st.plotly_chart(fig, use_container_width=True)

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
        x=-0.1, y=-0.25,  # paper coordinates: x=0 (chap), y=-0.15 (tagi)
        showarrow=False,
        text="Average Order Value = Daily Revenue / Daily Orders Count",
        font=dict(size=12, color="grey")
    )

    st.plotly_chart(fig, use_container_width=True)

    #### Weekly Statistics #######

    aov_df_filtered['weekday'] = aov_df_filtered['created_date_only'].apply(lambda x: x.strftime('%A'))
    aov_df_filtered['aov'] = aov_df_filtered['AOV']

    # Hafta kunlari bo'yicha o'rtacha
    # 1️⃣ Haftaning kunini aniqlash
    aov_df_filtered['weekday'] = aov_df_filtered['created_date'].dt.day_name()  # English weekdays

    # 2️⃣ Haftaning kunlari bo'yicha AOV ni hisoblash
    weekday_aov = aov_df_filtered.groupby('weekday', as_index=False).agg({'AOV':'mean'})

    # 3️⃣ KPI ko'rinishida chiqarish
    st.subheader("*Average Order Value by Weekday")

    # Hafta kunlarini tartiblab olish (Monday -> Sunday)
    weekday_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    weekday_aov['weekday'] = pd.Categorical(weekday_aov['weekday'], categories=weekday_order, ordered=True)
    weekday_aov = weekday_aov.sort_values('weekday')

    # 4️⃣ Bar chart chizish
    fig = px.bar(
        weekday_aov,
        x='weekday',
        y='AOV',
        labels={'weekday':'Day of Week','AOV':'Average Order Value'},
        title='Average Order Value by Weekday',
        text=weekday_aov['AOV'].apply(lambda x: f"{x:,.0f}")
    )

    # Textni bar ichida ko‘rsatish
    fig.update_traces(textposition='inside')  

    # Y-axis formatini chiroyli qilish
    fig.update_layout(
        yaxis_tickformat=',',
        xaxis_tickangle=-45,      # hafta kunlarini diagonal qilib yozish
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )

    st.plotly_chart(fig, use_container_width=True)
    
    st.write(aov_df_filtered.tail())

with tab3:
    st.title("Revenue per Driver")
    
    # 1️⃣ Google Sheet URL
    url = f"https://docs.google.com/spreadsheets/d/1C10Y4jSIJKcP-LnUzhh07Fuiwyr9aHUX/export?format=csv&gid=1164044928&t={time.time()}"
    rpd_df = pd.read_csv(url,sep=",")

    # 2️⃣ Date ustunini to'g'rilash
    rpd_df['created_date'] = pd.to_datetime(rpd_df['clean_date'], errors='coerce')  # clean_date mavjud deb faraz qilamiz
    rpd_df['created_date_only'] = rpd_df['created_date'].dt.date

    # 3️⃣ Noto‘g‘ri sanalarni olib tashlash
    rpd_df = rpd_df[rpd_df['created_date_only'].notna()]

    # 4️⃣ Slider uchun min va max date
    start_date = rpd_df['created_date_only'].min()
    end_date = rpd_df['created_date_only'].max()
    selected_start, selected_end = st.slider(
        "Select Date Range",
        min_value=start_date,
        max_value=end_date,
        value=(start_date, end_date)
    )

    # 5️⃣ Data filterlash
    rpd_df_filtered = rpd_df[(rpd_df['created_date_only'] >= selected_start) &
                             (rpd_df['created_date_only'] <= selected_end)]
    # Agar rpd ustuni hali ham bitta string bo'lsa:
    rpd_df['rpd'] = rpd_df['rpd'].astype(str).str.replace(" ", "").astype(float)
    rpd_df['rpd'] = pd.to_numeric(rpd_df['rpd'], errors='coerce')
    # 6️⃣ KPI hisoblash
    col1, col2, col3 = st.columns(3)

    if 'rpd' in rpd_df_filtered.columns and not rpd_df_filtered.empty:
        rpd_avg = rpd_df_filtered['rpd'].mean()
        rpd_min = rpd_df_filtered['rpd'].min()
        rpd_max = rpd_df_filtered['rpd'].max()
    else:
        rpd_avg = rpd_min = rpd_max = 0  # bo‘sh bo‘lsa 0 chiqadi

    with col1:
        st.metric("Average RPD", f"{rpd_avg:,.0f} UZS")
    with col2:
        st.metric("Minimum RPD", f"{rpd_min:,.0f} UZS")
    with col3:
        st.metric("Maximum RPD", f"{rpd_max:,.0f} UZS")

    rpd_df_grouped = rpd_df_filtered.groupby(['created_date_only'], as_index=False)['rpd'].sum()
    fig = px.bar(
        rpd_df_grouped,
        x='created_date_only',
        y='rpd',  # Revenue Per Driver
        labels={'created_date_only':'Date','rpd':'Revenue Per Driver'},
        title="Revenue Per Driver",
        text=rpd_df_grouped['rpd'].apply(lambda x: f"{x:,.0f}")
    )

    fig.update_traces(textposition='inside')
    fig.update_layout(yaxis_tickformat=',')  # y-axis format

    # Grafik tagida note qo‘shish
    fig.add_annotation(
        xref='paper', yref='paper',
        x=-0.1, y=-0.25,  # paper coordinates: x=0 (chap), y=-0.15 (tagi)
        showarrow=False,
        text="Revenue / Active Drivers",
        font=dict(size=12, color="grey")
    )

    st.plotly_chart(fig, use_container_width=True)
    

    # 7️⃣ Filterlangan DataFrame ni ko‘rsatish
    st.subheader("Filtered Data Preview")
    st.write(rpd_df_filtered.tail())

with tab4:
    st.title("Driver Top-Ups Statistic")
    
    # 1️⃣ Google Sheet URL
    url = f"https://docs.google.com/spreadsheets/d/1Xa1cxYF0Zp3dLq04T5MmbzHpqZpiFqZW/export?format=csv&gid=1401524925&t={time.time()}"
    dt_df = pd.read_csv(url,sep=",")

    # 2️⃣ Date ustunini to'g'rilash
    dt_df['created_date'] = pd.to_datetime(dt_df['clean_date'], errors='coerce')  # clean_date mavjud deb faraz qilamiz
    dt_df['created_date_only'] = dt_df['created_date'].dt.date

    # 3️⃣ Noto‘g‘ri sanalarni olib tashlash
    dt_df = dt_df[dt_df['created_date_only'].notna()]

    # 4️⃣ Slider uchun min va max date
    start_date = dt_df['created_date_only'].min()
    end_date = dt_df['created_date_only'].max()
    selected_start, selected_end = st.slider(
        "Select Date Range",
        min_value=start_date,
        max_value=end_date,
        value=(start_date, end_date)
    )
       # 5️⃣ Data filterlash
    dt_df_filtered = dt_df[(dt_df['created_date_only'] >= selected_start) &
                             (dt_df['created_date_only'] <= selected_end)]
    # Agar rpd ustuni hali ham bitta string bo'lsa:
    dt_df['total_value'] = dt_df['total_value'].astype(str).str.replace(" ", "").astype(float)
    dt_df['total_value'] = pd.to_numeric(dt_df['total_value'], errors='coerce')
    # 6️⃣ KPI hisoblash
    col1, col2, col3 = st.columns(3)

    if 'total_value' in dt_df_filtered.columns and not dt_df_filtered.empty:
        dt_avg = dt_df_filtered['total_value'].mean()
        dt_min = dt_df_filtered['total_value'].min()
        dt_max = dt_df_filtered['total_value'].max()
    else:
        dt_avg = dt_min = dt_max = 0  # bo‘sh bo‘lsa 0 chiqadi

    with col1:
        st.metric("Average rt", f"{dt_avg:,.0f} UZS")
    with col2:
        st.metric("Minimum rt", f"{dt_min:,.0f} UZS")
    with col3:
        st.metric("Maximum rt", f"{dt_max:,.0f} UZS")

    dt_df_grouped = dt_df_filtered.groupby(['created_date_only'], as_index=False)['total_value'].sum()
    fig = px.bar(
        dt_df_grouped,
        x='created_date_only',
        y='total_value',  # Revenue Per Driver
        labels={'created_date_only':'Date','total_value':'Revenue Per Driver'},
        title="Revenue Per Driver",
        text=dt_df_grouped['total_value'].apply(lambda x: f"{x:,.0f}")
    )

    fig.update_traces(textposition='inside')
    fig.update_layout(yaxis_tickformat=',')  # y-axis format

    # Grafik tagida note qo‘shish
    fig.add_annotation(
        xref='paper', yref='paper',
        x=-0.1, y=-0.25,  # paper coordinates: x=0 (chap), y=-0.15 (tagi)
        showarrow=False,
        text="Revenue / Active Drivers",
        font=dict(size=12, color="grey")
    )

    st.plotly_chart(fig, use_container_width=True)
    

    # 7️⃣ Filterlangan DataFrame ni ko‘rsatish
    st.subheader("Filtered Data Preview")

        #### Weekly Statistics #######

    dt_df_filtered['weekday'] = dt_df_filtered['created_date_only'].apply(lambda x: x.strftime('%A'))
    dt_df_filtered['total_value'] = dt_df_filtered['total_value']

    # Hafta kunlari bo'yicha o'rtacha
    # 1️⃣ Haftaning kunini aniqlash
    dt_df_filtered['weekday'] = dt_df_filtered['created_date'].dt.day_name()  # English weekdays

    # 2️⃣ Haftaning kunlari bo'yicha AOV ni hisoblash
    weekday_dt = dt_df_filtered.groupby('weekday', as_index=False).agg({'total_value':'mean'})

    # 3️⃣ KPI ko'rinishida chiqarish
    st.subheader("Average Driver Top-Ups by weekdays")

    # Hafta kunlarini tartiblab olish (Monday -> Sunday)
    weekday_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    weekday_dt['weekday'] = pd.Categorical(weekday_dt['weekday'], categories=weekday_order, ordered=True)
    weekday_dt = weekday_dt.sort_values('weekday')

    # 4️⃣ Bar chart chizish
    fig = px.bar(
        weekday_dt,
        x='weekday',
        y='total_value',
        labels={'weekday':'Day of Week','total_value':'Average Top-Up'},
        title='Average Order Value by Weekday',
        text=weekday_dt['total_value'].apply(lambda x: f"{x:,.0f}")
    )

    # Textni bar ichida ko‘rsatish
    fig.update_traces(textposition='inside')  

    # Y-axis formatini chiroyli qilish
    fig.update_layout(
        yaxis_tickformat=',',
        xaxis_tickangle=-45,      # hafta kunlarini diagonal qilib yozish
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )

    st.plotly_chart(fig, use_container_width=True)

    st.write(rpd_df_filtered.tail())