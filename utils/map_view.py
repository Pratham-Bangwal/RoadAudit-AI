import folium
def build_map(defects):
    center=[defects[0]["latitude"],defects[0]["longitude"]] if defects else [32.7266,74.8570]; road_map=folium.Map(location=center,zoom_start=15,tiles="OpenStreetMap"); colors={"Minor":"green","Moderate":"orange","Severe":"red","Critical":"darkred"}
    for defect in defects:
        folium.Marker(location=[defect["latitude"],defect["longitude"]],tooltip=f"{defect['id']} · {defect['severity']}",popup=f"<b>{defect['damage_type']}</b><br>Priority: {defect['priority_score']}/100<br>Repeated observations: {defect['duplicate_count']}",icon=folium.Icon(color=colors[defect["severity"]],icon="warning-sign")).add_to(road_map)
    return road_map

def build_route_map(route):
    road_map=folium.Map(location=route["depot"],zoom_start=15,tiles="OpenStreetMap")
    folium.Marker(route["depot"],tooltip="Repair depot",icon=folium.Icon(color="blue",icon="home")).add_to(road_map); folium.PolyLine(route["points"],color="#2563eb",weight=5,opacity=.8).add_to(road_map)
    for number,defect in enumerate(route["stops"],start=1):
        folium.Marker([defect["latitude"],defect["longitude"]],tooltip=f"Stop {number}: {defect['id']}",popup=f"<b>Stop {number}</b><br>{defect['damage_type']}<br>{defect['severity']} - {defect['priority_score']:.0f}/100",icon=folium.Icon(color="red" if defect["severity"] in {"Critical","Severe"} else "orange",icon="wrench")).add_to(road_map)
    return road_map
