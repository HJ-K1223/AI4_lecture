import numpy as np
import pandas as pd

np.random.seed(42)

# 서울 중심 좌표
SEOUL_CENTER = [37.5665, 126.9780]

# 가상 상점 업종
categories = {
    "음식점": "red",
    "카페": "blue",
    "편의점": "green",
    "의류": "purple",
    "화장품": "orange",
    "병원": "cadetblue",
}

# 서울 주요 상권의 중심 좌표
areas = {
    "강남": (37.4979, 127.0276),
    "홍대": (37.5563, 126.9236),
    "종로": (37.5729, 126.9793),
    "성수": (37.5445, 127.0557),
    "잠실": (37.5133, 127.1001),
    "여의도": (37.5219, 126.9245),
    "명동": (37.5636, 126.9869),
    "건대": (37.5404, 127.0698),
}

stores = []

for i in range(50):
    area = np.random.choice(list(areas.keys()))
    lat, lon = areas[area]

    category = np.random.choice(list(categories.keys()))

    stores.append({
        "store_id": f"S{i+1:04d}",
        "store_name": f"{area}_{category}_{i+1}",
        "category": category,
        "area": area,
        "latitude": lat + np.random.normal(0, 0.008),
        "longitude": lon + np.random.normal(0, 0.008),
        "sales": np.random.randint(100, 5000) * 10000,
        "rating": round(np.random.uniform(2.5, 5.0), 1),
        "visitors": np.random.randint(10, 1000),
    })

df = pd.DataFrame(stores)

print(df.head())


import folium

m = folium.Map(
    location=SEOUL_CENTER,
    zoom_start=12,
    tiles="OpenStreetMap"
)

for _, row in df.iterrows():

    color = categories[row["category"]]

    folium.Marker(
        location=[
            row["latitude"],
            row["longitude"]
        ],
        tooltip=row["store_name"],
        popup=folium.Popup(
            f"""
            <b>{row['store_name']}</b><br>
            업종: {row['category']}<br>
            상권: {row['area']}<br>
            매출: {row['sales']:,}원<br>
            평점: {row['rating']}
            """,
            max_width=300
        ),
        icon=folium.Icon(
            color=color,
            icon="shopping-cart",
            prefix="fa"
        )
    ).add_to(m)

m.save("01_marker.html")


from folium.plugins import MarkerCluster

m = folium.Map(SEOUL_CENTER, zoom_start=11)

cluster = MarkerCluster().add_to(m)

for _, row in df.iterrows():
    folium.Marker(
        [row.latitude, row.longitude],
        popup=row.store_name
    ).add_to(cluster)

m.save("06_cluster.html")