
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="Airbnb Analytics Dashboard",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- CUSTOM DESIGN ----------------

st.markdown("""
<style>
.stApp {
    background-color: #F4F7FC;
}
[data-testid="stSidebar"] {
    background-color: #172554;
}
[data-testid="stSidebar"] * {
    color: white !important;
}
h1 {
    color: #172554;
    font-weight: 800;
}
h2, h3 {
    color: #243B64;
}
div[data-testid="stMetric"] {
    background: linear-gradient(135deg,#FFFFFF,#E8F0FF);
    border: 1px solid #D6E3F5;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0px 3px 10px rgba(0,0,0,0.06);
}
div[data-testid="stMetricValue"] {
    color: #2563EB;
    font-weight: bold;
}
div[data-testid="stMetricLabel"] {
    color: #475569;
}
.block-container {
    padding-top: 2rem;
}
</style>
""", unsafe_allow_html=True)


# ---------------- HEADER ----------------

st.title("🏡 Airbnb Data Analytics Dashboard")

st.markdown(
    "### Explore listings, pricing, neighbourhoods and availability"
)

st.markdown("---")


# ---------------- FILE UPLOAD ----------------

st.sidebar.title("📂 Upload Dataset")

uploaded_file = st.sidebar.file_uploader(
    "Upload Airbnb CSV File",
    type=["csv"],
    help="Select your Airbnb_Open_Data.csv file"
)


# ---------------- DATA LOADING ----------------

@st.cache_data(show_spinner="Loading and processing Airbnb dataset...")
def load_data(file):

    df = pd.read_csv(file, low_memory=False)

    # Remove unwanted columns if available
    drop_columns = [
        'id', 'lat', 'long', 'country code',
        'house_rules'
    ]

    df = df.drop(
        columns=[c for c in drop_columns if c in df.columns],
        errors='ignore'
    )

    # Rename columns
    df = df.rename(columns={
        'host id': 'host_id',
        'host name': 'host_name',
        'neighbourhood group': 'neighbourhood_group',
        'room type': 'room_type',
        'Construction year': 'Construction_year',
        'service fee': 'service_fee',
        'minimum nights': 'minimum_nights',
        'number of reviews': 'number_of_reviews',
        'last review': 'last_review',
        'reviews per month': 'reviews_per_month',
        'review rate number': 'review_rate_number',
        'calculated host listings count':
            'calculated_host_listings_count',
        'availability 365': 'availability_365'
    })

    # Clean neighbourhood names
    if 'neighbourhood_group' in df.columns:
        df['neighbourhood_group'] = (
            df['neighbourhood_group']
            .replace({
                'brookln': 'Brooklyn',
                'manhatan': 'Manhattan'
            })
        )

    # Clean missing values
    text_columns = [
        'NAME', 'host_identity_verified',
        'host_name', 'neighbourhood_group',
        'neighbourhood', 'country',
        'instant_bookable', 'cancellation_policy',
        'license', 'room_type'
    ]

    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].fillna('unknown')

    # Numeric columns
    numeric_columns = [
        'Construction_year',
        'price',
        'service_fee',
        'minimum_nights',
        'number_of_reviews',
        'reviews_per_month',
        'review_rate_number',
        'calculated_host_listings_count',
        'availability_365'
    ]

    fill_values = {
        'Construction_year': 2012,
        'price': 625,
        'service_fee': 125,
        'minimum_nights': 8.135,
        'number_of_reviews': 27,
        'reviews_per_month': 1.37,
        'review_rate_number': 3.27,
        'calculated_host_listings_count': 7.93,
        'availability_365': 141
    }

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(
                    r'[$,]', '', regex=True
                ),
                errors='coerce'
            )
            df[col] = df[col].fillna(fill_values[col])

    # Convert review date
    if 'last_review' in df.columns:
        df['last_review'] = pd.to_datetime(
            df['last_review'],
            errors='coerce'
        )

        df['Year'] = df['last_review'].dt.year
        df['Month'] = df['last_review'].dt.month

    return df


if uploaded_file is None:

    st.info("👈 Please upload your Airbnb CSV dataset to start.")

    st.markdown("### Dashboard Preview")
    st.write("Upload your dataset to explore interactive charts and KPIs.")

    st.stop()


