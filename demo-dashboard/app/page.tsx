"use client";

import { useMemo, useState } from "react";
import Image from "next/image";

type InspectionState = "ready" | "running" | "complete";

const defects = [
  {
    id: "RA-101",
    type: "Pothole",
    location: "Airport Road · Zone A1",
    severity: "Critical",
    priority: 94,
    confidence: 87,
    color: "red",
    cost: 35000,
  },
  {
    id: "RA-104",
    type: "Transverse crack",
    location: "Hospital Road · Zone A2",
    severity: "Severe",
    priority: 88,
    confidence: 31,
    color: "red",
    cost: 18000,
  },
  {
    id: "RA-116",
    type: "Alligator crack",
    location: "School Road · Zone B1",
    severity: "Severe",
    priority: 85,
    confidence: 79,
    color: "red",
    cost: 27000,
  },
  {
    id: "RA-109",
    type: "Longitudinal crack",
    location: "Canal Road · Zone B2",
    severity: "Moderate",
    priority: 72,
    confidence: 27,
    color: "orange",
    cost: 14000,
  },
  {
    id: "RA-120",
    type: "Pothole",
    location: "Railway Road · Zone C1",
    severity: "Moderate",
    priority: 68,
    confidence: 74,
    color: "orange",
    cost: 16000,
  },
  {
    id: "RA-112",
    type: "Transverse crack",
    location: "Ring Road · Zone C2",
    severity: "Moderate",
    priority: 61,
    confidence: 18,
    color: "yellow",
    cost: 12000,
  },
  {
    id: "RA-124",
    type: "Longitudinal crack",
    location: "Market Road · Zone D1",
    severity: "Minor",
    priority: 44,
    confidence: 66,
    color: "green",
    cost: 8000,
  },
  {
    id: "RA-129",
    type: "Transverse crack",
    location: "Residency Road · Zone D2",
    severity: "Minor",
    priority: 39,
    confidence: 62,
    color: "green",
    cost: 6000,
  },
];

const inspectionHistory = [
  { label: "Survey 01", score: 78, date: "05 Jul" },
  { label: "Survey 02", score: 73, date: "10 Jul" },
  { label: "Survey 03", score: 68, date: "15 Jul" },
  { label: "Survey 04", score: 61, date: "20 Jul" },
  { label: "Survey 05", score: 56.7, date: "26 Jul" },
];

const routeStops = [
  { stop: "Depot", eta: "08:00", distance: "0 km" },
  { stop: "Airport Road", eta: "08:14", distance: "5.2 km" },
  { stop: "Hospital Road", eta: "08:41", distance: "3.8 km" },
  { stop: "School Road", eta: "09:12", distance: "4.1 km" },
  { stop: "Depot", eta: "10:05", distance: "6.7 km" },
];

const pipeline = [
  ["01", "Detect", "YOLOv11"],
  ["02", "Assess", "Severity"],
  ["03", "Locate", "GPS"],
  ["04", "Merge", "DBSCAN"],
  ["05", "Prioritize", "Score"],
  ["06", "Route", "Optimize"],
  ["07", "Verify", "Before / after"],
];

