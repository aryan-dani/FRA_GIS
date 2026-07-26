import React, { useState, useEffect } from "react";
import {
  Container,
  Row,
  Col,
  Spinner,
  Alert,
  Button,
} from "react-bootstrap";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft } from "react-bootstrap-icons";
import { fetchClaimById } from "../services/claimsService";
import WebGISMap from "../components/WebGISMap";
import "./ClaimDetailPage.css";

const DetailItem = ({ label, value }) => (
  <div className="detail-item">
    <span className="detail-item-label">{label}</span>
    <span className="detail-item-value">{value || "—"}</span>
  </div>
);

function ClaimDetailPage() {
  const { id } = useParams();
  const [claim, setClaim] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadClaim = async () => {
      setLoading(true);
      try {
        const data = await fetchClaimById(id);
        setClaim(data);
      } catch (err) {
        setError("Failed to fetch claim details.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadClaim();
  }, [id]);

  if (loading) {
    return (
      <div className="spinner-container">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading Claim Details...</span>
        </Spinner>
      </div>
    );
  }

  if (error) {
    return (
      <Container className="py-4">
        <Alert variant="danger">{error}</Alert>
      </Container>
    );
  }

  if (!claim) {
    return (
      <Container className="py-4">
        <Alert variant="warning">Claim not found.</Alert>
      </Container>
    );
  }

  return (
    <div className="claim-detail-page">
      <Container fluid>
        <div className="page-header">
          <h1 className="page-title">{claim.name || "Claim record"}</h1>
          <p className="page-subtitle">
            {[claim.village, claim.district, claim.state]
              .filter(Boolean)
              .join(" · ") || "Location not recorded"}
          </p>
          <div className="page-meta">
            <span className="meta-chip">#{String(claim.id).slice(0, 10)}</span>
            <span className="meta-chip">{claim.claim_type || "Individual"}</span>
            <span className={`status-indicator status-${claim.status || "Pending"}`}>
              {claim.status || "Pending"}
            </span>
          </div>
        </div>

        <Link to="/claims-data">
          <Button variant="primary" className="back-button mb-3">
            <ArrowLeft className="me-2" />
            Back to Claims Ledger
          </Button>
        </Link>

        <Row className="g-3 mb-3">
          <Col lg={5} xl={4}>
            <div className="detail-panel">
              <h2>Claimant</h2>
              <DetailItem label="Name" value={claim.name} />
              <DetailItem label="Village" value={claim.village} />
              <DetailItem label="District" value={claim.district} />
              <DetailItem label="State" value={claim.state} />
              <DetailItem label="Claim type" value={claim.claim_type} />
              <DetailItem
                label="Coordinates"
                value={
                  claim.latitude != null && claim.longitude != null
                    ? `${claim.latitude}, ${claim.longitude}`
                    : null
                }
              />
            </div>
          </Col>
          <Col lg={7} xl={8}>
            <div className="detail-panel map-panel-detail">
              <div className="detail-panel-header">
                <h2>Geospatial view</h2>
              </div>
              <div className="map-container-detail">
                <WebGISMap claims={[claim]} />
              </div>
            </div>
          </Col>
        </Row>

        <div className="detail-panel">
          <h2>Extracted text</h2>
          <pre className="raw-text-container">
            {claim.raw_text || "No raw text available for this claim."}
          </pre>
        </div>
      </Container>
    </div>
  );
}

export default ClaimDetailPage;
