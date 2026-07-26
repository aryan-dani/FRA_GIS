import React from "react";
import { Container } from "react-bootstrap";
import "./Footer.css";

function Footer() {
  return (
    <footer className="footer">
      <Container>
        <div className="footer-inner">
          <div>
            <strong className="footer-brand">FRA Atlas</strong>
            <p className="mb-0">
              SIH12508 · Ministry of Tribal Affairs · WebGIS DSS prototype
            </p>
          </div>
          <small>
            Built by <span className="developer-name">Aryan Dani</span> · Team
            Evonex · {new Date().getFullYear()}
          </small>
        </div>
      </Container>
    </footer>
  );
}

export default Footer;
