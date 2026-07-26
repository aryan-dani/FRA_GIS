import React from "react";
import { Container } from "react-bootstrap";
import { Link } from "react-router-dom";
import { ArrowRight, Map, Table, BarChartLine } from "react-bootstrap-icons";
import "./HomePage.css";

function HomePage() {
  return (
    <div className="homepage">
      <section className="hero" aria-label="FRA Atlas hero">
        <div className="hero-visual" aria-hidden="true">
          <svg className="hero-silhouette" viewBox="0 0 1440 520" preserveAspectRatio="xMidYMax slice">
            <path
              fill="rgba(12,47,36,0.55)"
              d="M0,360 L120,300 L240,340 L360,250 L480,320 L600,220 L720,300 L840,180 L960,280 L1080,200 L1200,290 L1320,240 L1440,300 L1440,520 L0,520 Z"
            />
            <path
              fill="rgba(26,77,58,0.65)"
              d="M0,400 L160,350 L320,390 L480,320 L640,380 L800,300 L960,370 L1120,310 L1280,360 L1440,330 L1440,520 L0,520 Z"
            />
            <path
              fill="rgba(201,162,39,0.18)"
              d="M0,450 L200,420 L400,445 L600,410 L800,440 L1000,405 L1200,435 L1440,415 L1440,520 L0,520 Z"
            />
          </svg>
        </div>

        <Container className="hero-content">
          <p className="hero-brand rise-in">FRA Atlas</p>
          <h1 className="hero-headline rise-in rise-in-delay-1">
            WebGIS for Forest Rights
          </h1>
          <p className="hero-support rise-in rise-in-delay-2">
            Digitize, map, and monitor IFR, CR, and CFR claims across Madhya
            Pradesh, Tripura, Odisha, and Telangana.
          </p>
          <div className="hero-actions rise-in rise-in-delay-3">
            <Link to="/dashboard" className="btn btn-primary hero-cta">
              Open Atlas <ArrowRight className="ms-2" />
            </Link>
            <Link to="/claims-data" className="btn btn-outline-light hero-cta-secondary">
              Browse Claims
            </Link>
          </div>
          <p className="hero-sih rise-in rise-in-delay-3">
            SIH12508 · Ministry of Tribal Affairs
          </p>
        </Container>
      </section>

      <section className="workspace-section">
        <Container>
          <div className="section-intro">
            <h2>Workspaces</h2>
            <p>Move between the atlas map, claims ledger, and analytics.</p>
          </div>
          <div className="workspace-grid">
            <Link to="/dashboard" className="workspace-link rise-in">
              <Map size={22} />
              <div>
                <strong>Dashboard</strong>
                <span>Geographic claim atlas</span>
              </div>
              <ArrowRight className="workspace-arrow" />
            </Link>
            <Link to="/claims-data" className="workspace-link rise-in rise-in-delay-1">
              <Table size={22} />
              <div>
                <strong>Claims Data</strong>
                <span>Search, filter, update status</span>
              </div>
              <ArrowRight className="workspace-arrow" />
            </Link>
            <Link to="/analytics" className="workspace-link rise-in rise-in-delay-2">
              <BarChartLine size={22} />
              <div>
                <strong>Analytics</strong>
                <span>Trends by status and region</span>
              </div>
              <ArrowRight className="workspace-arrow" />
            </Link>
          </div>
        </Container>
      </section>
    </div>
  );
}

export default HomePage;
