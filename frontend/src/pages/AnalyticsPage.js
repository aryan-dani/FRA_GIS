import React, { useState, useEffect, useCallback } from "react";
import { Container, Spinner, Alert } from "react-bootstrap";
import { fetchClaims } from "../services/claimsService";
import Analytics from "../components/Analytics";
import "./AnalyticsPage.css";

function AnalyticsPage() {
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
      setError(err.message || "Failed to fetch claims data from the API.");
      console.error("Failed to fetch claims:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadClaims();
  }, [loadClaims]);

  return (
    <div className="analytics-page">
      <Container fluid>
        <div className="page-header">
          <h1 className="page-title">Claims Analytics</h1>
          <p className="page-subtitle">
            Status, type, and regional patterns across the FRA ledger.
          </p>
        </div>
        {error && <Alert variant="danger">{error}</Alert>}
        {loading ? (
          <div className="spinner-container">
            <Spinner animation="border" role="status">
              <span className="visually-hidden">Loading Analytics...</span>
            </Spinner>
          </div>
        ) : (
          <Analytics claims={claims} />
        )}
      </Container>
    </div>
  );
}

export default AnalyticsPage;
