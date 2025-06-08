# Document Ingestion System

A FastAPI-based backend for ingesting, extracting, classifying, and routing documents using an agentic framework.

## Setup

1.  **Clone the repository**:

    git clone &lt;repository-url&gt;\\

    cd document_ingestion_system

2.  **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up environment variables**: Copy `.env.example` to `.env` and update values as needed:

    ```bash
    cp .env.example .env
    ```

4.  **Set up the database**: The application uses SQLite by default (`sqlite:///documents.db`). For production, consider using PostgreSQL by updating `DATABASE_URL` in `.env` or `config/settings.yaml`.

5.  **Set up RabbitMQ**: Install RabbitMQ on Windows:

    -   Download and install Erlang: https://www.erlang.org/downloads

    -   Download and install RabbitMQ: https://www.rabbitmq.com/install-windows.html

    -   Start RabbitMQ service:

        ```bash
        rabbitmq-service start
        ```

    -   Enable RabbitMQ management plugin (optional, for monitoring):

        ```bash
        rabbitmq-plugins enable rabbitmq_management
        ```

    -   Verify RabbitMQ is running by accessing http://localhost:15672 (default user: guest, password: guest). Configure RabbitMQ settings in `.env` or `config/settings.yaml` (default: `localhost:5672`, user `guest`, password `guest`).

6.  **Set up Tesseract for OCR**: Install Tesseract on Windows:

    -   Download and install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
    -   Add Tesseract to your system PATH or specify its path in `pytesseract.pytesseract.tesseract_cmd` if needed. Ensure `pytesseract` and `Pillow` are installed via `requirements.txt`.

7.  **Set up email webhook** (e.g., SendGrid Inbound Parse):

    -   Configure your email service to forward incoming emails to `http://localhost:8000/ingest/email`.
    -   For SendGrid, set up an Inbound Parse webhook (see https://docs.sendgrid.com/for-developers/parsing-email/setting-up-the-inbound-parse-webhook).
    -   Ensure the webhook sends a JSON payload with `from`, `subject`, and `attachments` (base64-encoded).

8.  **Run the application**:

    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```

9.  **Access the health-check endpoint**: Open `http://localhost:8000/health` in a browser or use `curl`:

    ```bash
    curl http://localhost:8000/health
    ```

10. **Upload a document**: Use the `/ingest/upload` endpoint to upload a file:

    ```bash
    curl -X POST -F "file=@/path/to/your/file.jpg" http://localhost:8000/ingest/upload
    ```

11. **Process an email**: Test the email webhook by sending a POST request to `/ingest/email`:

    ```bash
    curl -X POST -H "Content-Type: application/json" -d '{
        "from_email": "sender@example.com",
        "subject": "Test Invoice",
        "attachments": [
            {
                "filename": "invoice.jpg",
                "content_type": "image/jpeg",
                "content": "'$(base64 /path/to/invoice.jpg)'"
            }
        ]
    }' http://localhost:8000/ingest/email
    ```

12. **Track document status**: Use the `/documents/{doc_id}` endpoint to check a document’s status:

    ```bash
    curl http://localhost:8000/documents/1
    ```

13. **Override document type or destination**: Use the `/documents/{doc_id}/override` endpoint to update one or more fields (type, confidence, destination):

    ```bash
    curl -X PUT -H "Content-Type: application/json" -d '{"destination": "archive"}' http://localhost:8000/documents/1/override
    ```

## Configuration

-   Environment variables are loaded from `.env`.
-   Additional settings in `config/settings.yaml`.

## Database

-   Uses SQLAlchemy for ORM.
-   SQLite is used for development; PostgreSQL is recommended.
-   The `documents` table is created automatically on startup.

## Message Bus

-   Uses RabbitMQ for event-driven communication.
-   Configure RabbitMQ in `.env` or `config/settings.yaml`.

## Ingestor Service

-   **File Uploads**: Handles uploads via `POST /ingest/upload`.
-   **Email Ingestion**: Processes email attachments via `POST /ingest/email`.
-   Stores files in `uploads/` and metadata in the database.
-   Publishes `doc.received` events to RabbitMQ.
-   The Ingestor Agent assigns priorities based on metadata.

## Extractor Agent

-   Subscribes to `doc.received` events.
-   Performs OCR using `pytesseract`.
-   Publishes `doc.text` events.

## Classifier Agent

-   Subscribes to `doc.text` events.
-   Uses a rule-based classifier.
-   Publishes `doc.type` events.

## Router Agent

-   Subscribes to `doc.type` events.
-   Maps types to destinations.
-   Publishes `doc.routed` events.

## API Endpoints

-   **Health Check**: `GET /health`
-   **Upload Document**: `POST /ingest/upload`
-   **Email Webhook**: `POST /ingest/email`
-   **Document Status**: `GET /documents/{id}`
-   **Manual Override**: `PUT /documents/{id}/override` (supports partial updates for type, confidence, destination)

## Notes

-   Supports image files (JPG, PNG). PDF support requires `pdf2image`.
-   Mock NLP, Classifier, and Router services. Use LLMs or APIs in production.
-   **Email Webhook**: The `/ingest/email` endpoint expects a JSON payload with attachments in base64 format.
-   **Override Endpoint**: Allows partial updates; specify only the fields to change.

## Next Steps

-   Add monitoring and error handling.
-   Implement authentication for API endpoints.
-   Support PDF attachments in email ingestion.
