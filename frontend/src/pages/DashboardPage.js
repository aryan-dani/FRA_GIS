import React, { useState, useEffect, useCallback } from "react";
import { Container, Row, Col, Spinner, Alert } from "react-bootstrap";
import { Link } from "react-router-dom";
import { fetchClaims } from "../services/claimsService";

import WebGISMap from "../components/WebGISMap";
import DashboardStats from "../components/DashboardStats";
import "./DashboardPage.css";
import "../components/DashboardStats.css";

function DashboardPage() {
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadClaims = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchClaims();
      setClaims(data);
    } catch (err) {
      setError("Failed to fetch claims from Firebase.");
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
            <span className="meta-chip">{claims.length} records</span>
            <span className="meta-chip">WebGIS live map</span>
          </div>
        </div>

        {error && <Alert variant="danger">{error}</Alert>}

        {loading ? (
          <div className="spinner-container">
            <Spinner animation="border" role="status">
              <span className="visually-hidden">Loading Dashboard...</span>
            </Spinner>
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
