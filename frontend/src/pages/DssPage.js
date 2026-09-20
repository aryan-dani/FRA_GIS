import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Alert,
  Badge,
  Button,
  Col,
  Container,
  Form,
  Row,
  Spinner,
  Table,
} from "react-bootstrap";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import {
  fetchDssMetrics,
  fetchDssPriority,
  fetchSyntheticClaims,
  predictDss,
} from "../services/dssService";
import "./DssPage.css";

const FOCUS_STATES = [
  "Madhya Pradesh",
  "Odisha",
  "Telangana",
  "Tripura",
];

const priorityVariant = (score) => {
  if (score >= 55) return "danger";
  if (score >= 40) return "warning";
  return "success";
};

function DssPage() {
  const [state, setState] = useState("Madhya Pradesh");
  const [districts, setDistricts] = useState([]);
  const [claims, setClaims] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [selected, setSelected] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(true);
  const [predicting, setPredicting] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    setSelected(null);
    setPrediction(null);
    try {
      const [priorityRes, claimsRes, metricsRes] = await Promise.all([
        fetchDssPriority(state),
        fetchSyntheticClaims({ state, limit: 180 }),
        fetchDssMetrics().catch(() => null),
      ]);
      setDistricts(priorityRes.districts || []);
      setClaims(claimsRes.claims || []);
      setMetrics(metricsRes);
    } catch (err) {
      setError(err.message || "Failed to load DSS data.");
    } finally {
      setLoading(false);
    }
  }, [state]);

  useEffect(() => {
    load();
  }, [load]);

  const mapCenter = useMemo(() => {
    const withCoords = claims.filter((c) => c.latitude && c.longitude);
    if (withCoords.length === 0) return [22.5, 80.0];
    const lat =
      withCoords.reduce((s, c) => s + Number(c.latitude), 0) / withCoords.length;
    const lon =
      withCoords.reduce((s, c) => s + Number(c.longitude), 0) /
      withCoords.length;
    return [lat, lon];
  }, [claims]);

  const schemeSummary = useMemo(() => {
    if (!prediction?.schemes) return [];
    return prediction.schemes.filter((s) => s.eligible);
  }, [prediction]);

  const onSelectClaim = async (claim) => {
    setSelected(claim);
    setPredicting(true);
    setPrediction(null);
    try {
      const result = await predictDss(claim);
      setPrediction(result);
    } catch (err) {
      setError(err.message || "Prediction failed.");
    } finally {
      setPredicting(false);
    }
  };

  return (
    <div className="dss-page">
      <Container fluid>
        <div className="page-header">
          <h1 className="page-title">Decision Support System</h1>
          <p className="page-subtitle">
            AI claim-outcome risk + CSS scheme layering for focus-state FRA
            monitoring (PM-KISAN, JJM, MGNREGA, DAJGUA).
          </p>
          <div className="page-meta">
            <span className="meta-chip">LightGBM outcome model</span>
            <span className="meta-chip">Rule-based + AI-enhanced DSS</span>
            {metrics?.macro_f1 != null && (
              <span className="meta-chip">
                Macro-F1 {Number(metrics.macro_f1).toFixed(3)}
              </span>
            )}
          </div>
        </div>

        <Row className="g-3 mb-3 align-items-end">
          <Col md={4} lg={3}>
            <Form.Group>
              <Form.Label>Focus state</Form.Label>
              <Form.Select
                value={state}
                onChange={(e) => setState(e.target.value)}
              >
                {FOCUS_STATES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
          </Col>
          <Col md="auto">
            <Button variant="primary" onClick={load} disabled={loading}>
              Refresh
            </Button>
          </Col>
        </Row>

        {error && <Alert variant="danger">{error}</Alert>}

        {loading ? (
          <div className="spinner-container">
            <Spinner animation="border" role="status">
              <span className="visually-hidden">Loading DSS...</span>
            </Spinner>
          </div>
        ) : (
          <>
            <Row className="g-3 mb-3">
              <Col lg={7}>
                <div className="dss-panel">
                  <div className="dss-panel-header">
                    <h2>District priority hotspots</h2>
                    <span className="text-muted small">
                      Score = pending backlog + reject rate + processing delay
                    </span>
                  </div>
                  <div className="dss-table-wrap">
                    <Table hover responsive size="sm" className="mb-0">
                      <thead>
                        <tr>
                          <th>District</th>
                          <th>Pending</th>
                          <th>Rejected</th>
                          <th>Mean days</th>
                          <th>Priority</th>
                        </tr>
                      </thead>
                      <tbody>
                        {districts.map((d) => (
                          <tr key={`${d.state}-${d.district}`}>
                            <td>{d.district}</td>
                            <td>{d.pending}</td>
                            <td>{d.rejected}</td>
                            <td>{d.mean_processing_days ?? "—"}</td>
                            <td>
                              <Badge bg={priorityVariant(d.priority_score)}>
                                {d.priority_score}
                              </Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </div>
                </div>
              </Col>
              <Col lg={5}>
                <div className="dss-panel">
                  <div className="dss-panel-header">
                    <h2>Model snapshot</h2>
                  </div>
                  {metrics ? (
                    <ul className="dss-metrics">
                      <li>
                        <strong>Accuracy</strong>
                        <span>{Number(metrics.accuracy).toFixed(3)}</span>
                      </li>
                      <li>
                        <strong>Macro F1</strong>
                        <span>{Number(metrics.macro_f1).toFixed(3)}</span>
                      </li>
                      {metrics.per_class_recall &&
                        Object.entries(metrics.per_class_recall).map(
                          ([label, value]) => (
                            <li key={label}>
                              <strong>{label} recall</strong>
                              <span>{Number(value).toFixed(3)}</span>
                            </li>
                          )
                        )}
                      <li>
                        <strong>Holdout</strong>
                        <span>{metrics.holdout || "district split"}</span>
                      </li>
                    </ul>
                  ) : (
                    <p className="text-muted mb-0">
                      Train metrics unavailable. Run{" "}
                      <code>python ml/train_claim_outcome.py</code> in the
                      project venv.
                    </p>
                  )}
                </div>
              </Col>
            </Row>

            <Row className="g-3">
              <Col lg={7}>
                <div className="dss-panel map-panel">
                  <div className="dss-panel-header">
                    <h2>Synthetic claims sample</h2>
                    <span className="text-muted small">
                      Click a marker for AI prediction + scheme layering
                    </span>
                  </div>
                  <div className="dss-map">
                    <MapContainer
                      center={mapCenter}
                      zoom={7}
                      style={{ height: "100%", width: "100%" }}
                    >
                      <TileLayer
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                      />
                      {claims
                        .filter((c) => c.latitude && c.longitude)
                        .map((c) => (
                          <CircleMarker
                            key={c.claim_id}
                            center={[Number(c.latitude), Number(c.longitude)]}
                            radius={6}
                            pathOptions={{
                              color:
                                c.status === "Rejected"
                                  ? "#b91c1c"
                                  : c.status === "Pending"
                                    ? "#b45309"
                                    : "#166534",
                              fillOpacity: 0.75,
                            }}
                            eventHandlers={{
                              click: () => onSelectClaim(c),
                            }}
                          >
                            <Popup>
                              <strong>{c.claim_id}</strong>
                              <br />
                              {c.district} · {c.claim_type}
                              <br />
                              {c.status}
                            </Popup>
                          </CircleMarker>
                        ))}
                    </MapContainer>
                  </div>
                </div>
              </Col>
              <Col lg={5}>
                <div className="dss-panel">
                  <div className="dss-panel-header">
                    <h2>DSS recommendation</h2>
                  </div>
                  {!selected && !predicting && (
                    <p className="text-muted mb-0">
                      Select a claim on the map to run the outcome model and CSS
                      scheme rules.
                    </p>
                  )}
                  {predicting && (
                    <div className="py-4 text-center">
                      <Spinner animation="border" size="sm" /> Predicting…
                    </div>
                  )}
                  {selected && prediction && (
                    <div className="dss-rec">
                      <div className="dss-rec-claim">
                        <strong>{selected.claim_id}</strong>
                        <span>
                          {selected.village || "—"} · {selected.district}
                        </span>
                        <Badge bg="secondary">{selected.status}</Badge>
                      </div>
                      <div className="dss-pred">
                        <span className="label">Predicted status</span>
                        <strong>{prediction.predicted_status}</strong>
                        <div className="dss-probs">
                          {prediction.probabilities &&
                            Object.entries(prediction.probabilities).map(
                              ([k, v]) => (
                                <span key={k}>
                                  {k}: {(Number(v) * 100).toFixed(1)}%
                                </span>
                              )
                            )}
                        </div>
                      </div>
                      {prediction.shap_top?.length > 0 &&
                        prediction.shap_top[0].feature !==
                          "_shap_unavailable" && (
                          <div className="dss-shap">
                            <h3>Top SHAP drivers</h3>
                            <ul>
                              {prediction.shap_top.map((s) => (
                                <li key={s.feature}>
                                  <span>{s.feature}</span>
                                  <em>
                                    {s.impact > 0 ? "+" : ""}
                                    {s.impact}
                                  </em>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      <div className="dss-schemes">
                        <h3>Eligible CSS schemes</h3>
                        {schemeSummary.length === 0 ? (
                          <p className="text-muted small mb-0">
                            No schemes flagged for this claim under demo rules.
                          </p>
                        ) : (
                          schemeSummary.map((s) => (
                            <div className="dss-scheme-card" key={s.scheme_id}>
                              <div className="dss-scheme-head">
                                <strong>{s.name}</strong>
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
                              </div>
                              <p className="small text-muted mb-1">
                                {s.ministry}
                              </p>
                              <ul>
                                {s.reasons.map((r) => (
                                  <li key={r}>{r}</li>
                                ))}
                              </ul>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </Col>
            </Row>
          </>
        )}
      </Container>
    </div>
  );
}

export default DssPage;
