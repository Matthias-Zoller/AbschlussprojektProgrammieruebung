# EKG ML Analyzer

Dieses Repository beinhaltet den Code für das Abschlussprojekt: Eine Streamlit-Webanwendung für Kardiologen zur Verwaltung von Patienten und automatisierten Analyse von EKG-Daten mithilfe von Machine Learning.

🌐 **Live App:** https://abschlussprojektprogrammieruebung-eg3e34f2nqjrrkx9b5jgbd.streamlit.app/

---

## Repository herunterladen

Zuerst das Repository klonen:

```bash
git clone https://github.com/Matthias-Zoller/AbschlussprojektProgrammieruebung.git
```

Dann in den Projektordner wechseln:

```bash
cd AbschlussprojektProgrammieruebung
```

---

## Voraussetzungen

Benötigt:

- Python 3.11+
- PDM
- Git

### PDM installieren

```bash
curl -sSL https://pdm-project.org/install-pdm.py | python3 -
```

---

## Virtuelle Umgebung aktivieren (optional)

```bash
pdm venv activate
```

Windows (PowerShell):

```powershell
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned)
& .venv\Scripts\Activate.ps1
```

---

## Pakete installieren

```bash
pdm install
```

Falls die Pakete manuell installiert werden müssen:

```bash
pdm add streamlit sqlalchemy pandas numpy scipy scikit-learn plotly reportlab joblib matplotlib psycopg2-binary
```

---

## Datenbank einrichten (Supabase)

Die App verwendet **Supabase** als Cloud-Datenbank (PostgreSQL).

1. Account erstellen auf [supabase.com](https://supabase.com)
2. Neues Projekt erstellen
3. Folgende Tabellen anlegen:

```sql
CREATE TABLE patient (
    id SERIAL PRIMARY KEY,
    "Vorname" VARCHAR(45),
    "Nachname" VARCHAR(45),
    "Geburtsdatum" VARCHAR(45),
    "Gender" VARCHAR(45)
);

CREATE TABLE ekg_records (
    idekg_records SERIAL PRIMARY KEY,
    file_path VARCHAR(255),
    sampling_rate INT,
    recording_date TIMESTAMP,
    patient_id INT,
    FOREIGN KEY (patient_id) REFERENCES patient(id)
);

CREATE TABLE diagnosis_result (
    iddiagnosis_result SERIAL PRIMARY KEY,
    ekg_id INT,
    heart_rate DOUBLE PRECISION,
    max_heart_rate INT,
    rr_mean DOUBLE PRECISION,
    rr_std DOUBLE PRECISION,
    hrv DOUBLE PRECISION,
    predicted_class VARCHAR(45),
    confidence DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ekg_id) REFERENCES ekg_records(idekg_records)
);

CREATE TABLE reports (
    idreports SERIAL PRIMARY KEY,
    ekg_id INT,
    diagnosis_id INT,
    pdf_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ekg_id) REFERENCES ekg_records(idekg_records),
    FOREIGN KEY (diagnosis_id) REFERENCES diagnosis_result(iddiagnosis_result)
);
```

### Datenbankverbindung konfigurieren

Eine Datei `.streamlit/secrets.toml` erstellen:

```toml
[connections.supabase]
url = "postgresql://postgres.<project-id>:<passwort>@aws-0-eu-west-3.pooler.supabase.com:5432/postgres"
```

---

## ML-Modell trainieren

Vor dem ersten Start muss das Machine Learning Modell trainiert werden.

EKG-Trainingsdaten (CSV-Dateien) in den `data/` Ordner legen. Die Dateinamen müssen das Label enthalten:

Dann das Modell trainieren:

```bash
pdm run python -m machine_learning.model_trainer
```

Das trainierte Modell wird unter `machine_learning/models/ekg_model.pkl` gespeichert.

---

## Streamlit App starten

```bash
pdm run streamlit run app.py
```

Die App öffnet sich automatisch im Browser unter `http://localhost:8501`.

---

## Deployment auf Streamlit Cloud

1. Repository auf GitHub pushen
2. Auf [share.streamlit.io](https://share.streamlit.io) anmelden
3. Repository auswählen, Main file: `app.py`
4. Unter **Advanced settings → Secrets** einfügen:

```toml
[connections.supabase]
url = "postgresql://postgres.<project-id>:<passwort>@aws-0-eu-west-3.pooler.supabase.com:5432/postgres"
```

5. Deploy klicken

---

## Über diese App

Diese Anwendung wurde mit **Streamlit** entwickelt und bietet folgende Hauptfunktionen:

1. **Patientenverwaltung:** Patienten können angelegt und ausgewählt werden.
2. **EKG Upload:** CSV-Dateien können hochgeladen und einem Patienten zugeordnet werden.
3. **Automatische Analyse:** Das EKG-Signal wird verarbeitet, R-Peaks werden erkannt und Features wie Herzfrequenz, HRV und RR-Intervall werden berechnet.
4. **Machine Learning Diagnose:** Ein trainiertes Random Forest Modell klassifiziert das EKG automatisch (Normal, Tachykardie, Bradykardie, Arrhythmie, Verrauscht) und gibt einen Konfidenzwert aus.
5. **PDF-Report:** Ein professioneller Bericht mit EKG-Visualisierung, Analyseergebnissen und ML-Diagnose kann generiert und heruntergeladen werden.