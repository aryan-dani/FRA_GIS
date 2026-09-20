import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { Form, Button, Spinner, ProgressBar } from "react-bootstrap";
import { toast } from "react-toastify";

const API_URL = (
  process.env.REACT_APP_API_URL ||
  (process.env.NODE_ENV === "development" ? "http://localhost:5001" : "")
).replace(/\/$/, "");

function UploadForm() {
  const [file, setFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      toast.warn("Please select a file to upload.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setIsProcessing(true);
    setUploadProgress(0);

    try {
      const response = await axios.post(
        `${API_URL}/api/process-document`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / (progressEvent.total || 1)
            );
            setUploadProgress(percentCompleted);
          },
        }
      );

      // On success, navigate to the review page with the extracted data
      toast.success(
        "Document processed successfully! Redirecting to review page..."
      );
      setTimeout(() => {
        navigate("/add-claim", { state: { extractedData: response.data } });
      }, 1500);
    } catch (err) {
      toast.error(
        err.response?.data?.error || "An error occurred during file processing."
      );
      setIsProcessing(false);
    }
  };

  return (
    <div className="upload-form">
      <Form onSubmit={handleSubmit}>
        <Form.Group controlId="formFile" className="mb-3">
          <Form.Label>Select PDF or Image File</Form.Label>
          <Form.Control
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.tiff"
            onChange={handleFileChange}
            disabled={isProcessing}
          />
        </Form.Group>

        {isProcessing && (
          <ProgressBar
            animated
            now={uploadProgress}
            label={
              uploadProgress < 100
                ? `${uploadProgress}% Uploaded`
                : "Processing..."
            }
            className="mb-3"
          />
        )}

        <Button
          variant="primary"
          type="submit"
          disabled={isProcessing || !file}
        >
          {isProcessing ? (
            <>
              <Spinner
                as="span"
                animation="border"
                size="sm"
                role="status"
                aria-hidden="true"
              />
              <span className="ms-2">Processing Document...</span>
            </>
          ) : (
            "Upload and Review"
          )}
        </Button>
      </Form>
    </div>
  );
}

export default UploadForm;