# ---------------- LOAD DATA ----------------

try:
    df = load_data(uploaded_file)

except Exception as e:
    st.error(f"Error loading dataset: {e}")
    st.stop()


if df.empty:
    st.warning("The uploaded dataset is empty.")
    st.stop()


st.sidebar.success("Dataset uploaded successfully!")

st.sidebar.write("Total Rows:", f"{len(df):,}")
st.sidebar.write("Total Columns:", len(df.columns))


# ---------------- SIDEBAR FILTERS ----------------

st.sidebar.markdown("---")
st.sidebar.title("🎯 Dashboard Filters")

filtered_df = df.copy()

if 'neighbourhood_group' in df.columns:

    locations = sorted(
        df['neighbourhood_group'].dropna().unique()
    )

    selected_locations = st.sidebar.multiselect(
        "Select Location",
        locations,
        default=locations
    )

    filtered_df = filtered_df[
        filtered_df['neighbourhood_group'].isin(
            selected_locations
        )
    ]


if 'room_type' in df.columns:

    rooms = sorted(df['room_type'].dropna().unique())

    selected_rooms = st.sidebar.multiselect(
        "Select Room Type",
        rooms,
        default=rooms
    )

    filtered_df = filtered_df[
        filtered_df['room_type'].isin(selected_rooms)
    ]


if 'price' in df.columns and len(filtered_df) > 0:

    min_price = int(filtered_df['price'].min())
    max_price = int(filtered_df['price'].max())

    if min_price < max_price:

        price_range = st.sidebar.slider(
            "Select Price Range ($)",
            min_price,
            max_price,
            (min_price, max_price)
        )

        filtered_df = filtered_df[
            (filtered_df['price'] >= price_range[0]) &
            (filtered_df['price'] <= price_range[1])
        ]


if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()


# ---------------- KPI CARDS ----------------

st.markdown("## 📊 Airbnb Market Overview")

total_listings = len(filtered_df)

avg_price = filtered_df['price'].mean()

avg_availability = filtered_df['availability_365'].mean()

total_hosts = (
    filtered_df['host_id'].nunique()
    if 'host_id' in filtered_df.columns else 0
)

total_reviews = (
    filtered_df['number_of_reviews'].sum()
    if 'number_of_reviews' in filtered_df.columns else 0
)

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("🏠 Total Listings", f"{total_listings:,}")
k2.metric("💰 Average Price", f"${avg_price:,.0f}")
k3.metric("📅 Avg Availability", f"{avg_availability:,.1f} Days")
k4.metric("👤 Total Hosts", f"{total_hosts:,}")
k5.metric("⭐ Total Reviews", f"{total_reviews:,.0f}")


st.markdown("---")


# ---------------- LOCATION ANALYSIS ----------------

st.markdown("## 📍 Location Analysis")

col1, col2 = st.columns(2)

with col1:

    st.subheader("Top 10 Neighbourhoods by Listings")

    listing_data = (
        filtered_df['neighbourhood']
        .value_counts()
        .head(10)
        .reset_index()
    )

    listing_data.columns = ['Neighbourhood', 'Listings']

    fig1 = px.bar(
        listing_data,
        x='Listings',
        y='Neighbourhood',
        orientation='h',
        color='Listings',
        color_continuous_scale='Blues',
        text='Listings',
        template='plotly_white'
    )

    fig1.update_layout(
        height=450,
        yaxis={'categoryorder': 'total ascending'},
        showlegend=False,
        coloraxis_showscale=False,
        margin=dict(l=10,r=10,t=30,b=10)
    )

    fig1.update_traces(
        textposition='outside',
        cliponaxis=False
    )

    st.plotly_chart(fig1, use_container_width=True)


with col2:

    st.subheader("Top 10 Neighbourhoods by Average Price")

    price_data = (
        filtered_df.groupby('neighbourhood')['price']
        .mean()
        .nlargest(10)
        .reset_index()
    )

    price_data.columns = ['Neighbourhood', 'Average Price']

    fig2 = px.bar(
        price_data,
        x='Average Price',
        y='Neighbourhood',
        orientation='h',
        color='Average Price',
        color_continuous_scale='Sunset',
        text_auto='.0f',
        template='plotly_white'
    )

    fig2.update_layout(
        height=450,
        yaxis={'categoryorder': 'total ascending'},
        coloraxis_showscale=False,
        margin=dict(l=10,r=10,t=30,b=10)
    )

    st.plotly_chart(fig2, use_container_width=True)


