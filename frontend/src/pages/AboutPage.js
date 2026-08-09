import React from "react";
import { Container, Row, Col } from "react-bootstrap";
import "./AboutPage.css";

const FOCUS_STATES = [
  "Madhya Pradesh",
  "Tripura",
  "Odisha",
  "Telangana",
];

function AboutPage() {
  return (
    <div className="about-page">
      <Container className="py-4 py-md-5">
        <div className="page-header">
          <h1 className="page-title">About the Platform</h1>
          <p className="page-subtitle">
            AI-powered FRA Atlas and WebGIS Decision Support System for Forest
            Rights Act monitoring.
          </p>
          <div className="page-meta">
            <span className="meta-chip">SIH12508</span>
            <span className="meta-chip">Ministry of Tribal Affairs</span>
            <span className="meta-chip">Software · SIH 2025</span>
          </div>
        </div>

        <Row className="g-4">
          <Col lg={7}>
            <article className="about-panel rise-in">
              <h2>Problem Statement</h2>
              <p className="problem-title">
                Development of AI-powered FRA Atlas and WebGIS-based Decision
                Support System (DSS) for Integrated Monitoring of Forest Rights
                Act (FRA) Implementation.
              </p>
              <p>
                The platform supports integrated monitoring of Individual Forest
                Rights (IFR), Community Rights (CR), and Community Forest
                Resource (CFR) rights — aligned with MoTA’s roadmap for
                digitization, geotagging, and convergence of FRA records.
              </p>
              <dl className="about-meta-list">
                <div>
                  <dt>Problem ID</dt>
                  <dd>SIH12508</dd>
                </div>
                <div>
                  <dt>Organization</dt>
                  <dd>Ministry of Tribal Affairs (MoTA)</dd>
                </div>
                <div>
                  <dt>Category</dt>
                  <dd>Software</dd>
                </div>
                <div>
                  <dt>Theme</dt>
                  <dd>Miscellaneous</dd>
                </div>
              </dl>
            </article>
          </Col>

          <Col lg={5}>
            <article className="about-panel rise-in rise-in-delay-1">
              <h2>Focus States</h2>
              <p>
                Priority concentration states for the SIH solution prototype:
              </p>
              <ul className="state-list">
                {FOCUS_STATES.map((state) => (
                  <li key={state}>{state}</li>
                ))}
              </ul>
            </article>

            <article className="about-panel rise-in rise-in-delay-2 mt-4">
              <h2>Stack</h2>
              <ul className="stack-list">
                <li>
                  <strong>Frontend</strong> React · Leaflet WebGIS
                </li>
                <li>
                  <strong>Backend</strong> Flask · OCR / NER pipeline
                </li>
                <li>
                  <strong>Database</strong> Firebase Firestore
                </li>
                <li>
                  <strong>AI / OCR</strong> Google Vision · Tesseract · spaCy
                </li>
              </ul>
            </article>
          </Col>
        </Row>

        <p className="about-credit">
          Prototype by{" "}
          <a
            className="developer-name"
            href="https://www.aryandani.com"
            target="_blank"
            rel="noopener noreferrer"
          >
            Aryan Dani
          </a>
        </p>
      </Container>
    </div>
  );
}

export default AboutPage;
