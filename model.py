import logging
import os
import openai
import requests

# ------------------------------------------------
#                   SambaNova
# ------------------------------------------------

API_KEY = "96078828-c037-4655-90c0-e655e3bb71dc"
BASE_URL = "https://api.sambanova.ai/v1"

def generate_answer_for_questions(text, model="DeepSeek-R1-Distill-Llama-70B"):
    """
    Génère des réponses spécifiques aux questions sur les fonds d'investissement,
    les montants d'investissement, les exigences légales, les risques financiers, et les rendements.
    
    :param text: Le texte extrait du PDF.
    :param model: Le modèle à utiliser pour la génération des réponses.
    :return: La réponse aux questions sous forme de texte.
    """
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
    Voici un texte que vous devez analyser. Répondez aux questions suivantes de manière concise :
    
    1. C'est quoi le résumé de ce PDF ? De quoi parle-t-il, en quelques lignes (maximum 4) ?
    2. Identifiez tous les noms de fonds et les montants d'investissement mentionnés dans ce texte.
    3. Vérifiez si le fonds respecte les exigences légales concernant les informations financières et les risques.
    4. Quels sont les risques financiers associés aux fonds mentionnés ?
    5. Quelles sont les informations financières clés concernant les rendements des fonds ?
    
    Texte : {text}
    """

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant answering questions based on provided text."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "top_p": 0.1
    }

    try:
        response = requests.post(f"{BASE_URL}/chat/completions", headers=headers, json=payload)
        response_data = response.json()

        if response.status_code == 200 and "choices" in response_data:
            content = response_data["choices"][0]["message"]["content"].strip()
            return content
        else:
            logging.error(f"Erreur API: {response_data}")
            return "Erreur lors de la récupération des réponses."
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur de requête API : {e}")
        return "Erreur lors de la requête API."
    except Exception as e:
        logging.error(f"Erreur lors de la requête : {e}")
        return "Erreur lors du traitement de la requête."
