import json
import base64
import re
import boto3

def parse_amount(value: str):
    """Czyści kwotę i zamienia na float."""
    if not value:
        return None

    cleaned = value.replace(" ", "").replace(",", ".")
    cleaned = re.sub(r"[^0-9.]", "", cleaned)

    try:
        return float(cleaned)
    except ValueError:
        return None


def clean_address(raw_address: str):
    """
    Zwraca tylko:
    ulica + kod + miasto
    """
    if not raw_address:
        return None

    lines = [l.strip() for l in raw_address.split("\n") if l.strip() and l.strip() != "-"]

    street = None
    city_line = None

    for line in lines:
        if "ul." in line.lower():
            street = line

        if re.search(r"\d{2}-\d{3}", line):
            city_line = line

    if street and city_line:
        return f"{street}, {city_line}"

    return lines[-1] if lines else None


def extract_fields_from_expense(response):
    """Wyciąga NIP, adres i total z AnalyzeExpense."""
    vat_id = None
    address = None
    total = None
    fallback_amount = None

    for doc in response.get("ExpenseDocuments", []):
        for field in doc.get("SummaryFields", []):

            field_type = field.get("Type", {}).get("Text", "")
            label = (field.get("LabelDetection", {}) or {}).get("Text", "") or ""
            value = (field.get("ValueDetection", {}) or {}).get("Text", "") or ""

            # -------- NIP --------
            if "NIP" in label.upper() and value:
                cleaned = re.sub(r"[^0-9]", "", value)
                if len(cleaned) == 10:
                    vat_id = cleaned

            # -------- ADRES --------
            if field_type in ["RECEIVER_ADDRESS", "ADDRESS"] and not address:
                address = clean_address(value)

            # -------- TOTAL (główne) --------
            if field_type == "TOTAL":
                parsed = parse_amount(value)
                if parsed:
                    total = parsed

            # -------- Fallback brutto --------
            if "brutto" in label.lower() and value:
                parsed = parse_amount(value)
                if parsed:
                    fallback_amount = parsed

    if not total:
        total = fallback_amount

    return vat_id, address, total


def lambda_handler(event, context):
    try:
        headers = event.get("headers", {})
        content_type = headers.get("content-type") or headers.get("Content-Type")

        body = event["body"]

        if event.get("isBase64Encoded", False):
            body = base64.b64decode(body)
        else:
            body = body.encode()

        # --- Multipart parsing ---
        boundary = content_type.split("boundary=")[1]
        parts = body.split(f"--{boundary}".encode())

        pdf_bytes = None
        for part in parts:
            if b"filename=" in part:
                pdf_bytes = part.split(b"\r\n\r\n", 1)[1].rstrip(b"\r\n--")
                break

        if not pdf_bytes:
            raise Exception("No file found in request")

        # --- Textract ---
        textract = boto3.client("textract", region_name="us-east-1")
        response = textract.analyze_expense(Document={"Bytes": pdf_bytes})

        vat_id, address, total = extract_fields_from_expense(response)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "vat_id": vat_id or "",
                "address": address or "",
                "total": float(total) if total else 0.0
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }