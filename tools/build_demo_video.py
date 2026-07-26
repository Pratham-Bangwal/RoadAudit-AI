"""Render a narrated RoadAudit AI walkthrough from real product logic."""
from pathlib import Path
import math
import wave

import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "RoadAudit_AI_Demo_Silent.mp4"
AUDIO = ROOT / "outputs" / "RoadAudit_AI_Narration.wav"
WIDTH, HEIGHT, FPS = 1920, 1080, 30
NAVY, BLUE, CYAN, ORANGE, WHITE, MUTED, GREEN, RED = "#071426", "#2563eb", "#22d3ee", "#f97316", "#f8fafc", "#a9bad0", "#22c55e", "#ef4444"
FONT = Path("C:/Windows/Fonts/segoeui.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/seguisb.ttf")


def font(size, bold=False):
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT), size)


def base(title, kicker):
    image = Image.new("RGB", (WIDTH, HEIGHT), NAVY)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((70, 50, 1850, 1030), 28, fill="#0c1d34", outline="#17395f", width=2)
    draw.text((120, 92), kicker.upper(), font=font(24, True), fill=CYAN)
    draw.text((120, 138), title, font=font(58, True), fill=WHITE)
    draw.text((120, 990), "RoadAudit AI  |  Prototype Walkthrough", font=font(22), fill=MUTED)
    return image, draw


def wrapped(draw, text, box, size=34, color=MUTED, bold=False, spacing=12):
    words, lines, line = text.split(), [], ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font(size, bold))[2] <= box[2] - box[0]: line = candidate
        else: lines.append(line); line = word
    if line: lines.append(line)
    y = box[1]
    for item in lines:
        draw.text((box[0], y), item, font=font(size, bold), fill=color); y += size + spacing
    return y


def card(draw, xy, title, value, accent=BLUE, subtitle=""):
    draw.rounded_rectangle(xy, 20, fill="#102943", outline="#1d466f", width=2)
    draw.rectangle((xy[0], xy[1], xy[0]+8, xy[3]), fill=accent)
    draw.text((xy[0]+34, xy[1]+28), title, font=font(25), fill=MUTED)
    draw.text((xy[0]+34, xy[1]+72), value, font=font(48, True), fill=WHITE)
    if subtitle: draw.text((xy[0]+34, xy[3]-45), subtitle, font=font(21), fill=accent)


def slide_intro():
    im, d = base("From detection to repair accountability", "RoadAudit AI")
    d.text((120, 295), "AI-powered road asset intelligence", font=font(42), fill=MUTED)
    stages = ["DETECT", "DEDUPLICATE", "PRIORITIZE", "ROUTE", "VERIFY"]
    for i, stage in enumerate(stages):
        x = 120 + i*335
        d.rounded_rectangle((x, 470, x+270, 610), 22, fill="#102943", outline=CYAN if i==0 else "#254a70", width=3)
        d.text((x+28, 518), stage, font=font(28, True), fill=WHITE)
        if i < len(stages)-1: d.polygon([(x+288, 535),(x+318,550),(x+288,565)], fill=ORANGE)
    wrapped(d, "Existing vehicle cameras become continuous road inspectors—without requiring citizen reporting or new roadside infrastructure.", (120, 730, 1740, 900), 34, MUTED)
    return im


def slide_upload():
    im, d = base("Capture road evidence during routine travel", "1 · Inspection input")
    d.rounded_rectangle((120, 290, 880, 850), 28, fill="#091a2f", outline="#2b547d", width=2)
    d.rounded_rectangle((205, 410, 795, 690), 25, fill="#102943", outline=BLUE, width=3)
    d.text((440, 465), "+", font=font(90, True), fill=CYAN)
    d.text((310, 585), "UPLOAD IMAGE OR VIDEO", font=font(29, True), fill=WHITE)
    d.text((300, 645), "JPG · PNG · MP4 · AVI · MOV", font=font(22), fill=MUTED)
    items = [("Municipal vehicle", "Routine inspection"), ("Public bus", "Zero new fleet"), ("Smartphone mount", "Low-cost pilot")]
    for i,(a,b) in enumerate(items):
        y=320+i*170; card(d,(1030,y,1740,y+135),a,b,CYAN)
    return im


def slide_detection():
    im, d = base("Detect damage and estimate severity", "2 · Computer vision")
    d.polygon([(150,850),(650,330),(1210,330),(1740,850)], fill="#263649")
    d.line((935,350,935,820), fill="#f8fafc", width=10)
    d.ellipse((570,660,920,850), fill="#171717", outline="#2b2b2b", width=8)
    d.rounded_rectangle((520,590,980,900), 8, outline=RED, width=8)
    d.rectangle((520,535,1030,595), fill=RED)
    d.text((542,548), "POTHOLE · SEVERE · 92%", font=font(27, True), fill=WHITE)
    d.line((1230,540,1480,760), fill="#1a1a1a", width=17)
    d.rounded_rectangle((1175,475,1535,825), 8, outline=ORANGE, width=8)
    d.rectangle((1175,420,1600,480), fill=ORANGE)
    d.text((1195,433), "LONGITUDINAL CRACK · 84%", font=font(24, True), fill=WHITE)
    return im