st.markdown("---")


# ---------------- PRICE ANALYSIS ----------------

st.markdown("## 💰 Price Analysis")

col3, col4 = st.columns(2)

with col3:

    st.subheader("Price Distribution")

    fig3 = px.histogram(
        filtered_df,
        x='price',
        nbins=40,
        color_discrete_sequence=['#6366F1'],
        template='plotly_white',
        labels={'price': 'Price ($)'}
    )

    fig3.update_layout(
        height=420,
        bargap=0.08,
        xaxis_title="Price ($)",
        yaxis_title="Number of Listings"
    )

    st.plotly_chart(fig3, use_container_width=True)


with col4:

    st.subheader("Average Price by Room Type")

    room_price = (
        filtered_df.groupby('room_type')['price']
        .mean()
        .reset_index()
    )

    fig4 = px.bar(
        room_price,
        x='room_type',
        y='price',
        color='room_type',
        color_discrete_sequence=px.colors.qualitative.Bold,
        text_auto='.0f',
        template='plotly_white'
    )

    fig4.update_layout(
        height=420,
        showlegend=False,
        xaxis_title="Room Type",
        yaxis_title="Average Price ($)"
    )

    st.plotly_chart(fig4, use_container_width=True)


# ---------------- ROOM TYPE DISTRIBUTION ----------------

st.markdown("---")
st.markdown("## 🛏️ Room Type Distribution")

room_count = (
    filtered_df['room_type']
    .value_counts()
    .reset_index()
)

room_count.columns = ['Room Type', 'Listings']

fig5 = px.pie(
    room_count,
    names='Room Type',
    values='Listings',
    hole=0.55,
    color_discrete_sequence=px.colors.qualitative.Pastel,
    template='plotly_white'
)

fig5.update_traces(
    textposition='inside',
    textinfo='percent+label'
)

fig5.update_layout(
    height=450,
    legend_title="Room Types"
)

st.plotly_chart(fig5, use_container_width=True)


# ---------------- AVAILABILITY ANALYSIS ----------------

st.markdown("---")
st.markdown("## 📅 Availability Analysis")

col5, col6 = st.columns(2)

with col5:

    st.subheader("Average Availability by Month")

    if 'Month' in filtered_df.columns:

        month_data = (
            filtered_df.dropna(subset=['Month'])
            .groupby('Month')['availability_365']
            .mean()
            .reset_index()
        )

        month_data['Month'] = month_data['Month'].astype(int)

        month_names = {
            1: 'Jan', 2: 'Feb', 3: 'Mar',
            4: 'Apr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Aug', 9: 'Sep',
            10: 'Oct', 11: 'Nov', 12: 'Dec'
        }

        month_data['Month Name'] = (
            month_data['Month'].map(month_names)
        )

        fig6 = px.line(
            month_data,
            x='Month Name',
            y='availability_365',
            markers=True,
            line_shape='spline',
            color_discrete_sequence=['#2563EB'],
            template='plotly_white'
        )

        fig6.update_traces(
            line_width=4,
            marker_size=10
        )

        fig6.update_layout(
            height=420,
            xaxis_title="Month",
            yaxis_title="Average Available Days"
        )

        st.plotly_chart(fig6, use_container_width=True)


with col6:

    st.subheader("Yearly Availability Trend")

    if 'Year' in filtered_df.columns:

        year_data = (
            filtered_df.dropna(subset=['Year'])
            .groupby('Year')['availability_365']
            .mean()
            .reset_index()
        )

        year_data['Year'] = year_data['Year'].astype(int)

        fig7 = px.bar(
            year_data,
            x='Year',
            y='availability_365',
            color='availability_365',
            color_continuous_scale='Teal',
            text_auto='.1f',
            template='plotly_white'
        )

        fig7.update_layout(
            height=420,
            coloraxis_showscale=False,
            xaxis_title="Year of Last Review",
            yaxis_title="Average Availability"
        )

        st.plotly_chart(fig7, use_container_width=True)


