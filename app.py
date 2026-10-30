"""Health Prediction Application - Streamlit front end."""
import pandas as pd
import streamlit as st

import ai_service
import database
import validators

st.set_page_config(page_title="Health Prediction App", page_icon="🩺", layout="wide")
database.init_db()

FIELD_ORDER = ["full_name", "dob", "email", "glucose", "haemoglobin", "cholesterol"]


# ---------- helpers ----------
def get_remarks(data: dict) -> tuple[str, str | None]:
    """Return (remarks, warning). Falls back to a pending note if the AI call fails."""
    try:
        with st.spinner("Contacting AI health API..."):
            return ai_service.predict_health_risk(data), None
    except ai_service.AIServiceError as exc:
        return ai_service.PENDING_REMARK, f"AI prediction failed: {exc}"


def show_errors(errors: dict) -> None:
    st.error("The record was NOT saved. Please fix the following:")
    for key in FIELD_ORDER:
        if key in errors:
            st.markdown(f"- {errors[key]}")


def flash(kind: str, message: str) -> None:
    st.session_state["flash"] = (kind, message)


def show_flash() -> None:
    if "flash" in st.session_state:
        kind, message = st.session_state.pop("flash")
        getattr(st, kind)(message)


def records_dataframe(records: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(records)
    df = df[["id", "full_name", "dob", "email", "glucose", "haemoglobin", "cholesterol", "remarks"]]
    return df.rename(columns={
        "id": "ID", "full_name": "Full Name", "dob": "Date of Birth", "email": "Email",
        "glucose": "Glucose (mg/dL)", "haemoglobin": "Haemoglobin (g/dL)",
        "cholesterol": "Cholesterol (mg/dL)", "remarks": "Remarks (AI)",
    })


def patient_label(p: dict) -> str:
    return f"#{p['id']} - {p['full_name']} ({p['email']})"


# ---------- pages ----------
def page_add() -> None:
    st.header("Add Patient Record")
    show_flash()
    st.caption("Date of birth format: dd/mm/yyyy. Remarks are generated automatically by the AI API.")

    n = st.session_state.setdefault("add_form_id", 0)
    with st.form(f"add_form_{n}"):
        c1, c2 = st.columns(2)
        full_name = c1.text_input("Full Name", key=f"name_{n}")
        dob = c2.text_input("Date of Birth (dd/mm/yyyy)", key=f"dob_{n}")
        email = st.text_input("Email Address", key=f"email_{n}")
        g, h, c = st.columns(3)
        glucose = g.text_input("Glucose (mg/dL)", key=f"glu_{n}")
        haemoglobin = h.text_input("Haemoglobin (g/dL)", key=f"hb_{n}")
        cholesterol = c.text_input("Cholesterol (mg/dL)", key=f"chol_{n}")
        submitted = st.form_submit_button("Save & Predict", type="primary")

    if not submitted:
        return

    result = validators.validate_patient(full_name, dob, email, glucose, haemoglobin, cholesterol)
    if not result.is_valid:
        show_errors(result.errors)
        return

    remarks, warning = get_remarks(result.cleaned)
    try:
        new_id = database.create_patient(result.cleaned, remarks)
    except database.DuplicateEmailError as exc:
        st.error(f"The record was NOT saved. {exc}")
        return

    flash("success", f"Record #{new_id} saved for {result.cleaned['full_name']}. Remarks: {remarks}")
    if warning:
        st.session_state["flash_warning"] = warning
    st.session_state["add_form_id"] = n + 1  # reset the form
    st.rerun()


def page_records() -> None:
    st.header("Patient Records")
    show_flash()
    records = database.get_all_patients()
    if not records:
        st.info("No records yet. Use 'Add Patient' to create one.")
        return

    search = st.text_input("Search by name or email").strip().lower()
    if search:
        records = [r for r in records if search in r["full_name"].lower() or search in r["email"].lower()]
    st.caption(f"Showing {len(records)} record(s)")
    if records:
        st.dataframe(records_dataframe(records), hide_index=True)
    else:
        st.warning("No records match your search.")


def page_edit_delete() -> None:
    st.header("Edit / Delete Record")
    show_flash()
    records = database.get_all_patients()
    if not records:
        st.info("No records available.")
        return

    by_label = {patient_label(p): p for p in records}
    selected = by_label[st.selectbox("Select a record", list(by_label))]
    pid = selected["id"]

    edit_tab, delete_tab = st.tabs(["Edit", "Delete"])

    with edit_tab:
        with st.form(f"edit_form_{pid}"):
            c1, c2 = st.columns(2)
            full_name = c1.text_input("Full Name", value=selected["full_name"])
            dob = c2.text_input("Date of Birth (dd/mm/yyyy)", value=selected["dob"])
            email = st.text_input("Email Address", value=selected["email"])
            g, h, c = st.columns(3)
            glucose = g.text_input("Glucose (mg/dL)", value=f"{selected['glucose']:g}")
            haemoglobin = h.text_input("Haemoglobin (g/dL)", value=f"{selected['haemoglobin']:g}")
            cholesterol = c.text_input("Cholesterol (mg/dL)", value=f"{selected['cholesterol']:g}")
            regenerate = st.checkbox("Re-generate AI remarks", value=False)
            submitted = st.form_submit_button("Update Record", type="primary")

        if submitted:
            result = validators.validate_patient(full_name, dob, email, glucose, haemoglobin, cholesterol)
            if not result.is_valid:
                show_errors(result.errors)
            else:
                new = result.cleaned
                clinical_changed = any(new[k] != selected[k] for k in ("dob", "glucose", "haemoglobin", "cholesterol"))
                needs_ai = clinical_changed or regenerate or selected["remarks"] == ai_service.PENDING_REMARK
                remarks, warning = (get_remarks(new) if needs_ai else (selected["remarks"], None))
                try:
                    database.update_patient(pid, new, remarks)
                except database.DuplicateEmailError as exc:
                    st.error(f"Update failed. {exc}")
                else:
                    flash("success", f"Record #{pid} updated.")
                    if warning:
                        st.session_state["flash_warning"] = warning
                    st.rerun()

    with delete_tab:
        st.warning(f"You are about to permanently delete: **{patient_label(selected)}**")
        confirm = st.checkbox("I confirm I want to delete this record", key=f"confirm_{pid}")
        if st.button("Delete Record", type="primary", disabled=not confirm):
            database.delete_patient(pid)
            flash("success", f"Record #{pid} deleted.")
            st.rerun()


# ---------- layout ----------
st.title("🩺 Health Prediction Application")
st.caption("AI-generated remarks are indicative only and are not a medical diagnosis.")

if "flash_warning" in st.session_state:
    st.warning(st.session_state.pop("flash_warning"))

page = st.sidebar.radio("Navigation", ["Add Patient", "Patient Records", "Edit / Delete"])
if page == "Add Patient":
    page_add()
elif page == "Patient Records":
    page_records()
else:
    page_edit_delete()
