import React, { useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Diagram3,
  GeoAlt,
  Cpu,
  BarChartSteps,
  Bullseye,
  People,
  JournalText,
  Lightbulb,
  Database,
  ArrowRight,
} from "react-bootstrap-icons";
import "./EPosterPage.css";

function EPosterPage() {
  useEffect(() => {
    document.body.classList.add("e-poster-mode");
    return () => document.body.classList.remove("e-poster-mode");
  }, []);

  return (
    <div className="e-poster-shell">
      <div className="e-poster-toolbar no-print">
        <span>
          Screenshot tip: zoom browser so the full poster fits, then capture this
          frame. Navbar/footer are hidden on this route.
        </span>
        <Link to="/" className="e-poster-back">
          ← Back to app
        </Link>
      </div>

      <article className="e-poster" id="e-poster-capture">
        <header className="ep-header">
          <div className="ep-header-top">
            <div className="ep-inst">
              <strong>MIT World Peace University</strong>
              <span>
                B.Tech CSE · Artificial Intelligence &amp; Data Science
              </span>
            </div>
            <div className="ep-badge">ML Project · E-Poster</div>
          </div>
          <h1>AI-Powered FRA Atlas</h1>
          <p className="ep-subtitle">
            WebGIS-based Decision Support System (DSS) for Integrated Monitoring
            of Forest Rights Act (FRA) Implementation
          </p>
          <div className="ep-focus">
            <GeoAlt size={14} />
            Focus states: Madhya Pradesh · Tripura · Odisha · Telangana
          </div>
          <div className="ep-meta-row">
            <div className="ep-person">
              <span className="ep-role">Team Representative</span>
              <strong>Aryan Dani</strong>
              <span>PRN 1272250888</span>
            </div>
            <div className="ep-person">
              <span className="ep-role">Team Member</span>
              <strong>M. Sobaan Jagirdar</strong>
              <span>PRN 1272250891</span>
            </div>
            <div className="ep-person">
              <span className="ep-role">Guide</span>
              <strong>Jayshree Aher</strong>
              <span>Faculty Mentor</span>
            </div>
          </div>
        </header>

        <div className="ep-grid">
          {/* Problem */}
          <section className="ep-card ep-problem">
            <div className="ep-card-head">
              <Bullseye />
              <h2>1. Problem Statement</h2>
            </div>
            <p>
              FRA 2006 recognizes rights of Scheduled Tribes &amp; OTFDs, but
              claim processing is fragmented across Gram Sabha → SDLC → DLC,
              uneven across states, and hard to monitor centrally.
            </p>
            <div className="ep-chips">
              <span>No unified claim + forest GIS view</span>
              <span>Backlogs &amp; rejection disparities</span>
              <span>Need AI-assisted DSS for MoTA / officials</span>
            </div>
          </section>

          {/* Objectives */}
          <section className="ep-card ep-objectives">
            <div className="ep-card-head">
              <BarChartSteps />
              <h2>2. Objectives</h2>
            </div>
            <ol className="ep-obj-list">
              <li>
                <strong>Monitor</strong> IFR / CR / CFR claims across 4 states
              </li>
              <li>
                <strong>Predict</strong> claim outcome (Approved / Rejected /
                Pending)
              </li>
              <li>
                <strong>WebGIS DSS</strong> — backlog &amp; forest layers
              </li>
              <li>
                <strong>Find bottlenecks</strong> — delays, rejection patterns
              </li>
              <li>
                <strong>Extensible</strong> for future satellite verification
              </li>
            </ol>
            <div className="ep-obj-visual" aria-hidden="true">
              <span>Docs</span>
              <ArrowRight />
              <span>XGBoost</span>
              <ArrowRight />
              <span>SHAP</span>
              <ArrowRight />
              <span>DSS map</span>
            </div>
          </section>

          {/* Motivation */}
          <section className="ep-card ep-motivation">
            <div className="ep-card-head">
              <Lightbulb />
              <h2>Motivation</h2>
            </div>
            <div className="ep-two-col">
              <div className="ep-pill-block">
                <strong>Social equity</strong>
                <p>Timely, fair FRA processing for tribal &amp; forest communities</p>
              </div>
              <div className="ep-pill-block">
                <strong>Sustainability</strong>
                <p>CFR tenure security supports conservation outcomes</p>
              </div>
            </div>
            <div className="ep-sdg">
              <span>SDG 10 Reduced Inequalities</span>
              <span>SDG 15 Life on Land</span>
              <span>MoTA digitization</span>
            </div>
          </section>

          {/* Literature */}
          <section className="ep-card ep-lit">
            <div className="ep-card-head">
              <JournalText />
              <h2>3. Literature Analysis</h2>
            </div>
            <div className="ep-lit-grid">
              <article>
                <h3>FRA + WebGIS DSS</h3>
                <p>
                  Manimegala et al. (IJIRT) — AI FRA Atlas with OCR/NER, asset
                  mapping &amp; scheme DSS for fragmented FRA records.
                </p>
              </article>
              <article>
                <h3>LULC · Sentinel-2 · ML</h3>
                <p>
                  Shah et al. — Kolhapur LULC (RF 94.2%). IRUNet ensemble on
                  multi-year S2 (≈98%). Hy-DNN on GEE (S2 97.6%).
                </p>
              </article>
              <article>
                <h3>Datasets</h3>
                <p>
                  Sentinel2GlobalLULC — 194k S2 RGB tiles, 29 classes for DL
                  LULC training (Sci Data).
                </p>
              </article>
              <article>
                <h3>Explainable ML</h3>
                <p>
                  Ergün (2023) &amp; TreeSHAP — SHAP for XGBoost feature
                  attribution; critical for government-facing DSS trust.
                </p>
              </article>
              <article>
                <h3>Forest change · GIS</h3>
                <p>
                  Kodagu / Western Ghats encroachment studies show RS+GIS can
                  evidence historical forest change for verification layers.
                </p>
              </article>
              <article>
                <h3>Gap → Our work</h3>
                <p>
                  Prior work covers LULC or FRA portals separately — few fuse
                  calibrated claim ML + WebGIS priority DSS for four focus
                  states.
                </p>
              </article>
            </div>
          </section>

          {/* Dataset */}
          <section className="ep-card ep-data">
            <div className="ep-card-head">
              <Database />
              <h2>4. Dataset</h2>
            </div>
            <p className="ep-note">
              Parcel-level FRA claims are not public →{" "}
              <strong>synthetic claims calibrated</strong> to real MoTA /
              data.gov.in aggregates (2019–2024).
            </p>
            <div className="ep-schema">
              {[
                "claim_id",
                "state / district / village",
                "lat / lon",
                "IFR · CR · CFR",
                "ST / OTFD",
                "docs complete?",
                "committee level",
                "status",
                "rejection_reason",
              ].map((f) => (
                <span key={f}>{f}</span>
              ))}
            </div>
            <div className="ep-sources">
              <span>data.gov.in</span>
              <span>MoTA reports</span>
              <span>State FRA atlases</span>
              <span>ATREE CFR potential</span>
            </div>
          </section>

          {/* Methodology flow */}
          <section className="ep-card ep-method">
            <div className="ep-card-head">
              <Diagram3 />
              <h2>5. Methodology</h2>
            </div>
            <div className="ep-flow">
              {[
                { n: "01", t: "Real stats table", d: "State × year FRA totals" },
                { n: "02", t: "Village geo", d: "Real coords for WebGIS" },
                { n: "03", t: "Synthesize", d: "Match published volumes" },
                { n: "04", t: "Outcomes", d: "Rate + feature logistics" },
                { n: "05", t: "Validate", d: "Re-aggregate vs MoTA" },
                { n: "06", t: "Train ML", d: "Outcome prediction" },
                { n: "07", t: "DSS UI", d: "Map + priority views" },
              ].map((s) => (
                <div className="ep-step" key={s.n}>
                  <span className="ep-step-n">{s.n}</span>
                  <strong>{s.t}</strong>
                  <small>{s.d}</small>
                </div>
              ))}
            </div>

            <div className="ep-focus-stats">
              <div className="ep-focus-stats-head">
                <svg
                  className="ep-tree-icon"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    fill="currentColor"
                    d="M12 2L8 8h2L7 13h2l-3 6h12l-3-6h2l-3-5h2L12 2zm-1 18v2h2v-2h-2z"
                  />
                </svg>
                <span>Focus-state MoTA snapshot (June 2024) · claims → titles</span>
              </div>
              <div className="ep-focus-stats-row">
                {[
                  { state: "Madhya Pradesh", claims: "6.28L", titles: "2.95L" },
                  { state: "Odisha", claims: "6.76L", titles: "4.68L" },
                  { state: "Telangana", claims: "6.55L", titles: "2.31L" },
                  { state: "Tripura", claims: "2.01L", titles: "1.28L" },
                ].map((s) => (
                  <div className="ep-stat-pill" key={s.state}>
                    <span className="ep-stat-state">{s.state}</span>
                    <span className="ep-stat-nums">
                      <strong>{s.claims}</strong>
                      <span className="ep-stat-arrow">→</span>
                      <em>{s.titles}</em>
                    </span>
                    <span className="ep-stat-labels">received · titled</span>
                  </div>
                ))}
              </div>
              <div className="ep-forest-band" aria-hidden="true">
                <svg viewBox="0 0 720 48" preserveAspectRatio="none">
                  <path
                    fill="#0d2b24"
                    d="M0 48 V28 L18 8 36 28 48 14 64 30 78 6 96 28 110 16 128 32 142 10 160 30 176 18 192 34 208 12 228 30 246 8 264 28 280 16 300 34 318 10 336 28 352 14 372 32 390 6 410 28 428 16 448 34 466 10 486 30 504 14 524 32 542 8 560 28 578 18 598 34 616 12 636 30 654 8 674 28 692 16 720 32 V48 Z"
                  />
                  <path
                    fill="#1b5e4a"
                    opacity="0.85"
                    d="M0 48 V34 L22 18 40 34 58 22 76 36 94 14 118 34 140 20 162 36 184 16 208 34 230 22 254 36 276 14 300 34 324 20 348 36 370 16 396 34 420 22 444 36 468 14 492 34 516 20 540 36 564 16 588 34 612 22 636 36 660 14 684 34 708 22 720 34 V48 Z"
                  />
                  <path
                    fill="#2e7d32"
                    opacity="0.7"
                    d="M0 48 V40 L30 28 55 40 80 30 110 42 140 28 170 40 200 30 235 42 270 28 305 40 340 30 375 42 410 28 445 40 480 30 515 42 550 28 585 40 620 30 655 42 690 28 720 40 V48 Z"
                  />
                </svg>
              </div>
            </div>
          </section>

          {/* Techniques */}
          <section className="ep-card ep-tech">
            <div className="ep-card-head">
              <Cpu />
              <h2>6. Techniques &amp; Algorithms</h2>
            </div>
            <div className="ep-tech-row">
              <div>
                <h3>Claim outcome</h3>
                <ul>
                  <li>XGBoost / LightGBM (primary)</li>
                  <li>Logistic Regression (baseline)</li>
                  <li>Class weights · reject-class recall</li>
                  <li>SHAP explanations per claim</li>
                </ul>
              </div>
              <div>
                <h3>DSS aggregation</h3>
                <ul>
                  <li>Village / district priority score</li>
                  <li>Backlog size · processing time</li>
                  <li>Rejection-rate trend</li>
                </ul>
              </div>
              <div>
                <h3>Future (scoped out)</h3>
                <ul>
                  <li>Sentinel-2 / Landsat via GEE</li>
                  <li>RF · SVM · U-Net cover maps</li>
                  <li>Post-approval CFR monitoring</li>
                </ul>
              </div>
            </div>
          </section>

          {/* Contributions */}
          <section className="ep-card ep-contrib">
            <div className="ep-card-head">
              <People />
              <h2>7. Contributions</h2>
            </div>
            <div className="ep-contrib-grid">
              <div>
                <strong>Aryan Dani</strong>
                <ul>
                  <li>Frontend (React WebGIS FRA Atlas)</li>
                  <li>GIS map hosting &amp; visualization</li>
                  <li>Website / deployment (Vercel + API)</li>
                </ul>
                <a
                  href="https://fra-atlas-one.vercel.app"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  fra-atlas-one.vercel.app
                </a>
              </div>
              <div>
                <strong>M. Sobaan Jagirdar</strong>
                <ul>
                  <li>Literature survey &amp; documentation</li>
                  <li>Data preprocessing &amp; schema design</li>
                  <li>ML methodology support (early phase)</li>
                </ul>
              </div>
            </div>
            <p className="ep-status">
              Status: prototype WebGIS live · synthetic ML pipeline in progress
            </p>
          </section>

          {/* Expected outcomes */}
          <section className="ep-card ep-outcomes">
            <div className="ep-card-head">
              <Bullseye />
              <h2>8. Expected Outcomes</h2>
            </div>
            <div className="ep-outcome-pills">
              <span>Unified 4-state claim monitoring dashboard</span>
              <span>Interpretable outcome risk scores (SHAP)</span>
              <span>Priority maps of backlog hotspots</span>
              <span>Actionable rejection / delay insights</span>
              <span>Architecture ready for satellite CFR checks</span>
            </div>
          </section>
        </div>

        <footer className="ep-footer">
          <span>AI-Powered FRA Atlas · MIT-WPU · B.Tech CSE (AI &amp; DS)</span>
          <span>Guide: Jayshree Aher · Team: Aryan Dani · M. Sobaan Jagirdar</span>
        </footer>
      </article>
    </div>
  );
}

export default EPosterPage;
