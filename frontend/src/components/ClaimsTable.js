import React, { useState, useMemo } from "react";
import {
  Form,
  Row,
  Col,
  InputGroup,
  Spinner,
  Pagination,
  Dropdown,
  Button,
} from "react-bootstrap";
import {
  Search,
  PencilSquare,
  PlusCircle,
  Download,
} from "react-bootstrap-icons";
import { Link, useNavigate } from "react-router-dom";
import "./ClaimsTable.css";

const ROWS_PER_PAGE = 10;

function ClaimsTable({ claims, onStatusChange }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [filters, setFilters] = useState({
    state: "",
    district: "",
    status: "",
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((prev) => ({ ...prev, [name]: value }));
    setCurrentPage(1);
  };

  const handleStatusUpdate = async (claimId, newStatus) => {
    setLoading(true);
    await onStatusChange(claimId, newStatus);
    setLoading(false);
  };

  const handleRowClick = (claimId) => {
    navigate(`/claim/${claimId}`);
  };

  const exportToCSV = () => {
    const headers = [
      "ID",
      "Name",
      "Village",
      "District",
      "State",
      "Status",
      "Claim Type",
      "Created At",
    ];
    const rows = filteredClaims.map((claim) => [
      claim.id,
      claim.name,
      claim.village,
      claim.district,
      claim.state,
      claim.status,
      claim.claim_type,
      claim.created_at,
    ]);

    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += headers.join(",") + "\r\n";
    rows.forEach((rowArray) => {
      const row = rowArray.join(",");
      csvContent += row + "\r\n";
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "claims_data.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const filteredClaims = useMemo(() => {
    return claims
      .filter((claim) => {
        const searchLower = searchTerm.toLowerCase();
        return (
          !searchTerm ||
          claim.name?.toLowerCase().includes(searchLower) ||
          claim.village?.toLowerCase().includes(searchLower) ||
          claim.district?.toLowerCase().includes(searchLower)
        );
      })
      .filter((claim) => {
        return (
          (!filters.state || claim.state === filters.state) &&
          (!filters.district || claim.district === filters.district) &&
          (!filters.status || claim.status === filters.status)
        );
      });
  }, [claims, searchTerm, filters]);

  const paginatedClaims = useMemo(() => {
    const startIndex = (currentPage - 1) * ROWS_PER_PAGE;
    return filteredClaims.slice(startIndex, startIndex + ROWS_PER_PAGE);
  }, [filteredClaims, currentPage]);

  const totalPages = Math.ceil(filteredClaims.length / ROWS_PER_PAGE);

  const uniqueStates = useMemo(
    () => [...new Set(claims.map((c) => c.state).filter(Boolean))],
    [claims]
  );
  const uniqueDistricts = useMemo(
    () => [...new Set(claims.map((c) => c.district).filter(Boolean))],
    [claims]
  );
  const uniqueStatuses = useMemo(
    () => [...new Set(claims.map((c) => c.status).filter(Boolean))],
    [claims]
  );

  return (
    <div>
      <Row className="filter-bar align-items-center mb-2">
        <Col lg={3} md={6} className="mb-2 mb-md-0">
          <InputGroup>
            <InputGroup.Text>
              <Search />
            </InputGroup.Text>
            <Form.Control
              type="text"
              placeholder="Search name, village, district..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
            />
          </InputGroup>
        </Col>
        <Col lg={2} md={3} sm={6} className="mb-2 mb-md-0">
          <Form.Select
            name="state"
            value={filters.state}
            onChange={handleFilterChange}
          >
            <option value="">All States</option>
            {uniqueStates.map((state) => (
              <option key={state} value={state}>
                {state}
              </option>
            ))}
          </Form.Select>
        </Col>
        <Col lg={2} md={3} sm={6} className="mb-2 mb-md-0">
          <Form.Select
            name="district"
            value={filters.district}
            onChange={handleFilterChange}
          >
            <option value="">All Districts</option>
            {uniqueDistricts.map((district) => (
              <option key={district} value={district}>
                {district}
              </option>
            ))}
          </Form.Select>
        </Col>
        <Col lg={2} md={3} sm={6} className="mb-2 mb-md-0">
          <Form.Select
            name="status"
            value={filters.status}
            onChange={handleFilterChange}
          >
            <option value="">All Statuses</option>
            {uniqueStatuses.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </Form.Select>
        </Col>
        <Col
          lg={3}
          md={9}
          sm={12}
          className="d-flex justify-content-start justify-content-md-end mt-2 mt-md-0"
        >
          <Button
            variant="outline-secondary"
            className="me-2"
            onClick={exportToCSV}
          >
            <Download className="me-1" />
            Export
          </Button>
          <Link to="/add-claim">
            <Button variant="primary" className="add-claim-button">
              <PlusCircle className="me-1" />
              New Claim
            </Button>
          </Link>
        </Col>
      </Row>

      <div className="table-toolbar">
        <p className="table-count">
          Showing {paginatedClaims.length} of {filteredClaims.length} filtered
          claims
        </p>
      </div>

      <div className="claims-table-container">
        <table className="claims-table">
          <thead>
            <tr>
              <th>Claimant</th>
              <th>Location</th>
              <th>Type</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan="5" className="text-center">
                  <Spinner animation="border" size="sm" /> Updating...
                </td>
              </tr>
            )}
            {!loading && paginatedClaims.length > 0
              ? paginatedClaims.map((claim) => (
                  <tr
                    key={claim.id}
                    onClick={() => handleRowClick(claim.id)}
                    className="clickable-row"
                  >
                    <td>
                      <span className="claim-name">
                        {claim.name || "Unnamed claimant"}
                      </span>
                      <span className="claim-id">
                        #{String(claim.id).slice(0, 8)}
                      </span>
                    </td>
                    <td>
                      <div className="claim-name">
                        {claim.village || "Village N/A"}
                      </div>
                      <span className="claim-id">
                        {[claim.district, claim.state]
                          .filter(Boolean)
                          .join(" · ") || "Location N/A"}
                      </span>
                    </td>
                    <td>
                      <span className="claim-type">
                        {claim.claim_type || "Individual"}
                      </span>
                    </td>
                    <td>
                      <div
                        className={`status-indicator status-${
                          claim.status || "Pending"
                        }`}
                      >
                        {claim.status || "Pending"}
                      </div>
                    </td>
                    <td>
                      <Dropdown
                        onSelect={(newStatus) =>
                          handleStatusUpdate(claim.id, newStatus)
                        }
                        className="d-inline action-dropdown"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Dropdown.Toggle
                          as="button"
                          className="action-button"
                          title="Change Status"
                        >
                          <PencilSquare />
                        </Dropdown.Toggle>
                        <Dropdown.Menu>
                          <Dropdown.Item eventKey="Approved">
                            Approved
                          </Dropdown.Item>
                          <Dropdown.Item eventKey="Rejected">
                            Rejected
                          </Dropdown.Item>
                          <Dropdown.Item eventKey="Pending">
                            Pending
                          </Dropdown.Item>
                        </Dropdown.Menu>
                      </Dropdown>
                    </td>
                  </tr>
                ))
              : !loading && (
                  <tr>
                    <td colSpan="5">
                      <div className="empty-state">
                        No claims match the current filters. Try clearing
                        filters or add a new claim.
                      </div>
                    </td>
                  </tr>
                )}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <Pagination>
          <Pagination.Prev
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
          />
          {[...Array(totalPages).keys()].map((page) => (
            <Pagination.Item
              key={page + 1}
              active={page + 1 === currentPage}
              onClick={() => setCurrentPage(page + 1)}
            >
              {page + 1}
            </Pagination.Item>
          ))}
          <Pagination.Next
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
          />
        </Pagination>
      )}
    </div>
  );
}

export default ClaimsTable;
