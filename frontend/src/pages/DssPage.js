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
  Tab,
  Table,
  Tabs,
} from "react-bootstrap";
import {
  fetchDssBenchmark,
  fetchDssEta,
  fetchDssMetrics,
  fetchDssPriority,
  fetchDssReasons,
  fetchDssTriage,
  fetchDssWhatIf,
  fetchSyntheticClaims,
  predictDss,
} from "../services/dssService";
import WebGISMap from "../components/WebGISMap";
import "./DssPage.css";

const FOCUS_STATES = [
  "Madhya Pradesh",
  "Odisha",
  "Telangana",
  "Tripura",
];

const REVIEW_THRESHOLD = 0.55;

const EMPTY_SIM = {
  state: "Madhya Pradesh",
  district: "Demo District",
  claim_type: "IFR",
  applicant_type: "ST",
  land_area_ha: 1.5,
  forest_density_class: "Moderately Dense",
  year_filed: 2018,
  documentation_completeness: "Partial",
  gram_sabha_resolution: "Passed",
  processing_days: 180,
  committee_level_reached: "FRC",
};

const priorityVariant = (score) => {
  if (score >= 55) return "danger";
  if (score >= 40) return "warning";
  return "success";
};

function maxProb(probabilities) {
  if (!probabilities) return 0;
  return Math.max(...Object.values(probabilities).map(Number));
}

