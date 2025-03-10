# IMPORTS
import fitz  # PyMuPDF pour extraire le texte natif
import pytesseract  # Tesseract pour OCR
from pdf2image import convert_from_path  # Convertir les pages PDF en images
import pdfplumber  # Pour l'extraction de tableaux supplémentaires
import os
from uuid import uuid4
import shutil
import re
from nltk.tokenize import word_tokenize, sent_tokenize
import nltk
nltk.download('punkt_tab')
from nltk.stem import WordNetLemmatizer
from textblob import TextBlob
import nltk
nltk.download('wordnet')
import json
from datetime import datetime
import logging
import openai
import requests
import streamlit as st

from ingestion import detect_pdf_type, extract_pdf_metadata, store_pdf_for_processing
from extraction import extract_text_from_pdf, ocr_from_images, extract_tables_from_pdf, extract_images_from_pdf
from processing import clean_text, extract_emails, extract_phone_numbers, extract_financial_kpis, extract_dates, extract_fund_names, extract_addresses, extract_legal_mentions, tokenize_text, lemmatize_text, structure_data, extract_urls, extract_financial_amounts 
from validation import validate_email, validate_phone_number, validate_kpi, validate_date, validate_fund_name, validate_address, validate_legal_mention
from model import generate_answer_for_questions

# Configuration des logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Exemple de liste de régulateurs connus
known_regulators = ["SEC", "AMF", "FCA", "FINMA"]

# Exemple de liste de fonds connus
known_funds = ["Alpha Crypto Fund", "Beta Blockchain Fund", "Gamma Digital Assets Fund"]

