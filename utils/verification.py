WEIGHT={"Minor":1,"Moderate":2,"Severe":3,"Critical":4}
def compare_inspections(before_defects,before_summary,after_defects,after_summary):
    before_risk=sum(WEIGHT[x["severity"]] for x in before_defects); after_risk=sum(WEIGHT[x["severity"]] for x in after_defects); change=after_summary["road_health_index"]-before_summary["road_health_index"]
    if after_risk==0: status,explanation="Repair likely completed","No visible defects were detected after repair. Field inspection should confirm engineering quality."
    elif after_risk<before_risk or change>=10: status,explanation="Partial repair / manual review","The visual risk profile improved, but visible defects remain. Manual verification is recommended."
    else: status,explanation="Repair not verified","The post-repair image shows similar or higher visible damage. Confirm that the same road location and camera view were used."
    return {"status":status,"explanation":explanation,"health_change":change,"before_risk":before_risk,"after_risk":after_risk}
