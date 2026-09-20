import React, { useState, useEffect } from "react";
import {
  Container,
  Row,
  Col,
  Spinner,
  Alert,
  Button,
  Badge,
} from "react-bootstrap";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft } from "react-bootstrap-icons";
import { fetchClaimById } from "../services/claimsService";
import { predictDss } from "../services/dssService";
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
  const [dss, setDss] = useState(null);
  const [dssLoading, setDssLoading] = useState(false);
  const [dssError, setDssError] = useState("");

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

  useEffect(() => {
    if (!claim) return;
    let cancelled = false;
    const runDss = async () => {
      setDssLoading(true);
      setDssError("");
      try {
        const result = await predictDss({ claim_id: claim.id, ...claim });
        if (!cancelled) setDss(result);
      } catch (err) {
        if (!cancelled) {
          setDssError(err.message || "DSS prediction unavailable.");
        }
      } finally {
        if (!cancelled) setDssLoading(false);
      }
    };
    runDss();
    return () => {
      cancelled = true;
    };
  }, [claim]);

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

  const eligibleSchemes = (dss?.schemes || []).filter((s) => s.eligible);

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
                <WebGISMap claims={[claim]} height="460px" zoom={13} showAreas />
              </div>
            </div>
          </Col>
        </Row>

        <div className="detail-panel mb-3">
          <h2>DSS — AI outcome &amp; scheme layering</h2>
          {dssLoading && (
            <div className="py-3">
              <Spinner animation="border" size="sm" /> Running DSS…
            </div>
          )}
          {dssError && <Alert variant="warning">{dssError}</Alert>}
          {dss && !dssLoading && (
            <Row className="g-3">
              <Col md={5}>
                <DetailItem label="Predicted" value={dss.predicted_status} />
                {dss.probabilities &&
                  Object.entries(dss.probabilities).map(([label, p]) => (
                    <DetailItem
                      key={label}
                      label={label}
                      value={`${(Number(p) * 100).toFixed(1)}%`}
                    />
                  ))}
                {dss.shap_top?.length > 0 &&
                  dss.shap_top[0].feature !== "_shap_unavailable" && (
                    <div className="mt-3">
                      <h3 className="h6">Top SHAP drivers</h3>
                      <ul className="mb-0 small">
                        {dss.shap_top.map((s) => (
                          <li key={s.feature}>
                            {s.feature}: {s.impact > 0 ? "+" : ""}
                            {s.impact}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
              </Col>
              <Col md={7}>
                <h3 className="h6">Recommended CSS schemes</h3>
                {eligibleSchemes.length === 0 ? (
                  <p className="text-muted small mb-0">
                    No schemes flagged under demo eligibility rules.
                  </p>
                ) : (
                  eligibleSchemes.map((s) => (
                    <div key={s.scheme_id} className="mb-2">
                      <strong>{s.name}</strong>{" "}
                      <Badge
                        bg={
                          s.priority === "High"
                            ? "danger"
                            : s.priority === "Medium"
                              ? "warning"
                              : "secondary"
                        }
                      >
                        {s.priority}
                      </Badge>
                      <ul className="small mb-0">
                        {s.reasons.map((r) => (
                          <li key={r}>{r}</li>
                        ))}
                      </ul>
                    </div>
                  ))
                )}
                <Link to="/dss" className="small">
                  Open full DSS atlas →
                </Link>
              </Col>
            </Row>
          )}
        </div>

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