def process_pdf_data(pdf_path, output_dir="output"):
    """
    Processus complet d'extraction, de nettoyage, et de validation des données d'un PDF.
    """
    try:
        # Étape 1 : Détection du type de PDF
        pdf_type = detect_pdf_type(pdf_path)
        logging.info(f"Type de PDF détecté : {pdf_type}")

        # Étape 2 : Extraire le texte natif ou effectuer l'OCR si image
        if pdf_type == "texte natif":
            text = extract_text_from_pdf(pdf_path)
        else:
            # Si le PDF est un scan, utiliser OCR pour extraire le texte
            text = ocr_from_images(pdf_path, output_dir="ocr_output")
        
        if not text:
            logging.error("Aucun texte extrait du PDF.")
            return None

        # Étape 3 : Extraire les métadonnées
        metadata = extract_pdf_metadata(pdf_path)
        logging.info(f"Métadonnées extraites : {metadata}")

        # Étape 4 : Nettoyer le texte extrait
        cleaned_text = clean_text(text)
        logging.info("Texte nettoyé avec succès.")

        # Étape 5 : Extraire les informations sensibles
        emails = extract_emails(cleaned_text)
        phone_numbers = extract_phone_numbers(cleaned_text)
        kpis = extract_financial_kpis(cleaned_text)
        dates = extract_dates(cleaned_text)
        fund_names = extract_fund_names(cleaned_text)  # Extraction des noms de fonds
        addresses = extract_addresses(cleaned_text)    # Extraction des adresses
        legal_mentions = extract_legal_mentions(cleaned_text)  # Extraction des mentions légales
        urls = extract_urls(cleaned_text)  # Extraction des URLs
        financial_amounts = extract_financial_amounts(cleaned_text)  # Extraction des montants financ
        
        # Générer des questions à partir du texte
        questions = generate_answer_for_questions(cleaned_text)

        # Étape 6 : Tokeniser et lemmatiser le texte
        words, sentences = tokenize_text(cleaned_text)
        words = lemmatize_text(words)

        # Étape 7 : Extraire les tableaux et images
        tables = extract_tables_from_pdf(pdf_path, output_dir)

        # Étape 8 : Structurer les données extraites
        structured_data = structure_data(
            emails, phone_numbers, kpis, dates, fund_names, addresses, legal_mentions, urls, financial_amounts, questions 
        )

        # Étape 9 : Valider les informations extraites
        valid_emails = [email for email in structured_data["emails"] if validate_email(email)]
        valid_phones = [phone for phone in structured_data["phone_numbers"] if validate_phone_number(phone)]
        valid_kpis = [kpi for kpi in structured_data["financial_kpis"] if validate_kpi(kpi[0], kpi[1])]
        valid_dates = [date for date in structured_data["dates"] if validate_date(date)]
        valid_fund_names = [fund_name for fund_name in structured_data["fund_names"] if validate_fund_name(fund_name, known_funds)]
        valid_addresses = [address for address in structured_data["addresses"] if validate_address(address)]
        valid_legal_mentions = {
            key: value for key, value in structured_data["legal_mentions"].items()
            if validate_legal_mention(key, value, known_regulators)
        }
        #cleaned_urls = [clean_url(url) for url in structured_data["urls"]]
        #validate_urls = [url for url in cleaned_urls["urls"] if validate_url(url)]


        # Créer un dossier spécifique pour le PDF dans output
        pdf_name = os.path.basename(pdf_path).split(".")[0]  # Nom du PDF sans l'extension
        pdf_output_dir = os.path.join(output_dir, pdf_name)
        os.makedirs(pdf_output_dir, exist_ok=True)  # Crée le dossier si nécessaire

        # Sauvegarder les résultats dans le répertoire de sortie
        metadata_path = os.path.join(pdf_output_dir, "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=4)

        structured_data_path = os.path.join(pdf_output_dir, "structured_data.json")
        with open(structured_data_path, "w") as f:
            json.dump(structured_data, f, indent=4)

        # Sauvegarder les tableaux extraits dans un fichier JSON
        tables_path = os.path.join(pdf_output_dir, "tables.json")
        with open(tables_path, "w") as f:
            json.dump(tables, f, indent=4)

        # Créer un sous-dossier "images" dans le répertoire de sortie du PDF
        images_output_dir = os.path.join(pdf_output_dir, "images")
        os.makedirs(images_output_dir, exist_ok=True)

        # Sauvegarder les images elles-mêmes dans le sous-dossier "images"
        images = extract_images_from_pdf(pdf_path, images_output_dir)

        # Retourner les résultats
        return {
            "metadata": metadata,
            "structured_data": structured_data,
            "valid_emails": valid_emails,
            "valid_phones": valid_phones,
            "valid_kpis": valid_kpis,
            "valid_dates": valid_dates,
            "valid_fund_names": valid_fund_names,
            "valid_addresses": valid_addresses,
            "valid_legal_mentions": valid_legal_mentions,
            "validate_urls" : urls,
            "validate_financial_amounts" : financial_amounts,
            "pdf_output_dir": pdf_output_dir,  # Renvoie le chemin du dossier de sortie du PDF
            "tables": tables,  # Renvoie les tableaux extraits
            "images": images   # Renvoie les chemins des images extraites
        }
    except Exception as e:
        logging.error(f"Erreur lors du traitement du PDF : {e}")
        return None


# ------------------------------------------------
#                  Streamlit App
# ------------------------------------------------

def main():
    st.title("Traitement de PDF - Extraction et Validation des Données")

    uploaded_file = st.file_uploader("Téléchargez votre fichier PDF", type="pdf")
    
    if uploaded_file is not None:
        # Sauvegarder le fichier PDF dans le dossier "upload"
        upload_dir = "upload"
        os.makedirs(upload_dir, exist_ok=True)
        
        pdf_path = os.path.join(upload_dir, f"{uuid4()}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Processus complet d'extraction et de validation des données
        result = process_pdf_data(pdf_path)
        
        if result:
            # Afficher les résultats extraits
            st.subheader("Métadonnées PDF")
            st.json(result["metadata"])

            st.subheader("Données extraites et validées")
            st.json(result["structured_data"])

            # Afficher les résultats validés
            st.subheader("Emails validés")
            st.write(result["valid_emails"])

            st.subheader("Numéros de téléphone validés")
            st.write(result["valid_phones"])

            st.subheader("KPIs financiers validés")
            st.write(result["valid_kpis"])

            st.subheader("Dates validées")
            st.write(result["valid_dates"])

            st.subheader("Noms de fonds validés")
            st.write(result["valid_fund_names"])

            st.subheader("Adresses validées")
            st.write(result["valid_addresses"])

            st.subheader("Mentions légales validées")
            st.write(result["valid_legal_mentions"])

            st.subheader("Urls validées")
            st.write(result["validate_urls"])

            st.subheader("financial_amounts")
            st.write(result["validate_financial_amounts"])

            st.subheader("Fichiers générés")
            st.write(f"Les résultats et extractions ont été enregistrés dans : {result['pdf_output_dir']}")

        else:
            st.error("Une erreur est survenue pendant le traitement du PDF.")
        
        # Nettoyer le fichier PDF temporaire
        os.remove(pdf_path)

if __name__ == "__main__":
    main()