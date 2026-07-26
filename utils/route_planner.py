from math import asin, cos, radians, sin, sqrt
def distance_km(a,b):
    lat1,lon1,lat2,lon2=map(radians,[a[0],a[1],b[0],b[1]]); return 2*6371*asin(sqrt(sin((lat2-lat1)/2)**2+cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2))
def plan_route(defects,depot,max_repairs):
    remaining=sorted(defects,key=lambda x:x["priority_score"],reverse=True)[:max_repairs]; ordered=[]; current=depot
    while remaining:
        stop=min(remaining,key=lambda x:distance_km(current,(x["latitude"],x["longitude"]))-(x["priority_score"]/1000)); ordered.append(stop); current=(stop["latitude"],stop["longitude"]); remaining.remove(stop)
    points=[depot]+[(x["latitude"],x["longitude"]) for x in ordered]+[depot]; total=sum(distance_km(a,b) for a,b in zip(points,points[1:])); available=sum(x["priority_score"] for x in defects) or 1
    return {"depot":depot,"stops":ordered,"points":points,"distance_km":total,"priority_coverage":sum(x["priority_score"] for x in ordered)/available*100}
