"""Portable HTML inspection report generator."""
from html import escape


def build_html_report(record):
    summary = record["summary"]
    rows = "".join(
        f"<tr><td>{escape(item['id'])}</td><td>{escape(item['damage_type'])}</td><td>{escape(item['severity'])}</td><td>{item['confidence']:.0%}</td><td>{item['priority_score']:.0f}/100</td><td>{item.get('duplicate_count',1)}</td></tr>"
        for item in sorted(record["defects"], key=lambda value: value["priority_score"], reverse=True)
    ) or '<tr><td colspan="6">No visible defects recorded.</td></tr>'
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>RoadAudit Inspection #{record['id']}</title>
    <style>body{{font-family:Segoe UI,Arial;color:#102033;margin:40px;max-width:1100px}}header{{background:#071426;color:white;padding:28px;border-radius:16px}}h1{{margin:0}}.sub{{color:#b9c9d9}}.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:24px 0}}.metric{{border:1px solid #dbe4ef;border-radius:12px;padding:16px}}.metric b{{font-size:26px;display:block}}table{{width:100%;border-collapse:collapse}}th,td{{padding:11px;border-bottom:1px solid #dbe4ef;text-align:left}}th{{background:#eef4fb}}.note{{margin-top:24px;padding:16px;background:#fff7ed;border-left:4px solid #f97316}}@media print{{body{{margin:15px}}}}</style></head>
    <body><header><h1>RoadAudit AI</h1><p class="sub">Inspection record #{record['id']} · {escape(record['source_name'])} · {escape(record['created_at'])}</p></header>
    <section class="metrics"><div class="metric">Road health<b>{summary['road_health_index']}%</b>{escape(summary['health_label'])}</div><div class="metric">Unique defects<b>{summary['unique_defects']}</b>{summary['raw_detections']} observations</div><div class="metric">Urgent repairs<b>{summary['urgent_repairs']}</b>priority above 80</div><div class="metric">Budget estimate<b>Rs. {summary['estimated_cost']:,.0f}</b>planning value</div></section>
    <h2>Ranked maintenance register</h2><table><thead><tr><th>ID</th><th>Damage</th><th>Severity</th><th>Confidence</th><th>Priority</th><th>Observations</th></tr></thead><tbody>{rows}</tbody></table>
    <div class="note"><strong>Prototype disclosure:</strong> severity is image-based; GPS, traffic, road importance, and cost are planning assumptions. Critical maintenance decisions require field verification.</div></body></html>"""
