# FRA Atlas · WebGIS DSS

AI-powered FRA Atlas and WebGIS-based Decision Support System for integrated monitoring of Forest Rights Act (FRA) implementation.

**Live frontend:** [https://fra-atlas-one.vercel.app](https://fra-atlas-one.vercel.app) (Vercel)  
**Backend:** Render (OCR API — set `REACT_APP_API_URL` on Vercel when live)

The **FRA-GIS Platform** is a full-stack web application designed to digitize and streamline the management of claims under the Forest Rights Act (FRA) in India. It serves as a Smart India Hackathon prototype for MoTA’s FRA Atlas / DSS problem statement.


![FRA-GIS Platform Screenshot](URL_TO_SCREENSHOT_HERE) <!-- Add a screenshot of your application here -->

## ✨ Key Features

- **🤖 AI-Powered OCR**: Utilizes **Google Vision API** to automatically extract and populate claim details from uploaded documents (PDFs/images), minimizing manual data entry and errors.
- **🗺️ Interactive GIS Dashboard**: Features a dynamic dashboard with key statistics and an integrated **WebGIS map** to visualize the geographical distribution of claims, providing an at-a-glance overview of the landscape.
- **📊 Advanced Data Management**: A comprehensive data table allows users to search, filter, sort, and manage thousands of claims. Includes an **"Export to CSV"** functionality for offline analysis.
- **📈 In-Depth Analytics**: A dedicated analytics page with interactive charts provides deep insights into claim trends by status, type, location, and over time.
- **✅ Responsive & Modern UI**: Built with React and React Bootstrap, the user interface is designed to be clean, responsive, and highly functional, ensuring a seamless experience on any device.
- **⚙️ Full-Stack Architecture**: A robust backend built with Python and Flask supports the frontend, handling data processing, API requests, and database interactions.

## 🛠️ Tech Stack

- **Frontend**: React, React Bootstrap, Chart.js, React Router, Axios
- **Backend**: Python, Flask
- **Database**: Firebase Firestore (Spark / free tier)
- **APIs & Services**: Google Vision API
- **Deployment**: GitHub Actions for CI/CD

## 🚀 Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

- Node.js and npm
- Python and pip
- A Firebase project with Firestore enabled (Spark plan works)

### Installation

1.  **Clone the repo**
    ```sh
    git clone https://github.com/aryan-dani/FRA-GIS.git
    ```
2.  **Configure Frontend env**
    ```sh
    cd frontend
    cp .env.example .env
    ```
    Fill in the Firebase web app config values from the Firebase console.
3.  **Install Frontend Dependencies**
    ```sh
    npm install
    ```
4.  **Configure Backend env**
    ```sh
    cd ../backend
    cp .env.example .env
    ```
    Place a Firebase service account JSON at `backend/firebase-service-account.json`
    (or set `FIREBASE_CREDENTIALS_PATH` to its path).
5.  **Install Backend Dependencies**
    ```sh
    pip install -r requirements.txt
    ```

### Running the Application

1.  **Start the Backend Server**
    ```sh
    # From the 'backend' directory
    python app.py
    ```
    The API runs on `http://localhost:5001`.
2.  **Start the Frontend Development Server**
    ```sh
    # From the 'frontend' directory
    npm start
    ```
    The application will be available at `http://localhost:3000`.

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

## 👤 Contact

Aryan Dani - [LinkedIn](https://www.linkedin.com/in/aryan-dani/)

Project Link: [https://github.com/aryan-dani/FRA-GIS](https://github.com/aryan-dani/FRA-GIS)
