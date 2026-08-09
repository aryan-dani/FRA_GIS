import React from "react";
import { Container } from "react-bootstrap";
import "./Footer.css";

function Footer() {
  return (
    <footer className="footer">
      <Container fluid="xl">
        <div className="footer-inner">
          <div>
            <strong className="footer-brand">FRA Atlas</strong>
            <p className="mb-0">
              SIH12508 · Ministry of Tribal Affairs · WebGIS DSS prototype
            </p>
          </div>
          <small>
            Built by{" "}
            <a
              className="developer-name"
              href="https://www.aryandani.com"
              target="_blank"
              rel="noopener noreferrer"
            >
              Aryan Dani
            </a>{" "}
            · {new Date().getFullYear()}
          </small>
        </div>
      </Container>
    </footer>
  );
}

export default Footer;