# ---------------- ROOM TYPE BY LOCATION ----------------

st.markdown("---")
st.markdown("## 🏘️ Room Types by Location")

if 'neighbourhood_group' in filtered_df.columns:

    location_room = (
        filtered_df.groupby(
            ['neighbourhood_group', 'room_type']
        ).size().reset_index(name='Listings')
    )

    fig8 = px.bar(
        location_room,
        x='neighbourhood_group',
        y='Listings',
        color='room_type',
        barmode='group',
        text_auto=True,
        color_discrete_sequence=px.colors.qualitative.Bold,
        template='plotly_white'
    )

    fig8.update_layout(
        height=480,
        xaxis_title="Neighbourhood Group",
        yaxis_title="Number of Listings",
        legend_title="Room Type"
    )

    st.plotly_chart(fig8, use_container_width=True)


# ---------------- CORRELATION ANALYSIS ----------------

st.markdown("---")
st.markdown("## 🔥 Price Correlation Analysis")

corr_columns = [
    'price',
    'number_of_reviews',
    'service_fee',
    'minimum_nights',
    'reviews_per_month',
    'review_rate_number',
    'calculated_host_listings_count',
    'availability_365'
]

available_corr = [
    c for c in corr_columns if c in filtered_df.columns
]

if len(available_corr) > 1:

    correlation = filtered_df[available_corr].corr()

    fig9 = px.imshow(
        correlation,
        text_auto='.2f',
        color_continuous_scale='RdBu_r',
        zmin=-1,
        zmax=1,
        aspect='auto',
        template='plotly_white'
    )

    fig9.update_layout(
        height=550,
        title="Correlation Between Airbnb Features"
    )

    st.plotly_chart(fig9, use_container_width=True)


# ---------------- HOST ANALYSIS ----------------

st.markdown("---")
st.markdown("## 👤 Host Analysis")

col7, col8 = st.columns(2)

with col7:

    st.subheader("Top 10 Hosts by Listings")

    if 'host_id' in filtered_df.columns:

        host_data = (
            filtered_df.groupby('host_id')
            .size()
            .nlargest(10)
            .reset_index(name='Listings')
        )

        host_data['host_id'] = host_data['host_id'].astype(str)

        fig10 = px.bar(
            host_data,
            x='Listings',
            y='host_id',
            orientation='h',
            color='Listings',
            color_continuous_scale='Viridis',
            text='Listings',
            template='plotly_white'
        )

        fig10.update_layout(
            height=430,
            yaxis={'categoryorder': 'total ascending'},
            coloraxis_showscale=False,
            yaxis_title="Host ID"
        )

        st.plotly_chart(fig10, use_container_width=True)


with col8:

    st.subheader("Review Ratings by Verification Status")

    if 'host_identity_verified' in filtered_df.columns:

        verify_data = (
            filtered_df.groupby('host_identity_verified')
            ['review_rate_number']
            .mean()
            .reset_index()
        )

        fig11 = px.bar(
            verify_data,
            x='host_identity_verified',
            y='review_rate_number',
            color='host_identity_verified',
            text_auto='.2f',
            color_discrete_sequence=['#0EA5E9','#A78BFA','#F59E0B'],
            template='plotly_white'
        )

        fig11.update_layout(
            height=430,
            showlegend=False,
            xaxis_title="Host Verification",
            yaxis_title="Average Review Rating"
        )

        st.plotly_chart(fig11, use_container_width=True)


# ---------------- DATA TABLE ----------------

st.markdown("---")
st.markdown("## 📋 Airbnb Dataset Details")

with st.expander("View Dataset"):

    st.write("Total Records:", f"{len(filtered_df):,}")

    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=400
    )


# ---------------- DOWNLOAD CLEANED DATA ----------------

st.markdown("---")

st.subheader("📥 Download Cleaned Dataset")

csv_data = filtered_df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="Download Cleaned CSV",
    data=csv_data,
    file_name="Airbnb_Cleaned_Data.csv",
    mime="text/csv"
)


# ---------------- FOOTER ----------------

st.markdown("---")

st.markdown(
    "<center>🏡 Airbnb Analytics Dashboard | "
    "Developed using Python, Streamlit & Plotly</center>",
    unsafe_allow_html=True
)
