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
#                   Step 1
# ------------------------------------------------
# Détection du type de contenu (texte natif vs. scan/image)
def detect_pdf_type(pdf_path):
    """
    Détecte si un PDF contient du texte natif ou est composé d'images (scan).
    """
    try:
        doc = fitz.open(pdf_path)  # Ouvre le PDF
        text = ""  # Initialisation du texte extrait

        # Parcours de chaque page
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)  # Charge la page
            text += page.get_text("text")  # Extrait le texte de la page

        # Retourne le type de contenu
        if text.strip():
            return "texte natif"
        else:
            return "image/scans"  # Si aucun texte n'est trouvé
    except Exception as e:
        print(f"Erreur lors de la détection du type de contenu : {e}")
        return None

# Extraction des métadonnées
def extract_pdf_metadata(pdf_path):
    """
    Extrait les métadonnées du PDF (titre, auteur, etc.).
    """
    try:
        doc = fitz.open(pdf_path)  # Ouvre le PDF
        metadata = doc.metadata  # Récupère les métadonnées du PDF

        # Normalisation des clés pour une présentation uniforme (tout en minuscule)
        metadata = {key.lower(): value for key, value in metadata.items()}
        return metadata  # Retourne les métadonnées extraites
    except Exception as e:
        print(f"Erreur lors de l'extraction des métadonnées : {e}")
        return None

# Stockage initial des fichiers pour traitement
def store_pdf_for_processing(pdf_path, storage_dir="pdf_storage"):
    """
    Stocke le fichier PDF dans un répertoire dédié et renvoie son chemin de stockage.
    """
    try:
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)  # Crée le répertoire si nécessaire
        
        unique_id = str(uuid4())  # Génère un identifiant unique
        file_name = f"{unique_id}.pdf"  # Nom du fichier avec l'ID unique

        # Chemin du fichier de destination
        dest_path = os.path.join(storage_dir, file_name)
        if not os.path.exists(dest_path):  # Vérifie si le fichier existe
            shutil.copy(pdf_path, dest_path)  # Copie le fichier
            return dest_path  # Retourne le chemin du fichier stocké
        else:
            print("Le fichier existe déjà dans le répertoire de stockage.")
            return None
    except Exception as e:
        print(f"Erreur lors du stockage du fichier : {e}")
        return None

# Fonction de test de l'ingestion du PDF (type, métadonnées, stockage)
def test_ingestion(pdf_path):
    """
    Fonction de test pour vérifier l'ingestion des PDF (type, métadonnées, stockage).
    """
    # Test de la détection du type de contenu
    content_type = detect_pdf_type(pdf_path)
    if content_type:
        print(f"Type de contenu détecté : {content_type}")
    
    # Test de l'extraction des métadonnées
    metadata = extract_pdf_metadata(pdf_path)
    if metadata:
        print("Métadonnées extraites :")
        for key, value in metadata.items():
            print(f"{key}: {value}")
    
    # Test du stockage du fichier
    stored_path = store_pdf_for_processing(pdf_path)
    if stored_path:
        print(f"Fichier stocké à : {stored_path}")

# Extraction et affichage du texte natif pour vérifier si l'auteur est mentionné dans le texte
def extract_and_display_text(pdf_path):
    """
    Extrait et affiche le texte natif d'un PDF pour vérifier si l'auteur est mentionné dans le texte.
    """
    try:
        doc = fitz.open(pdf_path)  # Ouvre le fichier PDF
        text = ""  # Initialisation du texte extrait
        
        # Parcours de chaque page du PDF
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)  # Charge la page
            text += page.get_text("text")  # Extrait le texte de la page
        
        # Affichage du texte extrait (les 1000 premiers caractères)
        print("Texte extrait du PDF :")
        print(text[:1000])  # Affiche seulement les 1000 premiers caractères du texte extrait
        
        return text  # Retourne le texte extrait
    except Exception as e:
        print(f"Erreur lors de l'extraction du texte : {e}")
        return None