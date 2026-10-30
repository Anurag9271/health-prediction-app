"""External AI API integration (Google Gemini REST API)."""
import requests

import config
import validators

PENDING_REMARK = "Pending - AI prediction unavailable"


class AIServiceError(Exception):
    """Raised when the AI API call fails for any reason."""


def build_prompt(data: dict) -> str:
    age = validators.calculate_age(data["dob"])
    return (
        "You are a clinical decision-support assistant. Based on the blood test results below, "
        "predict the most likely health condition or disease risk (for example: diabetes / "
        "pre-diabetes, anaemia, polycythaemia, hypercholesterolaemia, cardiovascular risk, or "
        "'no significant risk').\n\n"
        f"Patient age: {age} years\n"
        f"Fasting glucose: {data['glucose']} mg/dL\n"
        f"Haemoglobin: {data['haemoglobin']} g/dL\n"
        f"Total cholesterol: {data['cholesterol']} mg/dL\n\n"
        "Reply in plain text, maximum 35 words, in this form: "
        "'<Risk level>: <possible condition(s)>. <one short recommendation>.' "
        "Do not use markdown. Do not give a definitive diagnosis."
    )


def predict_health_risk(data: dict) -> str:
    """Call the AI API and return the prediction text for the Remarks field."""
    if not config.GEMINI_API_KEY:
        raise AIServiceError("GEMINI_API_KEY is not configured (see .env.example).")

    url = config.GEMINI_URL.format(model=config.GEMINI_MODEL)
    headers = {"Content-Type": "application/json", "x-goog-api-key": config.GEMINI_API_KEY}
    payload = {
        "contents": [{"parts": [{"text": build_prompt(data)}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 512},
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=(10, config.AI_TIMEOUT_SECONDS))
        response.raise_for_status()
        body = response.json()
        text = body["candidates"][0]["content"]["parts"][0]["text"].strip()
    except requests.exceptions.Timeout:
        raise AIServiceError("The AI service timed out.") from None
    except requests.exceptions.HTTPError as exc:
        detail = ""
        try:
            detail = exc.response.json()["error"]["message"]
        except (ValueError, KeyError, TypeError):
            pass
        raise AIServiceError(f"AI service returned HTTP {exc.response.status_code}. {detail}") from None
    except requests.exceptions.RequestException:
        raise AIServiceError("Could not reach the AI service (network error).") from None
    except (KeyError, IndexError, ValueError):
        raise AIServiceError("The AI service returned an unexpected response.") from None

    if not text:
        raise AIServiceError("The AI service returned an empty prediction.")
    return text
