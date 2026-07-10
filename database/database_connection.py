import streamlit as st
from sqlalchemy import text
from datetime import date


def get_conn():
    """
    Stellt eine Verbindung zur Supabase PostgreSQL Datenbank her
    über Streamlit Connection (nutzt secrets.toml Konfiguration).

    Returns:
        st.connection: Aktive Datenbankverbindung.
    """
    return st.connection("supabase", type="sql")


def get_all_patients():
    """
    Gibt alle Patienten aus der Datenbank zurück.

    Returns:
        pd.DataFrame: DataFrame mit allen Patientendatensätzen.
                      Spalten: id, Vorname, Nachname, Geburtsdatum, Gender
    """
    conn = get_conn()
    return conn.query('SELECT * FROM patient;', ttl=0)


def create_patient(patient_dict):
    """
    Legt einen neuen Patienten in der Datenbank an.

    Args:
        patient_dict (dict): Dictionary mit Patientendaten.
            Erwartete Schlüssel:
                - vorname (str): Vorname des Patienten
                - nachname (str): Nachname des Patienten
                - geburtsdatum (str | date): Geburtsdatum im Format YYYY-MM-DD
                - gender (str): Geschlecht des Patienten

    Returns:
        None
    """
    conn = get_conn()
    with conn.session as s:
        sql = text("""
            INSERT INTO patient ("Vorname", "Nachname", "Geburtsdatum", "Gender")
            VALUES (:vorname, :nachname, :geburtsdatum, :gender)
        """)
        s.execute(sql, {
            "vorname":      patient_dict['vorname'],
            "nachname":     patient_dict['nachname'],
            "geburtsdatum": patient_dict['geburtsdatum'],
            "gender":       patient_dict['gender']
        })
        s.commit()


def get_patient_by_id(patient_id: int):
    """
    Gibt einen einzelnen Patienten anhand seiner ID zurück.

    Args:
        patient_id (int): Die ID des gesuchten Patienten.

    Returns:
        pd.DataFrame: DataFrame mit dem Patientendatensatz oder leer wenn nicht gefunden.
    """
    conn = get_conn()
    return conn.query(f'SELECT * FROM patient WHERE id = {patient_id};')


def create_ekg_data(data_name: str, patient_id: int):
    """
    Legt einen neuen EKG-Datensatz in der Datenbank an und verknüpft
    ihn mit einem Patienten.

    Args:
        data_name (str): Dateipfad zur gespeicherten CSV-Datei.
        patient_id (int): ID des Patienten dem das EKG zugeordnet wird.

    Returns:
        None
    """
    conn = get_conn()
    with conn.session as s:
        sql = text("""
            INSERT INTO ekg_records (file_path, recording_date, patient_id)
            VALUES (:data_name, :recording_date, :patient_id)
        """)
        s.execute(sql, {
            "data_name":      data_name,
            "recording_date": date.today(),
            "patient_id":     patient_id
        })
        s.commit()


def get_ekgs_by_patients(patient_id: int):
    """
    Gibt alle EKG-Datensätze eines bestimmten Patienten zurück.

    Args:
        patient_id (int): ID des Patienten.

    Returns:
        pd.DataFrame: DataFrame mit allen EKG-Datensätzen des Patienten.
                      Spalten: idekg_records, file_path, recording_date, patient_id
    """
    conn = get_conn()
    return conn.query(f'SELECT * FROM ekg_records WHERE patient_id = {patient_id};')


def save_analysis_result(result_data: dict) -> int:
    """
    Speichert das Ergebnis einer EKG-Analyse in der Datenbank.

    Args:
        result_data (dict): Dictionary mit allen Analyseergebnissen.
            Erwartete Schlüssel:
                - ekg_id (int): ID des analysierten EKGs
                - heart_rate (float): Durchschnittliche Herzfrequenz in bpm
                - max_heart_rate (float): Maximale Herzfrequenz in bpm
                - rr_mean (float): Mittleres RR-Intervall in ms
                - rr_std (float): Standardabweichung der RR-Intervalle in ms
                - hrv (float): Herzratenvariabilität in ms
                - predicted_class (str): ML-Diagnoseklasse
                - confidence (float): Konfidenzwert des ML-Modells in %

    Returns:
        int: ID des neu erstellten Analysedatensatzes.
    """
    conn = get_conn()
    with conn.session as s:
        sql = text("""
            INSERT INTO diagnosis_result
            (ekg_id, heart_rate, max_heart_rate, rr_mean, rr_std, hrv, predicted_class, confidence)
            VALUES
            (:ekg_id, :heart_rate, :max_heart_rate, :rr_mean, :rr_std, :hrv, :predicted_class, :confidence)
            RETURNING iddiagnosis_result
        """)
        result = s.execute(sql, result_data)
        s.commit()
        return result.fetchone()[0]


def get_results_by_ekg_id(ekg_id: int):
    """
    Gibt das Analyseergebnis für ein bestimmtes EKG zurück.

    Args:
        ekg_id (int): ID des EKGs.

    Returns:
        pd.DataFrame: DataFrame mit dem Analyseergebnis oder leer wenn nicht gefunden.
    """
    conn = get_conn()
    return conn.query(f'SELECT * FROM diagnosis_result WHERE ekg_id = {ekg_id};')


def save_report(report_data: dict) -> int:
    """
    Speichert einen generierten PDF-Bericht in der Datenbank.

    Args:
        report_data (dict): Dictionary mit den Report-Daten.
            Erwartete Schlüssel:
                - ekg_id (int): ID des EKGs
                - diagnosis_id (int): ID der Diagnose
                - pdf_path (str): Pfad zur PDF-Datei

    Returns:
        int: ID des neu erstellten Report-Eintrags.
    """
    conn = get_conn()
    with conn.session as s:
        sql = text("""
            INSERT INTO reports (ekg_id, diagnosis_id, pdf_path)
            VALUES (:ekg_id, :diagnosis_id, :pdf_path)
            RETURNING idreports
        """)
        result = s.execute(sql, report_data)
        s.commit()
        return result.fetchone()[0]


if __name__ == "__main__":
    st.write("Datenbank-Service bereit.")