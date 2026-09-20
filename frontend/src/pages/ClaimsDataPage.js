import React, { useState, useEffect, useCallback } from "react";
import { Button, Container, Spinner, Alert } from "react-bootstrap";
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
  const [loadAll, setLoadAll] = useState(false);

  const loadClaims = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchClaims({
        source: "all",
        limit: loadAll ? "all" : 5000,
      });
      const claimsWithStatus = data.map((claim) => ({
        ...claim,
        status: claim.status || "Pending",
      }));
      setClaims(claimsWithStatus);
    } catch (err) {
      setError(err.message || "Failed to fetch claims data from the API.");
      console.error("Error fetching claims:", err);
    } finally {
      setLoading(false);
    }
  }, [loadAll]);

  useEffect(() => {
    loadClaims();
  }, [loadClaims]);

  const handleStatusChange = async (claimId, newStatus) => {
    try {
      await updateClaimStatus(claimId, newStatus);
      loadClaims();
    } catch (err) {
      console.error("Failed to update status:", err);
      setError(err.message || "Failed to update claim status.");
    }
  };

  const syntheticCount = claims.filter((c) => c.source === "synthetic").length;
  const firestoreCount = claims.filter((c) => c.source !== "synthetic").length;

  return (
    <div className="claims-data-page">
      <Container fluid>
        <div className="page-header">
          <h1 className="page-title">Claims Ledger</h1>
          <p className="page-subtitle">
            Digitized Firestore claims plus the synthetic FRA dataset for ML /
            DSS demos.
          </p>
          <div className="page-meta">
            <span className="meta-chip">{claims.length} loaded</span>
            <span className="meta-chip">{syntheticCount} synthetic</span>
            <span className="meta-chip">{firestoreCount} digitized</span>
            {!loadAll && (
              <Button
                size="sm"
                variant="outline-primary"
                className="ms-1"
                disabled={loading}
                onClick={() => setLoadAll(true)}
              >
                Load all synthetic (~125k)
              </Button>
            )}
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