export default function Home() {
  const [inspection, setInspection] = useState<InspectionState>("ready");
  const [activeTab, setActiveTab] = useState<"overview" | "evidence">("overview");
  const [selectedDefect, setSelectedDefect] = useState(defects[0]);
  const [priorityFilter, setPriorityFilter] = useState<
    "all" | "urgent" | "cracks"
  >("all");
  const [routedIds, setRoutedIds] = useState<string[]>([]);

  const visibleDefects = useMemo(() => {
    if (priorityFilter === "urgent") {
      return defects.filter((defect) => defect.priority >= 80);
    }
    if (priorityFilter === "cracks") {
      return defects.filter((defect) => defect.type.toLowerCase().includes("crack"));
    }
    return defects;
  }, [priorityFilter]);

  const statusCopy = useMemo(() => {
    if (inspection === "running") return "Loading saved sample output…";
    if (inspection === "complete") return "Sample loaded · 36 observations";
    return "Validated MVP sample ready";
  }, [inspection]);

  function runInspection() {
    if (inspection === "running") return;
    setInspection("running");
    window.setTimeout(() => setInspection("complete"), 1500);
  }

  function toggleRoute(defectId: string) {
    setRoutedIds((current) =>
      current.includes(defectId)
        ? current.filter((id) => id !== defectId)
        : [...current, defectId],
    );
  }

  return (
    <main>
      <header className="topbar">
        <a className="brand" href="#top" aria-label="RoadAudit AI home">
          <span className="brandMark" aria-hidden="true">
            <i />
            <i />
          </span>
          <span>
            <strong>RoadAudit</strong> AI
          </span>
        </a>
        <nav aria-label="Primary navigation">
          <a href="#inspection">Inspection</a>
          <a href="#analytics">Analytics</a>
          <a href="#priorities">Priorities</a>
          <a href="#workflow">How it works</a>
        </nav>
        <span className="prototypeBadge">
          <i /> MVP · Round 2
        </span>
      </header>

      <section className="hero" id="top">
        <div className="heroCopy">
          <div className="eyebrow">AI ROAD ASSET INTELLIGENCE</div>
          <h1>
            From road damage
            <br />
            to <em>repair decisions.</em>
          </h1>
          <p>
            RoadAudit AI turns routine vehicle footage into an explainable
            maintenance plan—detecting defects, estimating urgency, grouping
            repeat observations, and prioritizing repair zones.
          </p>
          <div className="heroActions">
            <button className="primaryButton" onClick={runInspection}>
              <span className={inspection === "running" ? "spin" : ""}>✦</span>
              {inspection === "running"
                ? "Loading sample"
                : inspection === "complete"
                  ? "Replay sample inspection"
                  : "Run sample inspection"}
            </button>
            <a className="textLink" href="#workflow">
              View system workflow <span>→</span>
            </a>
          </div>
          <div className="heroFootnote">
            <span>YOLOv11</span>
            <i />
            <span>RDD2022</span>
            <i />
            <span>Image-based severity</span>
          </div>
        </div>

        <div className="heroVisual" aria-label="Road inspection preview">
          <div className="visualHeader">
            <span className="livePill">
              <i /> MODEL OUTPUT
            </span>
            <span>CAM-04 · SAMPLE SURVEY</span>
          </div>
          <Image
            src="/demo-frame.jpg"
            alt="Road footage annotated by the RoadAudit AI model"
            width={512}
            height={512}
          />
          <div className="scanLine" />
          <div className="visualFooter">
            <div>
              <span>Road health</span>
              <strong>56.7</strong>
              <small>/ 100</small>
            </div>
            <div>
              <span>Observations</span>
              <strong>{inspection === "complete" ? "36" : "—"}</strong>
            </div>
            <div>
              <span>Top urgency</span>
              <strong className="urgent">88</strong>
              <small>/ 100</small>
            </div>
          </div>
        </div>
      </section>

      <section className="metricStrip" aria-label="Inspection summary">
        <div>
          <span>01</span>
          <p>Routine footage</p>
          <strong>No new road hardware</strong>
        </div>
        <div>
          <span>02</span>
          <p>Four damage classes</p>
          <strong>Cracks + potholes</strong>
        </div>
        <div>
          <span>03</span>
          <p>Explainable scoring</p>
          <strong>Severity → priority</strong>
        </div>
        <div>
          <span>04</span>
          <p>Closed-loop workflow</p>
          <strong>Detect → verify</strong>
        </div>
      </section>

      <section className="dashboardSection" id="inspection">
        <div className="sectionHeading">
          <div>
            <span className="sectionNumber">01 / SAMPLE MVP</span>
            <h2>Inspection command center</h2>
          </div>
          <div className={`runStatus ${inspection}`}>
            <i />
            {statusCopy}
          </div>
        </div>

        <div className="dashboardGrid">
          <article className="panel evidencePanel">
            <div className="panelHeader">
              <div>
                <span className="panelKicker">FIELD EVIDENCE</span>
                <h3>Annotated road survey</h3>
              </div>
              <div className="tabs" role="tablist" aria-label="Evidence view">
                <button
                  className={activeTab === "overview" ? "active" : ""}
                  onClick={() => setActiveTab("overview")}
                >
                  Frame
                </button>
                <button
                  className={activeTab === "evidence" ? "active" : ""}
                  onClick={() => setActiveTab("evidence")}
                >
                  Video
                </button>
              </div>
            </div>
            {activeTab === "overview" ? (
              <div className="evidenceImage">
                <Image src="/demo-frame.jpg" alt="Annotated inspection frame" width={512} height={512} />
                <span className="frameStamp">FRAME 000 · 00:00.0</span>
              </div>
            ) : (
              <video
                className="evidenceVideo"
                controls
                muted
                playsInline
                src="/demo-video.mp4"
              >
                Your browser does not support embedded video.
              </video>
            )}
            <div className="evidenceMeta">
              <span>4 sampled frames</span>
              <span>36 raw observations</span>
              <span>0.31 max confidence</span>
              <span>CPU inference</span>
            </div>
          </article>

          <article className="panel healthPanel">
            <div className="panelHeader">
              <div>
                <span className="panelKicker">ROAD HEALTH INDEX</span>
                <h3>Maintenance needed</h3>
              </div>
              <span className="trend">↓ 43.3 pts</span>
            </div>
            <div className="healthGauge" aria-label="Road health score 56.7 out of 100">
              <div className="gaugeRing">
                <div>
                  <strong>56.7</strong>
                  <span>/ 100</span>
                </div>
              </div>
            </div>
            <div className="healthLegend">
              <span><i className="critical" />Critical</span>
              <span><i className="watch" />Watch</span>
              <span><i className="healthy" />Healthy</span>
            </div>
            <p className="modelNote">
              <strong>MVP interpretation:</strong> heuristic score based on
              detected class, visible area, and confidence—not a civil
              engineering measurement.
            </p>
          </article>

          <article className="panel mapPanel">
            <div className="panelHeader">
              <div>
                <span className="panelKicker">DECISION LAYER · SIMULATED GPS</span>
                <h3>Repair zones</h3>
              </div>
              <div className="mapCallout">
                <span>{selectedDefect.id} · SELECTED ZONE</span>
                <strong>{selectedDefect.location}</strong>
                <small>
                  Priority {selectedDefect.priority} · {selectedDefect.severity}
                  {" · "}₹{selectedDefect.cost.toLocaleString("en-IN")}
                </small>
              </div>
            </div>
            <div className="mapCanvas">
              <div className="road roadA" />
              <div className="road roadB" />
              <div className="road roadC" />
              <div className="routeLine routeA" />
              <div className="routeLine routeB" />
              {defects.map((defect, index) => (
                <button
                  key={defect.id}
                  className={`mapPin pin${index + 1} ${selectedDefect.id === defect.id ? "selected" : ""}`}
                  onClick={() => setSelectedDefect(defect)}
                  aria-label={`Select ${defect.location}`}
                >
                  {index + 1}
                </button>
              ))}
              <span className="mapLabel labelA">HOSPITAL RD</span>
              <span className="mapLabel labelB">CANAL RD</span>
              <span className="mapLabel labelC">RING RD</span>
            </div>
          </article>
        </div>
      </section>

      <section className="analyticsSection" id="analytics">
        <div className="sectionHeading">
          <div>
            <span className="sectionNumber">02 / ANALYTICS</span>
            <h2>Turn observations into a maintenance brief</h2>
          </div>
          <p>
            Model evidence is kept separate from simulated GPS, traffic, cost,
            and inspection-history context used to demonstrate the decision
            workflow.
          </p>
        </div>

        <div className="analyticsMetrics">
          <article>
            <span>Survey coverage</span>
            <strong>12.4 <small>km</small></strong>
            <p>3 municipal corridors</p>
          </article>
          <article>
            <span>Unique repair zones</span>
            <strong>8</strong>
            <p>36 raw model observations</p>
          </article>
          <article>
            <span>Urgent zones</span>
            <strong>3</strong>
            <p>Priority score ≥ 80</p>
          </article>
          <article>
            <span>Estimated budget</span>
            <strong>₹1.36 <small>lakh</small></strong>
            <p>Planning estimate only</p>
          </article>
          <article>
            <span>Optimized route</span>
            <strong>19.8 <small>km</small></strong>
            <p>4 stops · 2 h 05 min</p>
          </article>
        </div>

        <div className="analyticsGrid">
          <article className="dataCard typeCard">
            <div className="dataCardHeader">
              <div>
                <span className="panelKicker">ACTUAL SAMPLE OUTPUT</span>
                <h3>Observation distribution</h3>
              </div>
              <span className="dataChip">36 observations</span>
            </div>
            <div className="barChart" aria-label="Damage type distribution">
              <div>
                <span>Transverse crack</span>
                <i><b style={{ width: "67%" }} /></i>
                <strong>24</strong>
              </div>
              <div>
                <span>Longitudinal crack</span>
                <i><b style={{ width: "33%" }} /></i>
                <strong>12</strong>
              </div>
              <div className="mutedBar">
                <span>Alligator crack</span>
                <i><b style={{ width: "0%" }} /></i>
                <strong>0</strong>
              </div>
              <div className="mutedBar">
                <span>Pothole</span>
                <i><b style={{ width: "0%" }} /></i>
                <strong>0</strong>
              </div>
            </div>
            <p className="cardFootnote">
              These counts come from the bundled 4-frame video test at a 0.05
              confidence threshold.
            </p>
          </article>

          <article className="dataCard historyCard">
            <div className="dataCardHeader">
              <div>
                <span className="panelKicker">ILLUSTRATIVE HISTORY</span>
                <h3>Road Health Index trend</h3>
              </div>
              <span className="negativeChip">−21.3 pts</span>
            </div>
            <div className="trendChart" aria-label="Illustrative road health trend">
              <div className="trendGrid">
                <span>100</span><span>75</span><span>50</span><span>25</span>
              </div>
              <div className="trendBars">
                {inspectionHistory.map((survey) => (
                  <div key={survey.label}>
                    <b style={{ height: `${survey.score}%` }}>
                      <i>{survey.score}</i>
                    </b>
                    <span>{survey.date}</span>
                  </div>
                ))}
              </div>
            </div>
          </article>

          <article className="dataCard routeCard">
            <div className="dataCardHeader">
              <div>
                <span className="panelKicker">REPAIR ROUTE</span>
                <h3>Priority-first schedule</h3>
              </div>
              <span className="dataChip">19.8 km</span>
            </div>
            <div className="routeTimeline">
              {routeStops.map((item, index) => (
                <div key={`${item.stop}-${item.eta}`}>
                  <span className="stopNode">{index + 1}</span>
                  <p><strong>{item.stop}</strong><small>{item.distance}</small></p>
                  <time>{item.eta}</time>
                </div>
              ))}
            </div>
          </article>

          <article className="dataCard modelCard">
            <div className="dataCardHeader">
              <div>
                <span className="panelKicker">MODEL CARD · 3-EPOCH CPU MVP</span>
                <h3>Validation performance</h3>
              </div>
              <span className="warningChip">Prototype</span>
            </div>
            <div className="modelMetrics">
              <div><span>Precision</span><strong>0.349</strong></div>
              <div><span>Recall</span><strong>0.086</strong></div>
              <div><span>mAP50</span><strong>0.047</strong></div>
              <div><span>mAP50–95</span><strong>0.013</strong></div>
            </div>
            <p className="modelDisclosure">
              The model validates the end-to-end pipeline, not production
              accuracy. Full-data GPU training and field calibration are the
              next technical milestones.
            </p>
          </article>

          <article className="dataCard thresholdCard">
            <div className="dataCardHeader">
              <div>
                <span className="panelKicker">ACTUAL 12-FRAME CPU TEST</span>
                <h3>Confidence-threshold sensitivity</h3>
              </div>
              <span className="dataChip">27 Jul · validated</span>
            </div>
            <div className="thresholdMatrix">
              <div>
                <span>0.05 confidence</span>
                <strong>108</strong>
                <small>72 transverse · 36 longitudinal</small>
                <i><b style={{ width: "100%" }} /></i>
              </div>
              <div>
                <span>0.10 confidence</span>
                <strong>84</strong>
                <small>60 transverse · 24 longitudinal</small>
                <i><b style={{ width: "78%" }} /></i>
              </div>
              <div>
                <span>0.25 confidence</span>
                <strong>24</strong>
                <small>12 transverse · 12 longitudinal</small>
                <i><b style={{ width: "22%" }} /></i>
              </div>
              <div>
                <span>0.50 confidence</span>
                <strong>0</strong>
                <small>No detections above threshold</small>
                <i><b style={{ width: "0%" }} /></i>
              </div>
            </div>
            <div className="thresholdFoot">
              <span>12 frames per run</span>
              <span>4.66 s average CPU runtime</span>
              <span>0.307 maximum confidence</span>
              <span>Alligator / pothole: 0 in sample</span>
            </div>
          </article>
        </div>
      </section>

      <section className="prioritySection" id="priorities">
        <div className="sectionHeading">
          <div>
            <span className="sectionNumber">03 / ACTION PLAN</span>
            <h2>Repair what matters first</h2>
          </div>
          <p>
            A transparent score combines visible severity with simulated road
            importance and traffic context.
          </p>
        </div>

        <div className="priorityLayout">
          <div>
            <div className="filterBar" aria-label="Priority filters">
              <button
                className={priorityFilter === "all" ? "active" : ""}
                onClick={() => setPriorityFilter("all")}
              >
                All zones <span>8</span>
              </button>
              <button
                className={priorityFilter === "urgent" ? "active" : ""}
                onClick={() => setPriorityFilter("urgent")}
              >
                Urgent <span>3</span>
              </button>
              <button
                className={priorityFilter === "cracks" ? "active" : ""}
                onClick={() => setPriorityFilter("cracks")}
              >
                Cracks <span>6</span>
              </button>
            </div>
            <div className="priorityList">
            {visibleDefects.map((defect) => (
              <button
                className={`priorityRow ${selectedDefect.id === defect.id ? "selected" : ""}`}
                key={defect.id}
                onClick={() => setSelectedDefect(defect)}
              >
                <span className="rank">
                  {String(defects.findIndex((item) => item.id === defect.id) + 1).padStart(2, "0")}
                </span>
                <span className={`severityDot ${defect.color}`} />
                <span className="defectName">
                  <strong>{defect.location}</strong>
                  <small>{defect.type} · {defect.severity}</small>
                </span>
                <span className="priorityBar">
                  <i style={{ width: `${defect.priority}%` }} />
                </span>
                <span className="score">{defect.priority}</span>
                <span className="arrow">→</span>
              </button>
            ))}
            </div>
          </div>
          <aside className="whyCard">
            <span className="panelKicker">WHY THIS RANKS #{defects.findIndex((item) => item.id === selectedDefect.id) + 1}</span>
            <h3>{selectedDefect.location}</h3>
            <div className="scoreHero">
              <strong>{selectedDefect.priority}</strong>
              <span>/ 100 priority</span>
            </div>
            <ul>
              <li><span>Visible severity</span><strong>{selectedDefect.severity}</strong></li>
              <li><span>Critical-route weight</span><strong>High</strong></li>
              <li><span>Nearby observations</span><strong>Multiple</strong></li>
              <li><span>Repair status</span><strong>Unresolved</strong></li>
            </ul>
            <button
              className={`routeButton ${routedIds.includes(selectedDefect.id) ? "added" : ""}`}
              aria-pressed={routedIds.includes(selectedDefect.id)}
              onClick={() => toggleRoute(selectedDefect.id)}
            >
              {routedIds.includes(selectedDefect.id)
                ? "Added to repair route"
                : "Add to repair route"}
              <span>{routedIds.includes(selectedDefect.id) ? "✓" : "↗"}</span>
            </button>
          </aside>
        </div>
      </section>

      <section className="workflowSection" id="workflow">
        <div className="workflowIntro">
          <span className="sectionNumber">04 / SYSTEM WORKFLOW</span>
          <h2>Detection is only the first step.</h2>
          <p>
            The value of RoadAudit AI is the complete maintenance loop:
            inspection, decision, action, and accountability.
          </p>
        </div>
        <div className="pipeline">
          {pipeline.map(([number, title, detail], index) => (
            <div className="pipelineStep" key={number}>
              <span>{number}</span>
              <strong>{title}</strong>
              <small>{detail}</small>
              {index < pipeline.length - 1 && <i>→</i>}
            </div>
          ))}
        </div>
        <div className="impactBanner">
          <div>
            <span>THE OUTCOME</span>
            <h3>Safer roads. Faster decisions. Verifiable repairs.</h3>
          </div>
          <p>
            Built for municipal corporations, PWD teams, smart-city programs,
            highway authorities, and maintenance contractors.
          </p>
        </div>
      </section>

      <footer>
        <a className="brand footerBrand" href="#top">
          <span className="brandMark" aria-hidden="true"><i /><i /></span>
          <span><strong>RoadAudit</strong> AI</span>
        </a>
        <p>From road damage detection to repair accountability.</p>
        <span>AI First Hackathon · Summer School ’26</span>
      </footer>
    </main>
  );
}
