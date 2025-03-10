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
#                   Step 3
# ------------------------------------------------
# Normalisation et Nettoyage des Données
def clean_text(text):
    """
    Nettoie le texte extrait en conservant les caractères spéciaux nécessaires pour les emails.
    """
    try:
        # Suppression des caractères non alphanumériques sauf pour les espaces, @, ., et ,
        cleaned_text = re.sub(r"[^a-zA-Z0-9\s@.,:/\-]", "", text)
        # Conversion en minuscules et suppression des espaces multiples
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).lower()
        # Suppression des lignes vides
        cleaned_text = "\n".join([line for line in cleaned_text.splitlines() if line.strip()])
        return cleaned_text
    except Exception as e:
        logging.error(f"Erreur lors du nettoyage du texte : {e}")
        return None

# Tokenisation et Structuration du Texte
def tokenize_text(text):
    """
    Tokenise le texte en mots et en phrases.
    """
    try:
        words = word_tokenize(text)
        sentences = sent_tokenize(text)
        return words, sentences
    except Exception as e:
        logging.error(f"Erreur lors de la tokenisation du texte : {e}")
        return [], []

def lemmatize_text(words):
    """
    Lemmatise les mots pour réduire les formes flexionnelles.
    """
    try:
        lemmatizer = WordNetLemmatizer()
        return [lemmatizer.lemmatize(word) for word in words]
    except Exception as e:
        logging.error(f"Erreur lors de la lemmatisation du texte : {e}")


# ------------------------------------------------
# Extraction des Emails et Numéros de Téléphone
def extract_emails(text):
    """
    Extrait les emails du texte à l'aide d'une expression régulière.
    """
    try:
        email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
        return re.findall(email_pattern, text)
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction des emails : {e}")
        return []

def extract_phone_numbers(text):
    """
    Extrait les numéros de téléphone du texte à l'aide d'une expression régulière.
    """
    try:
        phone_pattern = r"(\+?\d{1,4}[\s\-]?)?(\(?\d{2,4}\)?[\s\-]?)?\d{3,4}[\s\-]?\d{3,4}"
        matches = re.findall(phone_pattern, text)
        # Normalisation des numéros de téléphone
        return [''.join(match).replace(" ", "").replace("-", "") for match in matches if len(''.join(match)) >= 7]
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction des numéros de téléphone : {e}")
        return []

# ------------------------------------------------
# Extraction des KPIs Financiers
def extract_financial_kpis(text):
    """
    Extrait les KPIs financiers du texte, comme les revenus, bénéfices, etc.
    """
    try:
        kpi_pattern = r"(revenu|bénéfice|marge|dépenses|profit|aum|roi|volatilité|ebitda)\s*[:\-]?\s*([\$€]?\d[\d,\.]*\s?[%]?)"
        return re.findall(kpi_pattern, text, flags=re.IGNORECASE)
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction des KPIs financiers : {e}")
        return []

# ------------------------------------------------
# Extraction des Dates
def extract_dates(text):
    """
    Extrait les dates au format standard (dd/mm/yyyy, dd-mm-yyyy, dd.mm.yyyy, dd mois yyyy, etc.).
    """
    try:
        date_pattern = (
            r"\b(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})\b|"
            r"\b(\d{1,2}\s(?:jan(?:uary|vier)?|fév(?:rier)?|feb(?:ruary)?|mars|mar(?:ch)?|avr(?:il)?|apr(?:il)?|mai|may|juin|jun(?:e)?|juil(?:let)?|jul(?:y)?|août|aug(?:ust)?|sep(?:tembre)?|sep(?:tember)?|oct(?:obre)?|oct(?:ober)?|nov(?:embre)?|nov(?:ember)?|déc(?:embre)?|dec(?:ember)?)[a-z]*\s\d{4})\b"
        )
        matches = re.findall(date_pattern, text, flags=re.IGNORECASE)
        return [match[0] if match[0] else match[1] for match in matches]
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction des dates : {e}")
        return []

