
import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import Search, Geocoder  # Import Geocoder for place search

# Load the shapefile and CSV
shapefile_path = "AllGroup.shp"
csv_path = "LicenseHref.csv"

gdf = gpd.read_file(shapefile_path)
df = pd.read_csv(csv_path)

# Select only the "Group", "Color", and "Line_wt" columns from the CSV
df= df[["Group", "Color", "Line_wt"]]

# Merge data on "Group"
gdf = gdf.merge(df, on="Group")

print(gdf.columns)

# Ensure geometries are valid and in WGS84 (Leaflet requires EPSG:4326)
gdf = gdf.to_crs(epsg=4326)

# Create a base map centered on the data
m = folium.Map(
    location=[gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()],
    zoom_start=10,
    control_scale=True  # Adds a scale bar
)

# Add base layers (OpenStreetMap and Google Satellite)
# osm = folium.TileLayer(
#     tiles='openstreetmap',
#     name='OpenStreetMap',
#     overlay=False,
#     control=True  # Ensure it appears in layer control
# ).add_to(m)

google_sat_hybrid = folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',  # Hybrid layer
    attr='Google',
    name='Google Satellite Hybrid',
    overlay=False,
    control=True
).add_to(m)

# Create a FeatureGroup for geometries
feature_group = folium.FeatureGroup(name="Power Projects", show=True)

# Add each geometry to the FeatureGroup
for _, row in gdf.iterrows():
    # Create a popup with attributes
    popup_content = ""
    for col in row.index:
        if col not in ['geometry', 'Line_wt', 'Color']:
            popup_content += f"<b>{col}:</b> {row[col]}<br>"

    # Style the geometry (hollow with outline)
    style = {
        'color': row['Color'],
        'weight': row['Line_wt'],
        'fill': False,
        'fillOpacity': 0
    }

    # Add GeoJSON to FeatureGroup
    folium.GeoJson(
        data=row.geometry.__geo_interface__,
        style_function=lambda x, style=style: style,
        popup=folium.Popup(popup_content, max_width=300)
    ).add_to(feature_group)

# Add FeatureGroup to the map
feature_group.add_to(m)

# Add Search plugin for the "Name" attribute
project_search = Search(
    layer=feature_group,
    search_label='Project',  # Must match the attribute name in your data
    placeholder='Search projects...',
    collapsed=False,
    position='topright'
).add_to(m)

# -----------------------------------------------
# 2. Add Place Search (geocoding for Google Satellite Hybrid)
# -----------------------------------------------
# Use Geocoder plugin (uses OpenStreetMap Nominatim by default)
Geocoder(
    position="bottomright",
    collapsed=False,
    provider='nominatim',  # Use Nominatim for place search
    placeholder='Search places (e.g., Kathmandu, Taplejung)...',
    add_marker=True  # Add a marker when a place is found
).add_to(m)

# Add Layer Control to toggle base layers/overlays
folium.LayerControl(collapsed=False).add_to(m)

# Save the map
m.save("leaflet_map.html")

print("Map saved successfully!")


