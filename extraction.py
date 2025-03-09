import os
import fitz  # PyMuPDF pour extraire le texte natif
import pytesseract  # Tesseract pour OCR
from pdf2image import convert_from_path  # Convertir les pages PDF en images
import pdfplumber  # Pour l'extraction de tableaux supplémentaires
import logging

# Configuration des logs
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Extraction du texte natif
def extract_text_from_pdf(pdf_path):
    """
    Extrait le texte natif d'un PDF à l'aide de PyMuPDF (fitz).
    """
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        # Parcours de chaque page du PDF
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text("text")  # Extrait le texte de chaque page
            if page_text:
                text += page_text  # Ajoute le texte extrait
            else:
                logging.warning(f"Aucun texte trouvé sur la page {page_num+1}")
        
        if not text:
            logging.warning("Aucun texte extrait du PDF.")
        
        return text.strip()  # Retourne le texte extrait (en enlevant les espaces superflus)
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction du texte natif : {e}")
        return None


# OCR pour les scans/les images
def ocr_from_images(pdf_path, output_dir):
    """
    Effectue l'OCR sur un PDF contenant des scans/Images pour extraire le texte.
    """
    try:
        images = convert_from_path(pdf_path)  # Convertit le PDF en images
        text = ""
        
        # Applique Tesseract OCR à chaque image
        for i, image in enumerate(images):
            image_text = pytesseract.image_to_string(image)  # OCR sur l'image
            if image_text:
                text += image_text
            else:
                logging.warning(f"Aucun texte trouvé sur l'image {i+1}")
            
        if not text:
            logging.warning("Aucun texte trouvé par OCR.")
        
        # Sauvegarder le texte OCR dans un fichier dans le répertoire de sortie
        ocr_text_path = os.path.join(output_dir, "ocr_text.txt")
        with open(ocr_text_path, "w") as f:
            f.write(text)
        
        logging.debug(f"OCR text saved to {ocr_text_path}")
        return text.strip()  # Retourne le texte extrait par OCR
    except Exception as e:
        logging.error(f"Erreur lors de l'OCR des images : {e}")
        return None


# Extraction des tableaux avec pdfplumber
def extract_tables_from_pdf(pdf_path, output_dir):
    """
    Extrait un tableau depuis un fichier PDF en utilisant pdfplumber.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[0]  # Accède à la première page
            tables = page.extract_tables()  # Extrait les tableaux de la page

            if tables:
                # Sauvegarder les tableaux dans un fichier
                tables_path = os.path.join(output_dir, "tables.txt")
                with open(tables_path, "w") as f:
                    for table in tables:
                        for row in table:
                            f.write(str(row) + "\n")
                
                logging.debug(f"Tables saved to {tables_path}")
            else:
                logging.warning("Aucun tableau trouvé dans ce PDF.")
            
            return tables
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction des tableaux : {e}")
        return None


# Détection des images dans le PDF
def extract_images_from_pdf(pdf_path, output_dir):
    """
    Extrait les images d'un PDF et les stocke dans un répertoire.
    """
    try:
        doc = fitz.open(pdf_path)  # Ouvre le fichier PDF
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)  # Crée le répertoire si nécessaire
            logging.debug(f"Directory {output_dir} created.")
        
        # Parcours de chaque page et extraction des images
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            images = page.get_images(full=True)
            
            for img_index, img in enumerate(images):
                xref = img[0]  # Identifiant de l'image
                image = doc.extract_image(xref)  # Extrait l'image
                image_bytes = image["image"]
                image_filename = os.path.join(output_dir, f"image_page_{page_num+1}_{img_index+1}.png")
                
                with open(image_filename, "wb") as img_file:
                    img_file.write(image_bytes)  # Sauvegarde l'image
                
                logging.debug(f"Image saved to {image_filename}")

        return output_dir  # Retourne le répertoire où les images ont été stockées
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction des images : {e}")
        return None


# Fonction de test pour l'extraction des données
def test_data_extraction(pdf_path):
    """
    Fonction de test pour l'extraction des données (texte, OCR, tableaux, images).
    """
    try:
        # Créer un dossier spécifique pour le PDF
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_dir = os.path.join("output", pdf_name)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logging.debug(f"Directory {output_dir} created.")

        # Test de l'extraction du texte natif
        text = extract_text_from_pdf(pdf_path)
        if text:
            logging.debug(f"Text extracted: {text[:500]}")  # Affiche les 500 premiers caractères
            # Test de l'extraction du texte natif
            text = extract_text_from_pdf(pdf_path)
            if text:
                logging.debug(f"Text extracted: {text[:500]}")  # Affiche les 500 premiers caractères
                with open(os.path.join(output_dir, "text.txt"), "w", encoding="utf-8") as f:
                    f.write(text)
            else:
                logging.warning("No native text extracted.")
        else:
            logging.warning("No native text extracted.")

        # Test de l'OCR pour les scans/les images
        ocr_text = ocr_from_images(pdf_path, output_dir)
        if ocr_text:
            logging.debug(f"OCR text extracted: {ocr_text[:500]}")  # Affiche les 500 premiers caractères
        else:
            logging.warning("No OCR text extracted.")

        # Test de l'extraction des tableaux
        tables = extract_tables_from_pdf(pdf_path, output_dir)
        if tables:
            logging.debug(f"Tables extracted: {tables}")
        else:
            logging.warning("No tables extracted.")

        # Test de l'extraction des images
        images_dir = extract_images_from_pdf(pdf_path, output_dir)
        if images_dir:
            logging.debug(f"Images extracted to {images_dir}")
        else:
            logging.warning("No images extracted.")

    except Exception as e:
        logging.error(f"Erreur lors du test d'extraction des données : {e}")


