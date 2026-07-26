import random
import numpy as np
from sklearn.cluster import DBSCAN

SEVERITY_POINTS={"Minor":1,"Moderate":2,"Severe":3,"Critical":4}; SEVERITY_SCORE={"Minor":25,"Moderate":50,"Severe":75,"Critical":100}; ROAD_SCORE={"Hospital / emergency route":100,"Main road":75,"Local road":45}; COST={"Minor":2000,"Moderate":7000,"Severe":15000,"Critical":35000}
def severity_from_bbox(bbox):
    area=max(0,bbox[2]-bbox[0])*max(0,bbox[3]-bbox[1])
    if area>=70000:return "Critical"
    if area>=35000:return "Severe"
    if area>=12000:return "Moderate"
    return "Minor"
def enrich_detections(raw, traffic, road_type):
    random.seed(14); enriched=[]
    for index,item in enumerate(raw,start=1):
        severity=severity_from_bbox(item["bbox"]); score=min(round(.45*SEVERITY_SCORE[severity]+.25*ROAD_SCORE[road_type]+.20*traffic+.10*(item["confidence"]*100),1),100); label="Urgent" if score>=80 else "High" if score>=60 else "Medium" if score>=40 else "Low"; group=index%2
        enriched.append({**item,"id":f"RD-{index:03}","severity":severity,"priority_score":score,"priority":label,"latitude":32.7266+group*.0014+random.uniform(-.00004,.00004),"longitude":74.8570+group*.0012+random.uniform(-.00004,.00004)})
    return enriched
def remove_duplicates(detections):
    if not detections:return []
    coords=np.array([[x["latitude"],x["longitude"]] for x in detections]); labels=DBSCAN(eps=.00020,min_samples=1).fit_predict(coords); unique=[]
    for label in sorted(set(labels)):
        group=[item for item,assigned in zip(detections,labels) if assigned==label]; best=dict(max(group,key=lambda x:x["confidence"])); best["duplicate_count"]=len(group); unique.append(best)
    return sorted(unique,key=lambda x:x["priority_score"],reverse=True)
def build_summary(defects):
    raw=sum(x.get("duplicate_count",1) for x in defects); points=sum(SEVERITY_POINTS[x["severity"]]*8 for x in defects); rhi=max(0,round(100-points)); label="Excellent" if rhi>=80 else "Needs maintenance" if rhi>=60 else "Poor"
    return {"unique_defects":len(defects),"raw_detections":raw,"urgent_repairs":sum(x["priority"]=="Urgent" for x in defects),"estimated_cost":sum(COST[x["severity"]] for x in defects),"road_health_index":rhi,"health_label":label}
