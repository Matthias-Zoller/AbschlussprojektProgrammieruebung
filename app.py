import streamlit as st
import pandas as pd
from database.database_connection import *
from ekg_processing.ekg import EKGdata
from pathlib import Path
from machine_learning.prediction import Prediction
from reports.reports import generate_pdf
from datetime import date


def main():

    st.set_page_config(
        page_title="EKG ML Analyzer",
        layout="wide"
    )

    st.title("EKG ML Analyzer")

    menu = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Patients",
        ]
    )

    if menu == "Dashboard":
        dashboard_page()
    elif menu == "Patients":
        patients_page()


# ------------------------------------------------------
# Dashboard
# ------------------------------------------------------

def dashboard_page():

    st.header("Dashboard")

    persons_df = get_all_patients()

    if persons_df.empty:
        st.warning("Keine Patienten vorhanden. Bitte zuerst einen Patienten anlegen.")
        return

    persons = persons_df.to_dict("records")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Patient Information")
        selected_patient = st.selectbox(
            "Select Patient",
            options=persons,
            format_func=lambda p: f"{p['Vorname']} {p['Nachname']}"
        )
        patient_id = selected_patient["id"]

        st.markdown(f"**Name:** {selected_patient['Vorname']} {selected_patient['Nachname']}")
        st.markdown(f"**Date of Birth:** {selected_patient['Geburtsdatum']}")
        st.markdown(f"**Gender:** {selected_patient['Gender']}")

    with col2:
        st.subheader("ECG File Upload")
        uploaded_file = st.file_uploader(
            "Upload ECG file (.csv)",
            type=["csv"]
        )

        if uploaded_file is not None:
            upload_dir = Path("data/")
            upload_dir.mkdir(parents=True, exist_ok=True)
            file_path = upload_dir / uploaded_file.name

            if not st.session_state.get(f"uploaded_{uploaded_file.name}"):
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                create_ekg_data(str(file_path), patient_id)
                st.session_state[f"uploaded_{uploaded_file.name}"] = True
                st.success(f"Datei gespeichert: {file_path}")

    # EKG auswählen
    st.divider()
    ekgs_df = get_ekgs_by_patients(patient_id)

    if ekgs_df.empty:
        st.info("Noch keine EKG-Daten für diesen Patienten vorhanden.")
        return

    ekgs = ekgs_df.to_dict("records")

    selected_ekg = st.selectbox(
        "EKG-Aufnahme auswählen",
        options=ekgs,
        format_func=lambda e: f"EKG {e['idekg_records']} — {e['recording_date']}"
    )

    # EKG laden und analysieren
    try:
        ekg = EKGdata(selected_ekg["file_path"])
    except Exception as ex:
        st.error(f"Fehler beim Laden der EKG-Datei: {ex}")
        return

    # Plot
    st.subheader("ECG Visualization — Lead II")
    fig = ekg.plot_time_series()
    st.plotly_chart(fig, use_container_width=True)

    # Feature Cards
    st.subheader("Analysis Results")
    features = ekg.get_all_features()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Heart Rate",     f"{features['heart_rate']} bpm")
    c2.metric("Max Heart Rate", f"{features['max_heart_rate']} bpm")
    c3.metric("RR Interval",    f"{features['rr_mean']} ms")
    c4.metric("HRV",            f"{features['hrv']} ms")

    # ML Diagnose
    st.subheader("Machine Learning Diagnosis")
    result = None

    try:
        prediction = Prediction()
        result = prediction.predict(features)

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**Predicted Diagnosis**")
            st.markdown(f"### {result['predicted_class']}")

        with col_b:
            st.markdown("**Confidence Score**")
            st.markdown(f"### {result['confidence']} %")
            st.progress(result['confidence'] / 100)

        # Automatisch speichern
        ekg_key = f"saved_ekg_{selected_ekg['idekg_records']}"
        if not st.session_state.get(ekg_key):
            result_data = {
                "ekg_id":          int(selected_ekg["idekg_records"]),
                "heart_rate":      float(features["heart_rate"]),
                "max_heart_rate":  float(features["max_heart_rate"]),
                "rr_mean":         float(features["rr_mean"]),
                "rr_std":          float(features["hrv"]),
                "hrv":             float(features["hrv"]),
                "predicted_class": str(result["predicted_class"]),
                "confidence":      float(result["confidence"])
            }
            result_id = save_analysis_result(result_data)
            st.session_state[ekg_key] = result_id
            st.success("Analyse automatisch gespeichert!")

        st.session_state["result_id"] = st.session_state.get(ekg_key)

    except FileNotFoundError as e:
        st.error(f"Modell nicht gefunden: {e}")
    except Exception as e:
        st.error(f"Fehler bei der Diagnose: {e}")

    # PDF generieren
    if result is not None:
        st.divider()
        st.subheader("Report")

        if st.button("Generate PDF Report"):
            report_dir = Path("reports/")
            report_dir.mkdir(parents=True, exist_ok=True)

            pdf_path = str(report_dir / f"report_patient_{patient_id}_{selected_ekg['idekg_records']}.pdf")

            patient_tuple = (
                selected_patient["id"],
                selected_patient["Vorname"],
                selected_patient["Nachname"],
                selected_patient["Geburtsdatum"],
                selected_patient["Gender"]
            )

            generate_pdf(
                patient=patient_tuple,
                features=features,
                result=result,
                ekg_df=ekg.df,
                output_path=pdf_path
            )

            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="Download Report",
                    data=f,
                    file_name=f"ekg_report_{patient_id}.pdf",
                    mime="application/pdf"
                )

            save_report({
                "ekg_id":       int(selected_ekg["idekg_records"]),
                "diagnosis_id": st.session_state["result_id"],
                "pdf_path":     pdf_path
            })


# ------------------------------------------------------
# Patienten
# ------------------------------------------------------

def patients_page():

    st.header("Patients")
    st.subheader("Neuen Patienten anlegen")

    first_name = st.text_input("First Name")
    last_name  = st.text_input("Last Name")
    birth_date = st.date_input(
        "Date of Birth",
        value=date(1990, 1, 1),
        min_value=date(1900, 1, 1),
        max_value=date.today()
    )
    sex = st.selectbox("Gender", ["Male", "Female", "Diverse"])

    if st.button("Create Patient"):
        patient_data = {
            "vorname":      first_name,
            "nachname":     last_name,
            "geburtsdatum": birth_date,
            "gender":       sex
        }
        create_patient(patient_data)
        st.success("Patient erfolgreich angelegt!")


if __name__ == "__main__":
    main()