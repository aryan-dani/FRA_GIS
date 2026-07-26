import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Container,
  Form,
  Button,
  Card,
  Row,
  Col,
  Spinner,
} from "react-bootstrap";
import { createClaim } from "../services/claimsService";
import { toast } from "react-toastify";

const AddClaimPage = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: "",
    village: "",
    district: "",
    state: "",
    claim_type: "Individual",
    status: "Pending",
    latitude: "",
    longitude: "",
    raw_text: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    // Pre-fill form if data is passed from a previous step (though OCR is disabled)
    if (location.state && location.state.extractedData) {
      const { extractedData } = location.state;
      setFormData({
        name: extractedData.name || "",
        village: extractedData.village || "",
        district: extractedData.district || "",
        state: extractedData.state || "",
        claim_type: "Individual",
        status: "Pending",
        latitude: extractedData.latitude || "",
        longitude: extractedData.longitude || "",
        raw_text: extractedData.raw_text || "",
      });
    }
  }, [location.state]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await createClaim(formData);
      toast.success("Claim submitted successfully!");
      setTimeout(() => {
        navigate("/claims-data");
      }, 1500);
    } catch (err) {
      toast.error(err.message || "An unexpected error occurred.");
      setIsSubmitting(false);
    }
  };

  const isReviewMode = location.state && location.state.extractedData;

  return (
    <Container className="my-4">
      <Card>
        <Card.Header as="h2">
          {isReviewMode ? "Review and Confirm Claim" : "Add New Claim Manually"}
        </Card.Header>
        <Card.Body>
          {isReviewMode && (
            <div className="mb-3 p-3 border rounded bg-light">
              <h5>Extracted Entities (Review Mode)</h5>
              <p>
                <strong>Claimant:</strong>{" "}
                {formData.name || <span className="text-muted">Not found</span>}
              </p>
              <p>
                <strong>Village:</strong>{" "}
                {formData.village || (
                  <span className="text-muted">Not found</span>
                )}
              </p>
              <p>
                <strong>District:</strong>{" "}
                {formData.district || (
                  <span className="text-muted">Not found</span>
                )}
              </p>
            </div>
          )}
          <Form onSubmit={handleSubmit}>
            <Row className="mb-3">
              <Form.Group as={Col} controlId="formName">
                <Form.Label>Claimant Name</Form.Label>
                <Form.Control
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Enter claimant's name"
                  required
                />
              </Form.Group>
            </Row>

            <Row className="mb-3">
              <Form.Group as={Col} controlId="formVillage">
                <Form.Label>Village</Form.Label>
                <Form.Control
                  type="text"
                  name="village"
                  value={formData.village}
                  onChange={handleChange}
                  placeholder="Village"
                />
              </Form.Group>
              <Form.Group as={Col} controlId="formDistrict">
                <Form.Label>District</Form.Label>
                <Form.Control
                  type="text"
                  name="district"
                  value={formData.district}
                  onChange={handleChange}
                  placeholder="District"
                />
              </Form.Group>
              <Form.Group as={Col} controlId="formState">
                <Form.Label>State</Form.Label>
                <Form.Control
                  type="text"
                  name="state"
                  value={formData.state}
                  onChange={handleChange}
                  placeholder="State"
                />
              </Form.Group>
            </Row>

            <Row className="mb-3">
              <Form.Group as={Col} controlId="formLatitude">
                <Form.Label>Latitude</Form.Label>
                <Form.Control
                  type="number"
                  step="any"
                  name="latitude"
                  value={formData.latitude}
                  onChange={handleChange}
                  placeholder="e.g., 28.6139"
                />
              </Form.Group>
              <Form.Group as={Col} controlId="formLongitude">
                <Form.Label>Longitude</Form.Label>
                <Form.Control
                  type="number"
                  step="any"
                  name="longitude"
                  value={formData.longitude}
                  onChange={handleChange}
                  placeholder="e.g., 77.2090"
                />
              </Form.Group>
            </Row>

            <Row className="mb-3">
              <Form.Group as={Col} controlId="formClaimType">
                <Form.Label>Claim Type</Form.Label>
                <Form.Select
                  name="claim_type"
                  value={formData.claim_type}
                  onChange={handleChange}
                >
                  <option>Individual</option>
                  <option>Community</option>
                </Form.Select>
              </Form.Group>
              <Form.Group as={Col} controlId="formStatus">
                <Form.Label>Status</Form.Label>
                <Form.Select
                  name="status"
                  value={formData.status}
                  onChange={handleChange}
                >
                  <option>Pending</option>
                  <option>Approved</option>
                  <option>Rejected</option>
                  <option>In Review</option>
                </Form.Select>
              </Form.Group>
            </Row>

            {isReviewMode && (
              <Form.Group className="mb-3" controlId="formRawText">
                <Form.Label>Extracted Raw Text</Form.Label>
                <Form.Control
                  as="textarea"
                  name="raw_text"
                  rows={5}
                  value={formData.raw_text}
                  readOnly
                  style={{ backgroundColor: "#f8f9fa", cursor: "not-allowed" }}
                />
              </Form.Group>
            )}

            <Button variant="primary" type="submit" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Spinner
                    as="span"
                    animation="border"
                    size="sm"
                    role="status"
                    aria-hidden="true"
                  />
                  <span className="ms-2">Submitting...</span>
                </>
              ) : (
                "Submit Claim"
              )}
            </Button>
            <Button
              variant="secondary"
              className="ms-2"
              onClick={() => navigate(-1)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
          </Form>
        </Card.Body>
      </Card>
    </Container>
  );
};

export default AddClaimPage;