function RecommendationPanel({
  selected,
  prediction,
  whatIf,
  eta,
  reasons,
  predicting,
}) {
  const schemeSummary = useMemo(() => {
    if (!prediction?.schemes) return [];
    return prediction.schemes.filter((s) => s.eligible);
  }, [prediction]);

  const needsReview =
    prediction?.probabilities &&
    maxProb(prediction.probabilities) < REVIEW_THRESHOLD;

  if (!selected && !predicting) {
    return (
      <p className="text-muted mb-0">
        Select a claim on the map, triage queue, or score a simulated claim to
        run the outcome model and CSS scheme rules.
      </p>
    );
  }

  if (predicting) {
    return (
      <div className="py-4 text-center">
        <Spinner animation="border" size="sm" /> Predicting…
      </div>
    );
  }

  if (!prediction) return null;

  const placeBits = [selected?.village, selected?.district].filter(
    (v, i, arr) => v && arr.indexOf(v) === i
  );
  const placeLabel = placeBits.length ? placeBits.join(" · ") : "—";
  const title =
    selected?.claim_id && selected.claim_id !== "Simulated claim"
      ? selected.claim_id
      : "Simulated claim";

  return (
    <div className="dss-rec">
      <div className="dss-rec-claim">
        <strong>{title}</strong>
        <span>{placeLabel}</span>
        {selected?.status && <Badge bg="secondary">{selected.status}</Badge>}
      </div>
      <div className="dss-pred">
        <span className="label">Predicted status</span>
        <strong>{prediction.predicted_status}</strong>
        <div className="dss-prob-bars">
          {prediction.probabilities &&
            Object.entries(prediction.probabilities).map(([k, v]) => {
              const pct = Math.max(0, Math.min(100, Number(v) * 100));
              return (
                <div className="dss-prob-row" key={k}>
                  <div className="dss-prob-meta">
                    <span>{k}</span>
                    <span>{pct.toFixed(1)}%</span>
                  </div>
                  <div className="dss-prob-track">
                    <div
                      className={`dss-prob-fill dss-prob-${k.toLowerCase()}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
        </div>
        {needsReview && (
          <Alert variant="warning" className="mt-2 mb-0 py-2 small">
            Low confidence (below {REVIEW_THRESHOLD}). Flag for human review.
          </Alert>
        )}
      </div>
      {prediction.shap_top?.length > 0 &&
        prediction.shap_top[0].feature !== "_shap_unavailable" && (
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
              <p className="small text-muted mb-1">{s.ministry}</p>
              <ul>
                {(s.reasons || []).map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            </div>
          ))
        )}
      </div>
      {whatIf?.changes?.length > 0 && (
        <div className="dss-shap mt-3">
          <h3>What-if (actionable fields)</h3>
          <ul>
            {whatIf.changes.map((c) => (
              <li key={`${c.field}-${c.to_value}`}>
                <span>
                  {c.field}: {String(c.from_value)} to {String(c.to_value)}
                </span>
                <em>+{(Number(c.approval_lift) * 100).toFixed(1)}%</em>
              </li>
            ))}
          </ul>
        </div>
      )}
      {eta?.eta_days_point != null && (
        <div className="dss-shap mt-3">
          <h3>ETA (resolved-claims model)</h3>
          <p className="mb-1">
            Point estimate: <strong>{eta.eta_days_point}</strong> days
          </p>
          {eta.caveat && (
            <p className="text-muted small mb-0">{eta.caveat}</p>
          )}
        </div>
      )}
      {reasons?.length > 0 && (
        <div className="dss-shap mt-3">
          <h3>Top rejection reasons</h3>
          <ul>
            {reasons.map((r) => (
              <li key={r.reason}>
                <span>{r.reason}</span>
                <em>{(Number(r.probability) * 100).toFixed(1)}%</em>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function DssPage() {
  const [state, setState] = useState("Madhya Pradesh");
  const [activeTab, setActiveTab] = useState("overview");
  const [districts, setDistricts] = useState([]);
  const [claims, setClaims] = useState([]);
  const [triage, setTriage] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [benchmark, setBenchmark] = useState(null);
  const [whatIf, setWhatIf] = useState(null);
  const [eta, setEta] = useState(null);
  const [reasons, setReasons] = useState([]);
  const [selected, setSelected] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [simForm, setSimForm] = useState(EMPTY_SIM);
  const [loading, setLoading] = useState(true);
  const [triageLoading, setTriageLoading] = useState(false);
  const [predicting, setPredicting] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    setSelected(null);
    setPrediction(null);
    setWhatIf(null);
    setEta(null);
    setReasons([]);
    try {
      const [priorityRes, claimsRes, metricsRes, benchRes] = await Promise.all([
        fetchDssPriority(state),
        fetchSyntheticClaims({ state, limit: 180 }),
        fetchDssMetrics().catch(() => null),
        fetchDssBenchmark().catch(() => null),
      ]);
      setDistricts(priorityRes.districts || []);
      setClaims(claimsRes.claims || []);
      setMetrics(metricsRes);
      setBenchmark(benchRes);
    } catch (err) {
      setError(err.message || "Failed to load DSS data.");
    } finally {
      setLoading(false);
    }
  }, [state]);

  const loadTriage = useCallback(async () => {
    setTriageLoading(true);
    try {
      const res = await fetchDssTriage({ state, limit: 40 });
      setTriage(res.claims || []);
    } catch (err) {
      setError(err.message || "Failed to load triage queue.");
      setTriage([]);
    } finally {
      setTriageLoading(false);
    }
  }, [state]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (activeTab === "triage") {
      loadTriage();
    }
  }, [activeTab, loadTriage]);

  useEffect(() => {
    setSimForm((prev) => ({ ...prev, state }));
  }, [state]);

  const mapCenter = useMemo(() => {
    const withCoords = claims.filter((c) => c.latitude && c.longitude);
    if (withCoords.length === 0) return { lat: 22.5, lng: 80.0 };
    const lat =
      withCoords.reduce((s, c) => s + Number(c.latitude), 0) / withCoords.length;
    const lng =
      withCoords.reduce((s, c) => s + Number(c.longitude), 0) /
      withCoords.length;
    return { lat, lng };
  }, [claims]);

  const benchRows = useMemo(() => {
    const rows = benchmark?.rows || [];
    return rows
      .filter((r) => r.feature_set === "A" && r.s1_macro_f1_mean)
      .sort((a, b) => Number(b.s1_macro_f1_mean) - Number(a.s1_macro_f1_mean))
      .slice(0, 12);
  }, [benchmark]);

  const runRecommendation = async (claim) => {
    const { _label, ...apiClaim } = claim;
    setSelected({
      ...apiClaim,
      claim_id: apiClaim.claim_id || _label || "Simulated claim",
    });
    setPredicting(true);
    setPrediction(null);
    setWhatIf(null);
    setEta(null);
    setReasons([]);
    setError("");
    try {
      const result = await predictDss(apiClaim);
      setPrediction(result);
      const [wi, etaRes, reasonRes] = await Promise.all([
        fetchDssWhatIf(apiClaim).catch(() => null),
        fetchDssEta(apiClaim).catch(() => null),
        fetchDssReasons(apiClaim).catch(() => null),
      ]);
      setWhatIf(wi);
      setEta(etaRes);
      setReasons(reasonRes?.reasons || []);
    } catch (err) {
      setError(err.message || "Prediction failed.");
    } finally {
      setPredicting(false);
    }
  };

  const onSelectClaim = (claim) => runRecommendation(claim);

  const onSimSubmit = async (e) => {
    e.preventDefault();
    // Do not send claim_id — Flask treats that as a Firestore/synthetic lookup.
    const claim = {
      ...simForm,
      land_area_ha: Number(simForm.land_area_ha),
      year_filed: Number(simForm.year_filed),
      processing_days: Number(simForm.processing_days),
    };
    await runRecommendation({ ...claim, _label: "Simulated claim" });
  };

  const recProps = {
    selected,
    prediction,
    whatIf,
    eta,
    reasons,
    predicting,
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
            <span className="meta-chip meta-chip-warn">Synthetic data demo</span>
            {metrics?.macro_f1 != null && (
              <span className="meta-chip">
                Macro-F1 {Number(metrics.macro_f1).toFixed(3)}
              </span>
            )}
            {benchmark?.champion?.model && (
              <span className="meta-chip">
                S1 champion: {benchmark.champion.model}
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

        {error && (
          <Alert variant="danger" dismissible onClose={() => setError("")}>
            {error}
          </Alert>
        )}

        {loading ? (
          <div className="spinner-container">
            <Spinner animation="border" role="status">
              <span className="visually-hidden">Loading DSS...</span>
            </Spinner>
          </div>
        ) : (
          <Tabs
            activeKey={activeTab}
            onSelect={(k) => setActiveTab(k || "overview")}
            className="dss-tabs mb-3"
            mountOnEnter
            unmountOnExit
          >
            <Tab eventKey="overview" title="Overview">
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
                      <WebGISMap
                        claims={claims}
                        height="100%"
                        center={mapCenter}
                        zoom={7}
                        colorBy="status"
                        showAreas
                        onClaimClick={onSelectClaim}
                      />
                    </div>
                  </div>
                </Col>
                <Col lg={5}>
                  <div className="dss-panel">
                    <div className="dss-panel-header">
                      <h2>DSS recommendation</h2>
                    </div>
                    <RecommendationPanel {...recProps} />
                  </div>
                </Col>
              </Row>
            </Tab>

            <Tab eventKey="simulator" title="Claim simulator">
              <Row className="g-3">
                <Col lg={6}>
                  <div className="dss-panel">
                    <div className="dss-panel-header">
                      <h2>Filing-time claim form</h2>
                      <span className="text-muted small">
                        Set A fields only (no leakage features required)
                      </span>
                    </div>
                    <Form className="dss-sim-form" onSubmit={onSimSubmit}>
                      <Row className="g-2">
                        <Col md={6}>
                          <Form.Group>
                            <Form.Label>State</Form.Label>
                            <Form.Select
                              value={simForm.state}
                              onChange={(e) =>
                                setSimForm((f) => ({
                                  ...f,
                                  state: e.target.value,
                                }))
                              }
                            >
                              {FOCUS_STATES.map((s) => (
                                <option key={s} value={s}>
                                  {s}
                                </option>
                              ))}
                            </Form.Select>
                          </Form.Group>
                        </Col>
                        <Col md={6}>
                          <Form.Group>
                            <Form.Label>District</Form.Label>
                            <Form.Control
                              value={simForm.district}
                              onChange={(e) =>
                                setSimForm((f) => ({
                                  ...f,
                                  district: e.target.value,
                                }))
                              }
                            />
                          </Form.Group>
                        </Col>
                        <Col md={6}>
                          <Form.Group>
                            <Form.Label>Claim type</Form.Label>
                            <Form.Select
                              value={simForm.claim_type}
                              onChange={(e) =>
                                setSimForm((f) => ({
                                  ...f,
                                  claim_type: e.target.value,
                                }))
                              }
                            >
                              {["IFR", "CFR", "CR"].map((v) => (
                                <option key={v} value={v}>
                                  {v}
                                </option>
                              ))}
                            </Form.Select>
                          </Form.Group>
                        </Col>
                        <Col md={6}>
                          <Form.Group>
                            <Form.Label>Applicant type</Form.Label>
                            <Form.Select
                              value={simForm.applicant_type}
                              onChange={(e) =>
                                setSimForm((f) => ({
                                  ...f,
                                  applicant_type: e.target.value,
                                }))
                              }
                            >
                              {["ST", "OTFD"].map((v) => (
                                <option key={v} value={v}>
                                  {v}
                                </option>
                              ))}
                            </Form.Select>
                          </Form.Group>
                        </Col>
                        <Col md={6}>
                          <Form.Group>
                            <Form.Label>Land area (ha)</Form.Label>
                            <Form.Control
                              type="number"
                              min={0.1}
                              max={100}
                              step={0.1}
                              value={simForm.land_area_ha}
                              onChange={(e) =>
                                setSimForm((f) => ({
                                  ...f,
                                  land_area_ha: e.target.value,
                                }))
                              }
                            />
                          </Form.Group>
                        </Col>
                        <Col md={6}>
                          <Form.Group>
                            <Form.Label>Year filed</Form.Label>
                            <Form.Control
                              type="number"
                              min={2008}
                              max={2024}
                              value={simForm.year_filed}
                              onChange={(e) =>
                                setSimForm((f) => ({
                                  ...f,
                                  year_filed: e.target.value,
                                }))
                              }
                            />
                          </Form.Group>
                        </Col>
                        <Col md={6}>
                          <Form.Group>
                            <Form.Label>Forest density</Form.Label>
                            <Form.Select
                              value={simForm.forest_density_class}
                              onChange={(e) =>
                                setSimForm((f) => ({
                                  ...f,
                                  forest_density_class: e.target.value,
                                }))
                              }
                            >
                              {[
                                "Open",
                                "Moderately Dense",
                                "Very Dense",
                                "Scrub",
                              ].map((v) => (
                                <option key={v} value={v}>
                                  {v}
                                </option>
                              ))}
                            </Form.Select>
                          </Form.Group>
                        </Col>
                        <Col md={6}>
                          <Form.Group>
                            <Form.Label>Documentation</Form.Label>
                            <Form.Select
                              value={simForm.documentation_completeness}
                              onChange={(e) =>
                                setSimForm((f) => ({
                                  ...f,
                                  documentation_completeness: e.target.value,
                                }))
                              }
                            >
                              {["Complete", "Partial", "Incomplete"].map(
                                (v) => (
                                  <option key={v} value={v}>
                                    {v}
                                  </option>
                                )
                              )}
                            </Form.Select>
                          </Form.Group>
                        </Col>
                        <Col md={12}>
                          <Form.Group>
                            <Form.Label>Gram Sabha resolution</Form.Label>
                            <Form.Select
                              value={simForm.gram_sabha_resolution}
                              onChange={(e) =>
                                setSimForm((f) => ({
                                  ...f,
                                  gram_sabha_resolution: e.target.value,
                                }))
                              }
                            >
                              {[
                                "Passed",
                                "Pending",
                                "Disputed",
                                "Rejected",
                              ].map((v) => (
                                <option key={v} value={v}>
                                  {v}
                                </option>
                              ))}
                            </Form.Select>
                          </Form.Group>
                        </Col>
                      </Row>
                      <Button
                        type="submit"
                        variant="primary"
                        className="mt-3"
                        disabled={predicting}
                      >
                        {predicting ? "Scoring…" : "Score claim"}
                      </Button>
                    </Form>
                  </div>
                </Col>
                <Col lg={6}>
                  <div className="dss-panel">
                    <div className="dss-panel-header">
                      <h2>DSS recommendation</h2>
                    </div>
                    <RecommendationPanel {...recProps} />
                  </div>
                </Col>
              </Row>
            </Tab>

            <Tab eventKey="triage" title="Triage queue">
              <Row className="g-3">
                <Col lg={7}>
                  <div className="dss-panel">
                    <div className="dss-panel-header">
                      <h2>Pending backlog triage</h2>
                      <span className="text-muted small">
                        Score = 0.45×P(reject) + 0.35×delay + 0.20×age
                      </span>
                    </div>
                    {triageLoading ? (
                      <div className="py-4 text-center">
                        <Spinner animation="border" size="sm" /> Loading triage…
                      </div>
                    ) : (
                      <div className="dss-table-wrap dss-table-tall">
                        <Table hover responsive size="sm" className="mb-0">
                          <thead>
                            <tr>
                              <th>Claim</th>
                              <th>District</th>
                              <th>Type</th>
                              <th>Days</th>
                              <th>P(reject)</th>
                              <th>Triage</th>
                            </tr>
                          </thead>
                          <tbody>
                            {triage.map((c) => (
                              <tr
                                key={c.claim_id}
                                className={
                                  selected?.claim_id === c.claim_id
                                    ? "dss-row-active"
                                    : "dss-row-click"
                                }
                                onClick={() => onSelectClaim(c)}
                              >
                                <td>{c.claim_id}</td>
                                <td>{c.district}</td>
                                <td>{c.claim_type}</td>
                                <td>{c.processing_days ?? "—"}</td>
                                <td>
                                  {(Number(c.reject_prob || 0) * 100).toFixed(
                                    1
                                  )}
                                  %
                                </td>
                                <td>
                                  <Badge
                                    bg={priorityVariant(c.triage_score)}
                                    className="dss-triage-badge"
                                  >
                                    {c.triage_score}
                                  </Badge>
                                </td>
                              </tr>
                            ))}
                            {triage.length === 0 && (
                              <tr>
                                <td colSpan={6} className="text-muted">
                                  No pending claims in sample for this state.
                                </td>
                              </tr>
                            )}
                          </tbody>
                        </Table>
                      </div>
                    )}
                  </div>
                </Col>
                <Col lg={5}>
                  <div className="dss-panel">
                    <div className="dss-panel-header">
                      <h2>DSS recommendation</h2>
                    </div>
                    <RecommendationPanel {...recProps} />
                  </div>
                </Col>
              </Row>
            </Tab>

            <Tab eventKey="benchmark" title="Benchmark">
              <div className="dss-panel">
                <div className="dss-panel-header">
                  <h2>ML Benchmark (Set A)</h2>
                  <span className="text-muted small">
                    Synthetic data. S1 grouped district CV macro-F1.
                    {benchmark?.champion?.model
                      ? ` Champion: ${benchmark.champion.model} (S1=${Number(
                          benchmark.champion.s1_macro_f1_mean || 0
                        ).toFixed(3)}).`
                      : ""}
                  </span>
                </div>
                {benchRows.length === 0 ? (
                  <p className="text-muted mb-0">
                    Benchmark unavailable. Run the ML pipeline first.
                  </p>
                ) : (
                  <div className="dss-table-wrap dss-table-tall">
                    <Table hover responsive size="sm" className="mb-0">
                      <thead>
                        <tr>
                          <th>Model</th>
                          <th>S1 macro-F1</th>
                          <th>Final macro-F1</th>
                          <th>S3 macro-F1</th>
                          <th>Latency ms/1k</th>
                        </tr>
                      </thead>
                      <tbody>
                        {benchRows.map((r) => (
                          <tr
                            key={r.model}
                            className={
                              benchmark?.champion?.model === r.model
                                ? "dss-row-active"
                                : undefined
                            }
                          >
                            <td>
                              {r.model}
                              {benchmark?.champion?.model === r.model && (
                                <Badge bg="success" className="ms-2">
                                  champion
                                </Badge>
                              )}
                            </td>
                            <td>
                              {Number(r.s1_macro_f1_mean).toFixed(3)}
                              {r.s1_macro_f1_std != null &&
                                ` ± ${Number(r.s1_macro_f1_std).toFixed(3)}`}
                            </td>
                            <td>
                              {r.final_macro_f1 != null
                                ? Number(r.final_macro_f1).toFixed(3)
                                : "—"}
                            </td>
                            <td>
                              {r.s3_macro_f1 != null
                                ? Number(r.s3_macro_f1).toFixed(3)
                                : "—"}
                            </td>
                            <td>
                              {r.latency_ms_per_1k != null
                                ? Number(r.latency_ms_per_1k).toFixed(1)
                                : "—"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </div>
                )}
                {benchmark?.disclosure && (
                  <p className="text-muted small mt-3 mb-0">
                    {benchmark.disclosure}
                  </p>
                )}
              </div>
            </Tab>
          </Tabs>
        )}
      </Container>
    </div>
  );
}

export default DssPage;
