import os
import asyncio
import json
from dotenv import load_dotenv
from upstash_vector import Index
from agents import Agent, Runner, FunctionTool

import logging

# On force le silence sur les modules réseau et OpenAI
os.environ["OPENAI_LOG"] = "error"
logging.getLogger("openai").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)

load_dotenv()
index = Index(url=os.getenv("UPSTASH_VECTOR_REST_URL"), token=os.getenv("UPSTASH_VECTOR_REST_TOKEN"))

async def search_portfolio(context, query) -> str:
    # Nettoyage de la requête (cas du JSON envoyé par l'IA)
    search_text = query
    if isinstance(query, dict):
        search_text = query.get("query", str(query))
    elif isinstance(query, str) and "{" in query:
        try:
            search_text = json.loads(query).get("query", query)
        except: pass

    print(f"\n🔍 [DEBUG] Recherche Upstash : '{search_text}'")
    results = index.query(data=search_text, top_k=3, include_data=True)
    
    if not results or not results[0].data:
        print("❌ Rien trouvé dans Upstash")
        return "ERREUR : Aucun document trouvé dans la base de données."

    data_recue = results[0].data
    print(f"📥 Contenu reçu : {data_recue[:100]}...")
    
    # Message ultra-explicite pour forcer l'IA à utiliser le texte
    return f"IMPORTANT - VOICI LES DONNÉES EXTRAITES : {data_recue}"

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
    tools=[portfolio_search_tool]
    )

async def main():
    print("--- Test de l'Agent ---")
    result = await Runner.run(agent, "Quelles sont mes compétences techniques ?")
    print(f"\n--- Réponse finale ---\n{result.final_output}")

if __name__ == "__main__":

    asyncio.run(main())
