import React, { useState, useEffect, useCallback } from "react";
import { Container, Row, Col, Spinner, Alert } from "react-bootstrap";
import { Link } from "react-router-dom";
import { fetchClaims } from "../services/claimsService";

import WebGISMap from "../components/WebGISMap";
import DashboardStats from "../components/DashboardStats";
import "./DashboardPage.css";
import "../components/DashboardStats.css";

const SYNTHETIC_DATASET_SIZE = 125000;
const DASHBOARD_MAP_SAMPLE = 2500;

function DashboardPage() {
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadClaims = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      // Display sample only — Leaflet cannot comfortably render 125k markers.
      // The full 125,000-row CSV is used for LightGBM training (not this map sample).
      const data = await fetchClaims({
        source: "all",
        limit: DASHBOARD_MAP_SAMPLE,
      });
      setClaims(data);
    } catch (err) {
      setError(err.message || "Failed to fetch claims from the API.");
      console.error("Error fetching claims:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadClaims();
  }, [loadClaims]);

  const stats = {
    totalClaims: claims.length,
    claimsInReview: claims.filter((c) => c.status === "Pending").length,
    claimsApproved: claims.filter((c) => c.status === "Approved").length,
  };

  return (
    <div className="dashboard-page">
      <Container fluid>
        <div className="page-header">
          <h1 className="page-title">Claims Dashboard</h1>
          <p className="page-subtitle">
            Atlas overview of digitized FRA claims across focus states.
          </p>
          <div className="page-meta">
            <span className="meta-chip">
              {claims.length.toLocaleString("en-IN")} map sample
            </span>
            <span className="meta-chip">
              {SYNTHETIC_DATASET_SIZE.toLocaleString("en-IN")} in full synthetic
              set
            </span>
            <span className="meta-chip">WebGIS live map</span>
          </div>
        </div>

        {error && <Alert variant="danger">{error}</Alert>}

        {!loading && !error && (
          <Alert variant="info" className="mb-3">
            Showing a <strong>{DASHBOARD_MAP_SAMPLE.toLocaleString("en-IN")}</strong>
            -row <em>display sample</em> so the map stays responsive. The ML model
            was trained on the <strong>full{" "}
            {SYNTHETIC_DATASET_SIZE.toLocaleString("en-IN")}</strong> synthetic
            claims (not this sample). Open{" "}
            <Link to="/claims-data">Claims</Link> and use{" "}
            <strong>Load all synthetic</strong> for the complete ledger, or{" "}
            <Link to="/dss">DSS</Link> for priority / scheme views.
          </Alert>
        )}

        {loading ? (
          <div className="spinner-container">
            <Spinner animation="border" role="status">
              <span className="visually-hidden">Loading Dashboard...</span>
            </Spinner>
            <p className="loading-hint">
              Loading claims from the API… first load can take a minute on free
              hosting.
            </p>
          </div>
        ) : (
          <>
            <DashboardStats stats={stats} />
            <Row className="g-3">
              <Col lg={8}>
                <div className="map-panel">
                  <div className="map-panel-header">
                    <h2>Geographic Atlas</h2>
                    <span>Claim locations on the map</span>
                  </div>
                  <div className="map-panel-body">
                    <WebGISMap claims={claims} />
                  </div>
                </div>
              </Col>
              <Col lg={4}>
                <div className="side-panel">
                  <h2>Next step</h2>
                  <p>
                    Add claims from the ledger, or connect the OCR API for
                    document digitization.
                  </p>
                  <Link to="/claims-data" className="btn btn-primary">
                    Open Claims Ledger
                  </Link>
                </div>
              </Col>
            </Row>
          </>
        )}
      </Container>
    </div>
  );
}

export default DashboardPage;