def extract_fund_names(text):
    """
    Extrait les noms des fonds mentionnés dans le texte.
    """
    try:
        # Regex pour capturer les noms de fonds
        fund_name_pattern = r"(Fonds|Fund|Fundo|Investment)\s+([A-Za-z0-9\s\-]+)"
        matches = re.findall(fund_name_pattern, text, flags=re.IGNORECASE)
        # Retourne uniquement les noms de fonds (sans les mots-clés comme "Fonds" ou "Fund")
        return [match[1].strip() for match in matches]
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction des noms de fonds : {e}")
        return []
    
def extract_addresses(text):
    """
    Extrait les adresses mentionnées dans le texte.
    """
    try:
        # Regex améliorée pour capturer les adresses
        address_pattern = r"\d+\s+[A-Za-z]+(?:\s+[A-Za-z]+)*\s*(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Str\.?)?\s*,\s*\d{5,6}\s+[A-Za-z]+(?:\s+[A-Za-z]+)*\s*,\s*[A-Za-z]+(?:\s+[A-Za-z]+)*"
        return re.findall(address_pattern, text, flags=re.IGNORECASE)
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction des adresses : {e}")
        return []
    
def extract_legal_mentions(text):
    """
    Extrait les mentions légales du texte.
    """
    try:
        # Regex pour capturer les mentions légales
        legal_pattern = r"(Registre|Registration|License|Licence|Regulator|Régulateur)\s*:\s*([A-Za-z0-9\s\-]+)"
        matches = re.findall(legal_pattern, text, flags=re.IGNORECASE)
        # Retourne les mentions légales sous forme de dictionnaire
        return {match[0]: match[1].strip() for match in matches}
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction des mentions légales : {e}")
        return {}

def extract_urls(text):
    """
    Extrait les URLs du texte à l'aide d'une expression régulière améliorée.
    """
    try:
        # Expression régulière pour capturer les URLs, y compris les DOI et les chemins complexes
        url_pattern = r"(https?://(?:www\.)?[\w\-\.]+\.[a-zA-Z]{2,}(?:/\S*)?|doi:\s*https?://doi\.org/\S+|https?://[\w\-\.]+\.\w{2,}(?:/\S*)?)"
        return re.findall(url_pattern, text)
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction des URLs : {e}")
        return []

def extract_financial_amounts(text):
    """
    Extrait les montants financiers avec leurs devises.
    """
    try:
        amount_pattern = r"(\$|€|£)?\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?"
        return re.findall(amount_pattern, text)
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction des montants financiers : {e}")
        return []
    
# ------------------------------------------------
def structure_data(emails, phones, kpis, dates, fund_names=None, addresses=None, legal_mentions=None, urls=None, financial_amounts=None, questions=None):
    """
    Structure les données extraites sous forme d'un dictionnaire.
    """
    return {
        "emails": emails,
        "phone_numbers": phones,
        "financial_kpis": kpis,
        "dates": dates,
        "fund_names": fund_names if fund_names else [],  # Ajout des noms de fonds
        "addresses": addresses if addresses else [],    # Ajout des adresses
        "legal_mentions": legal_mentions if legal_mentions else {},  # Ajout des mentions légales
        "urls": urls if urls else [],
        "financial_amounts": financial_amounts if financial_amounts else [],
        "questions": questions if questions else [],  # Ajout des questions
        "metadata": {
            "extraction_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_emails": len(emails),
            "total_phones": len(phones),
            "total_kpis": len(kpis),
            "total_dates": len(dates),
            "total_fund_names": len(fund_names) if fund_names else 0,
            "total_addresses": len(addresses) if addresses else 0,
            "total_legal_mentions": len(legal_mentions) if legal_mentions else 0,
            "total_urls": len(urls) if urls else 0,
            "total_financial_amounts": len(financial_amounts) if financial_amounts else 0,  # Ajout du total des montants
            "total_questions": len(questions) if questions else 0,  # Ajout du total de questions
            
        }
    }