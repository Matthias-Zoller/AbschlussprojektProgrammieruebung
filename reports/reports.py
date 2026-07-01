from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import tempfile
import os
import pandas as pd


def plot_ekg_matplotlib(df: pd.DataFrame, tmp_path: str) -> None:
    """
    Zeichnet EKG Signal mit Matplotlib und speichert es als PNG.
    Wird für den PDF Export verwendet da kaleido auf Streamlit Cloud
    keinen Chrome Browser findet.

    Args:
        df (pd.DataFrame): DataFrame mit Spalten 'time', 'voltage', 'is_peak'
        tmp_path (str): Pfad zum Speichern der PNG Datei
    """
    fig, ax = plt.subplots(figsize=(12, 3))

    ax.plot(df['time'], df['voltage'], color='#1a56db', linewidth=0.8, label='Signal')

    peaks = df[df['is_peak']]
    ax.scatter(peaks['time'], peaks['voltage'], color='red', s=30, zorder=5, label='R-Peak')

    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Voltage (mV)')
    ax.set_title('ECG Visualization — Lead II')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(tmp_path, dpi=150, bbox_inches='tight')
    plt.close()


def generate_pdf(
    patient: tuple,
    features: dict,
    result: dict,
    ekg_df: pd.DataFrame,
    output_path: str
) -> str:
    """
    Generiert einen professionellen PDF-Bericht für eine EKG-Analyse.

    Erstellt ein PDF-Dokument mit Patientendaten, EKG-Visualisierung,
    Analyseergebnissen und ML-Diagnose.

    Args:
        patient (tuple): Patientendatensatz aus der Datenbank.
                         Format: (id, Vorname, Nachname, Geburtsdatum, Gender)
        features (dict): Dictionary mit den berechneten EKG-Features.
                         Erwartete Schlüssel:
                             - heart_rate (float): Herzfrequenz in bpm
                             - max_heart_rate (float): Max. Herzfrequenz in bpm
                             - hrv (float): Herzratenvariabilität in ms
                             - rr_mean (float): Mittleres RR-Intervall in ms
        result (dict): Dictionary mit dem ML-Diagnoseergebnis.
                       Erwartete Schlüssel:
                           - predicted_class (str): Diagnoseklasse
                           - confidence (float): Konfidenzwert in %
        ekg_df (pd.DataFrame): DataFrame mit EKG Daten (time, voltage, is_peak)
        output_path (str): Dateipfad wo das PDF gespeichert werden soll.

    Returns:
        str: Pfad zur erstellten PDF-Datei.
    """

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#1a56db"),
        spaceAfter=6
    )

    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#1a56db"),
        spaceBefore=12,
        spaceAfter=6
    )

    normal_style = styles["Normal"]

    story = []

    # ── Header ──────────────────────────────────────────
    story.append(Paragraph("EKG ML Analyzer", title_style))
    story.append(Paragraph("Machine Learning supported ECG Analysis", normal_style))
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    story.append(Paragraph(f"Erstellt am: {now}", normal_style))
    story.append(Spacer(1, 0.5*cm))

    # ── Patientendaten ───────────────────────────────────
    story.append(Paragraph("Patientendaten", heading_style))

    patient_data = [
        ["Name:",         f"{patient[1]} {patient[2]}"],
        ["Geburtsdatum:", str(patient[3])],
        ["Geschlecht:",   str(patient[4])],
        ["Patienten-ID:", str(patient[0])],
    ]

    patient_table = Table(patient_data, colWidths=[4*cm, 10*cm])
    patient_table.setStyle(TableStyle([
        ("FONTNAME",       (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",       (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",       (0, 0), (-1, -1), 11),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f0f4ff"), colors.white]),
        ("TOPPADDING",     (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 0.3*cm))

    # ── EKG Grafik ───────────────────────────────────────
    story.append(Paragraph("EKG Visualisierung — Lead II", heading_style))

    # Matplotlib Plot als temporäres PNG speichern
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name

    plot_ekg_matplotlib(ekg_df, tmp_path)
    story.append(Image(tmp_path, width=16*cm, height=6*cm))
    story.append(Spacer(1, 0.3*cm))

    # ── Analyseergebnisse ────────────────────────────────
    story.append(Paragraph("Analyseergebnisse", heading_style))

    analysis_data = [
        ["Parameter",      "Wert"],
        ["Heart Rate",     f"{features['heart_rate']} bpm"],
        ["Max Heart Rate", f"{features['max_heart_rate']} bpm"],
        ["RR Intervall",   f"{features['rr_mean']} ms"],
        ["HRV",            f"{features['hrv']} ms"],
    ]

    analysis_table = Table(analysis_data, colWidths=[7*cm, 7*cm])
    analysis_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#1a56db")),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 11),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.HexColor("#f0f4ff"), colors.white]),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
    ]))
    story.append(analysis_table)
    story.append(Spacer(1, 0.3*cm))

    # ── ML Diagnose ──────────────────────────────────────
    story.append(Paragraph("Machine Learning Diagnose", heading_style))

    ml_data = [
        ["Diagnose",  result["predicted_class"]],
        ["Konfidenz", f"{result['confidence']} %"],
    ]

    ml_table = Table(ml_data, colWidths=[7*cm, 7*cm])
    ml_table.setStyle(TableStyle([
        ("FONTNAME",      (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",      (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 11),
        ("ROWBACKGROUNDS",(0, 0), (-1, -1), [colors.HexColor("#f0f4ff"), colors.white]),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(ml_table)
    story.append(Spacer(1, 0.5*cm))

    # PDF erstellen
    doc.build(story)
    os.unlink(tmp_path)

    return output_path