def slide_dashboard():
    im, d = base("Convert detections into decisions", "3 · Intelligence dashboard")
    card(d,(120,300,500,500),"ROAD HEALTH INDEX","52%",ORANGE,"Needs maintenance")
    card(d,(540,300,920,500),"UNIQUE DEFECTS","18",CYAN,"126 raw observations")
    card(d,(960,300,1340,500),"URGENT REPAIRS","4",RED,"Priority above 80")
    card(d,(1380,300,1760,500),"ESTIMATED BUDGET","Rs. 2.4L",GREEN,"Planning estimate")
    d.rounded_rectangle((120,565,1080,880),20,fill="#102943",outline="#1d466f")
    d.text((155,595),"EXPLAINABLE PRIORITY REGISTER",font=font(27,True),fill=WHITE)
    rows=[("RD-012","Pothole","Critical","94/100"),("RD-016","Pothole","Severe","89/100"),("RD-008","Crack","Moderate","48/100")]
    for i,row in enumerate(rows):
        y=665+i*65; d.line((155,y-10,1045,y-10),fill="#264561",width=2)
        for x,text in zip((160,350,580,825),row): d.text((x,y),text,font=font(24, i==0),fill=WHITE if i==0 else MUTED)
    d.rounded_rectangle((1135,565,1760,880),20,fill="#102943",outline="#1d466f")
    d.text((1170,595),"SEVERITY DISTRIBUTION",font=font(27,True),fill=WHITE)
    bars=[("Critical",4,RED),("Severe",6,ORANGE),("Moderate",5,"#eab308"),("Minor",3,GREEN)]
    for i,(label,value,color) in enumerate(bars):
        y=665+i*52; d.text((1170,y),label,font=font(22),fill=MUTED); d.rounded_rectangle((1330,y,1330+value*55,y+28),8,fill=color)
    return im


def slide_route():
    im, d = base("Plan the highest-value repair route", "4 · NetworkX optimization")
    d.rounded_rectangle((120,280,1250,900),24,fill="#dbeafe",outline="#4f83bd")
    for x in range(180,1200,170): d.line((x,300,x-80,880),fill="#aac5df",width=14)
    for y in range(350,880,135): d.line((140,y,1230,y+45),fill="#aac5df",width=12)
    points=[(220,780),(390,650),(610,700),(760,500),(990,550),(1110,360),(220,780)]
    d.line(points,fill=BLUE,width=12,joint="curve")
    for i,(x,y) in enumerate(points[:-1]):
        color=BLUE if i==0 else RED; d.ellipse((x-24,y-24,x+24,y+24),fill=color,outline=WHITE,width=4); d.text((x-8,y-16),"D" if i==0 else str(i),font=font(22,True),fill=WHITE)
    card(d,(1320,310,1760,480),"SCHEDULED REPAIRS","5",CYAN)
    card(d,(1320,520,1760,690),"ROUTE LENGTH","7.8 km",BLUE)
    card(d,(1320,730,1760,900),"PRIORITY COVERAGE","87%",GREEN)
    return im


def slide_verify():
    im, d = base("Close the accountability loop", "5 · Repair verification")
    for left,title,color,health in [(120,"BEFORE REPAIR",RED,"42%"),(1010,"AFTER REPAIR",GREEN,"87%")]:
        d.rounded_rectangle((left,300,left+780,820),25,fill="#102943",outline=color,width=3)
        d.text((left+35,335),title,font=font(28,True),fill=color)
        d.polygon([(left+80,710),(left+320,440),(left+700,710)],fill="#3b4652")
        if title.startswith("BEFORE"):
            d.ellipse((left+300,600,left+510,735),fill="#171717"); d.rectangle((left+260,560,left+550,765),outline=RED,width=6)
        else: d.rounded_rectangle((left+285,610,left+525,700),25,fill="#6b7280")
        d.text((left+35,755),f"Road health: {health}",font=font(28,True),fill=WHITE)
    d.rounded_rectangle((660,870,1260,955),18,fill="#123d2a",outline=GREEN,width=3)
    d.text((735,895),"REPAIR LIKELY COMPLETED",font=font(28,True),fill=GREEN)
    return im


def slide_close():
    im, d = base("Safer roads. Faster repairs. Better accountability.", "RoadAudit AI")
    d.text((120,330),"DETECTION",font=font(52,True),fill=CYAN); d.text((465,330),"→",font=font(52),fill=ORANGE)
    d.text((550,330),"DECISION",font=font(52,True),fill=CYAN); d.text((850,330),"→",font=font(52),fill=ORANGE)
    d.text((940,330),"ACTION",font=font(52,True),fill=CYAN); d.text((1165,330),"→",font=font(52),fill=ORANGE)
    d.text((1250,330),"ACCOUNTABILITY",font=font(52,True),fill=CYAN)
    wrapped(d,"FastAPI · SQLite · YOLO · DBSCAN · NetworkX · Streamlit · Folium",(120,560,1760,670),37,WHITE,True)
    wrapped(d,"An AI-powered road asset intelligence and maintenance management platform.",(120,710,1760,850),36,MUTED)
    return im


def main():
    ROOT.joinpath("outputs").mkdir(exist_ok=True)
    with wave.open(str(AUDIO), "rb") as audio:
        duration = audio.getnframes() / audio.getframerate()
    slides = [slide_intro(),slide_upload(),slide_detection(),slide_dashboard(),slide_route(),slide_verify(),slide_close()]
    weights = [0.08,0.13,0.17,0.22,0.17,0.15,0.08]
    writer = cv2.VideoWriter(str(OUTPUT),cv2.VideoWriter_fourcc(*"mp4v"),FPS,(WIDTH,HEIGHT))
    for image,weight in zip(slides,weights):
        frame=cv2.cvtColor(__import__("numpy").array(image),cv2.COLOR_RGB2BGR)
        for _ in range(max(1,math.ceil(duration*weight*FPS))): writer.write(frame)
    writer.release()
    print(OUTPUT)


if __name__ == "__main__": main()
