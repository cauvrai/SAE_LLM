import os
import json
import asyncio
import streamlit as st
from dotenv import load_dotenv
from upstash_vector import Index
from agents import Agent, Runner, FunctionTool, ModelSettings

load_dotenv()

# Connexion à Upstash
index = Index(
    url=os.getenv("UPSTASH_VECTOR_REST_URL"), 
    token=os.getenv("UPSTASH_VECTOR_REST_TOKEN")
)

async def search_portfolio(context, query) -> str:
    try:
        # Nettoyage de la requête envoyée par Groq
        search_text = query
        if isinstance(query, dict):
            search_text = query.get("query", str(query))
        elif isinstance(query, str) and "{" in query:
            try:
                search_text = json.loads(query).get("query", query)
            except: pass

        # Sécurité supplémentaire : on force le texte en chaîne de caractères
        search_text = str(search_text)

        print(f"\n🔍 [DEBUG] Recherche Upstash : '{search_text}'")
        
        # Appel à la base de données
        results = index.query(data=search_text, top_k=3, include_data=True)
        
        if not results or not results[0].data:
            return "ERREUR : Aucun document trouvé dans la base de données."

        data_recue = results[0].data
        return f"IMPORTANT - VOICI LES DONNÉES EXTRAITES : {data_recue}"

    except Exception as e:
        # C'EST ICI LA MAGIE : au lieu de crasher, on capture l'erreur !
        error_msg = f"Erreur de connexion à Upstash : {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg

# --- Configuration de l'Outil ---
search_portfolio_schema = {
    "type": "object",
    "properties": {"query": {"type": "string", "description": "Mots-clés"}},
    "required": ["query"],
}

portfolio_search_tool = FunctionTool(
    name="search_portfolio",
    description="Outil pour lire les compétences et projets dans les fichiers .md",
    params_json_schema=search_portfolio_schema,
    on_invoke_tool=search_portfolio
)

# --- Configuration de l'Agent ---
agent = Agent(
    name="Charles Auvrai",  
    model="llama-3.1-8b-instant", 
    instructions=(
        "Je suis Charles Auvrai, étudiant en Science des Données et sportif de haut niveau. "
        "Je m'exprime TOUJOURS à la première personne du singulier ('Je', 'Moi'). "
        "Mon ton est professionnel, déterminé mais accessible. "
        "Voici les règles strictes que je dois appliquer à chaque réponse : "
        "1. RECHERCHE : J'utilise obligatoirement l'outil 'search_portfolio' pour retrouver mes expériences et compétences. "
        "2. GESTION DU MARKDOWN : L'outil me renvoie du texte brut. Je dois assimiler ces informations et les reformuler de manière fluide. Je ne copie-colle JAMAIS le formatage Markdown brut (comme les #, *, ou -) dans ma réponse finale. Je m'approprie les idées naturellement. "
        "3. SPORT : Je mentionne le sport de haut niveau UNIQUEMENT si on aborde mes loisirs, mes passions ou mes qualités morales (rigueur, esprit d'équipe). "
        "4. FORMAT : Mes réponses sont concises (pas plus de 5 phrases, sauf si on me demande des détails). Je fais des paragraphes et je saute des lignes pour que ma réponse soit très lisible."
    ),
    tools=[portfolio_search_tool],
    model_settings=ModelSettings(temperature=0.1)
)
