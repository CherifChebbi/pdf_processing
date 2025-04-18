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
import os
import openai
import requests
import streamlit as st

# Configuration des logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ------------------------------------------------
# Vérification et Validation des Données
def validate_email(email):
    """
    Vérifie si un email est valide.
    """
    email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(email_pattern, email) is not None

def validate_phone_number(phone):
    """
    Vérifie si un numéro de téléphone est valide.
    """
    phone_pattern = r"^(\+?\d{1,4}[\s\-]?)?(\(?\d{2,4}\)?[\s\-]?)?\d{3,4}[\s\-]?\d{3,4}$"
    return re.match(phone_pattern, phone) is not None

def validate_kpi(kpi_name, kpi_value):
    """
    Vérifie si une valeur KPI est un nombre valide et cohérent.
    """
    try:
        value = float(kpi_value.replace(",", "").replace(" ", ""))
        if kpi_name.lower() == "aum" and value < 0:
            return False  # AUM ne peut pas être négatif
        elif kpi_name.lower() == "roi" and (value < -100 or value > 1000):
            return False  # ROI doit être entre -100% et 1000%
        return True
    except ValueError:
        return False

def validate_date(date):
    """
    Valide si la date correspond à un format valide.
    """
    date_pattern = (
        r"\b(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})\b|"
        r"\b(\d{1,2}\s(?:jan(?:uary|vier)?|fév(?:rier)?|feb(?:ruary)?|mars|mar(?:ch)?|avr(?:il)?|apr(?:il)?|mai|may|juin|jun(?:e)?|juil(?:let)?|jul(?:y)?|août|aug(?:ust)?|sep(?:tembre)?|sep(?:tember)?|oct(?:obre)?|oct(?:ober)?|nov(?:embre)?|nov(?:ember)?|déc(?:embre)?|dec(?:ember)?)[a-z]*\s\d{4})\b"
    )
    return re.match(date_pattern, date) is not None

def validate_fund_name(fund_name, known_funds):
    """
    Vérifie si un nom de fonds est valide en le comparant à une liste de fonds connus.
    """
    return fund_name in known_funds

# Exemple de liste de fonds connus
known_funds = ["Alpha Crypto Fund", "Beta Blockchain Fund", "Gamma Digital Assets Fund"]


def validate_address(address):
    """
    Vérifie si une adresse est valide en utilisant l'API OpenStreetMap Nominatim.
    """
    try:
        # Vérifier si l'adresse est vide ou invalide
        if not address or not isinstance(address, str):
            logging.warning(f"Adresse vide ou invalide : {address}")
            return False

        # Envoyer une requête à l'API Nominatim
        response = requests.get(
            f"https://nominatim.openstreetmap.org/search?q={address}&format=json",
            headers={"User-Agent": "YourAppName/1.0"}  # Ajouter un User-Agent pour éviter les erreurs 403
        )

        # Vérifier si la réponse est vide ou invalide
        if not response.text.strip():
            logging.error(f"Réponse vide de l'API Nominatim pour l'adresse : {address}")
            return False

        # Parser la réponse JSON
        data = response.json()

        # Vérifier si des résultats ont été trouvés
        if isinstance(data, list) and len(data) > 0:
            return True  # L'adresse est valide
        else:
            logging.debug(f"Aucun résultat trouvé pour l'adresse : {address}")
            return False  # L'adresse n'est pas valide

    except json.JSONDecodeError as e:
        logging.error(f"Erreur de décodage JSON pour l'adresse {address} : {e}")
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur de requête pour l'adresse {address} : {e}")
        return False
    except Exception as e:
        logging.error(f"Erreur lors de la validation de l'adresse {address} : {e}")
        return False
    
def validate_legal_mention(mention_type, mention_value, known_regulators):
    """
    Vérifie si une mention légale est valide en la comparant à une liste de régulateurs ou de licences connus.
    """
    if mention_type.lower() in ["regulator", "régulateur"]:
        return mention_value in known_regulators
    return True  # Pour d'autres types de mentions, on suppose qu'elles sont valides

# Exemple de liste de régulateurs connus
known_regulators = ["SEC", "AMF", "FCA", "FINMA"]

def validate_url(url):
    """
    Valide une URL en vérifiant si elle est accessible.
    """
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Erreur lors de la validation de l'URL {url} : {e}")
        return False
    

