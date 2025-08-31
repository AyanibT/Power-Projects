import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import Search, Geocoder
import json

# Load the shapefile and CSV
shapefile_path = "AllGroup.shp"
csv_path = "LicenseHref.csv"

gdf = gpd.read_file(shapefile_path)
df = pd.read_csv(csv_path)

# Merge data on "Group" and "Sub_Group"
df_selected = df[["Group", "Sub_Group", "Color", "Line_wt","Category"]]
gdf = gdf.merge(df_selected, on=["Group", "Sub_Group"], how="left")

# Using fullform from "Category" {PP = Power Plants}
gdf["Group"]=gdf["Category"]
gdf.drop('Category', axis='columns', inplace=True)

gdf = gdf.to_crs(epsg=4326)

# Create a base map
m = folium.Map(
    location=[gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()],
    zoom_start=7,
    control_scale=True
)

# Add base layers
# folium.TileLayer('openstreetmap', name='OpenStreetMap').add_to(m)
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google',
    name='Google Satellite Hybrid'
).add_to(m)

# Create a FeatureGroup for geometries
feature_group = folium.FeatureGroup(name="Projects")
for _, row in gdf.iterrows():
    popup_content = f"""
        <div style="width: 250px; word-wrap: break-word;">
        """
    for col in row.index:
        if col not in ['geometry', 'Line_wt', 'Color']:
            popup_content += f"<b>{col}:</b> {row[col]}<br>"
    popup_content += "</div>"

    # folium.GeoJson(
    #     row.geometry.__geo_interface__,
    #     style_function=lambda x, color=row['Color'], weight=row['Line_wt']: {
    #         'color': color,
    #         'weight': weight,
    #         'fill': False
    #     },
    #     popup=folium.Popup(popup_content),

    # ).add_to(feature_group)

    folium.GeoJson(
        {
            "type": "Feature",
            "geometry": row.geometry.__geo_interface__,
            "properties": {
                "Project": row['Project']  # Explicitly set properties for search
            }
        },
        style_function=lambda x, color=row['Color'], weight=row['Line_wt']: {
            'color': color,
            'weight': weight,
            'fill': False
        },
        popup=folium.Popup(popup_content),
        tooltip=row['Project'],  # Tooltip for better visibility
        name=row['Project']  # Ensures better search compatibility
    ).add_to(feature_group)


feature_group.add_to(m)

# Add search bars
project_search = Search(
    layer=feature_group,
    search_label='Project',
    placeholder='Search projects...',
    position='topright'
).add_to(m)

Geocoder(
    position='bottomright',
    placeholder='Search places (Kathmnadu, Palpa...',
).add_to(m)

# Add Layer Control
folium.LayerControl().add_to(m)

# Extract project names with bounding coordinates
project_data = {
    row['Project']: row.geometry.bounds for _, row in gdf.iterrows()
}
project_data_js = json.dumps(project_data)

# Inject jQuery UI and custom JavaScript/CSS
autocomplete_js = """
<link rel="stylesheet" href="https://code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css">
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://code.jquery.com/ui/1.12.1/jquery-ui.min.js"></script>
<script>
$(document).ready(function() {
    const projectData = %s;  // Injected from Python
    
    const map = window.%s;  // Ensure correct map reference

    $(".search-input").autocomplete({
        source: Object.keys(projectData),
        minLength: 1,
        appendTo: ".search-control",
        select: function(event, ui) {
            const searchInput = $(".search-input");
            searchInput.val(ui.item.value);

            // Get the bounding box of the selected project
            const bounds = projectData[ui.item.value];
            if (bounds) {
                let southWest = [bounds[1], bounds[0]];  // minY, minX
                let northEast = [bounds[3], bounds[2]];  // maxY, maxX

                // Apply bounds to the map
                map.fitBounds([southWest, northEast]);
            } else {
                console.error("Bounds not found for", ui.item.value);
            }
        }
    });

    $(".ui-autocomplete").css("z-index", "9999");
});
</script>
""" % (project_data_js, m.get_name())  # Inject correct map variable name

# Define the HTML title with styling
title_html = '''
<div style="
    position: fixed; 
    top: 10px; left: 50%; 
    transform: translateX(-50%);
    background-color: rgba(255, 255, 255, 0.7); 
    padding: 10px 20px; 
    font-size: 20px; 
    font-weight: bold;
    border-radius: 5px;
    box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2);
    z-index: 9999;">
    Power Plant Projects of Nepal
</div>
'''
# Define the HTML footer with styling
footer_html = '''
<div style="
    position: fixed;
    bottom: 55px; right: 10px;
    background-color: rgba(255, 255, 255, 0.7);
    padding: 3px 5px;
    font-size: 12px;
    text-align: right;
    border-radius: 5px;
    box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2);
    z-index: 999;">
    Updated: Aug 29, 2025<br>
    Made by: <a href="https://www.linkedin.com/in/binaya-basnet" target="_blank" style="color: #0073b1; text-decoration: none;">
        Er. Binaya Basnet
    </a>
</div>
'''

# Define the HTML for the legend with styling
legend_html = '''
<div style="
    position: fixed;
    bottom: 40px; left: 10px;
    box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2);
    z-index: 9999;">
    <img src="Legend.png" alt="Legend" style="width: 250px; opacity: 0.7;">
</div>
'''

# Add the JavaScript/CSS to the map
m.get_root().html.add_child(folium.Element(autocomplete_js))

# Add the title to the Folium map
m.get_root().html.add_child(folium.Element(title_html))

# Add the footer to the Folium map
m.get_root().html.add_child(folium.Element(footer_html))

# Add the Legend to the Folium map
m.get_root().html.add_child(folium.Element(legend_html))

# Save the map
m.save("index.html")
print("Map saved with bounding box zooming!")
