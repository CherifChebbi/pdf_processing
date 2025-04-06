import logging
import requests

API_KEY = "96078828-c037-4655-90c0-e655e3bb71dc"
BASE_URL = "https://api.sambanova.ai/v1"

def generate_answer(text, question, model="DeepSeek-R1-Distill-Llama-70B"):
    """
    Génère des réponses spécifiques aux questions sur le texte fourni.
    
    :param text: Le texte extrait du PDF.
    :param question: La question posée par l'utilisateur.
    :param model: Le modèle à utiliser pour la génération des réponses.
    :return: La réponse à la question sous forme de texte.
    """
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
    Voici un texte. Résumez-le de manière concise en ne répondant qu'à la question posée, sans expliquer votre raisonnement.

    Texte : {text}

    Question : {question}

    Réponse concise :
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