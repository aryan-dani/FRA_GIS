import React, { useState, useEffect, useCallback } from "react";
import { Container, Spinner, Alert } from "react-bootstrap";
import {
  fetchClaims,
  updateClaimStatus,
} from "../services/claimsService";

import ClaimsTable from "../components/ClaimsTable";
import "./ClaimsDataPage.css";

function ClaimsDataPage() {
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadClaims = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchClaims();
      const claimsWithStatus = data.map((claim) => ({
        ...claim,
        status: claim.status || "Pending",
      }));
      setClaims(claimsWithStatus);
    } catch (err) {
      setError("Failed to fetch claims data from Firebase.");
      console.error("Error fetching claims:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadClaims();
  }, [loadClaims]);

  const handleStatusChange = async (claimId, newStatus) => {
    try {
      await updateClaimStatus(claimId, newStatus);
      loadClaims();
    } catch (err) {
      console.error("Failed to update status:", err);
      setError("Failed to update claim status.");
    }
  };

  return (
    <div className="claims-data-page">
      <Container fluid>
        <div className="page-header">
          <h1 className="page-title">Claims Ledger</h1>
          <p className="page-subtitle">
            Search, filter, and update FRA claim records.
          </p>
          <div className="page-meta">
            <span className="meta-chip">{claims.length} total</span>
            <span className="meta-chip">SIH focus states ready</span>
          </div>
        </div>

        <div className="ledger-shell">
          <div className="ledger-body">
            {error && <Alert variant="danger">{error}</Alert>}
            {loading ? (
              <div className="spinner-container">
                <Spinner animation="border" role="status">
                  <span className="visually-hidden">Loading Claims...</span>
                </Spinner>
              </div>
            ) : (
              <ClaimsTable
                claims={claims}
                onStatusChange={handleStatusChange}
              />
            )}
          </div>
        </div>
      </Container>
    </div>
  );
}

export default ClaimsDataPage;
