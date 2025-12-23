import logging
import os
import aiohttp
from dotenv import load_dotenv

# --- NUOVI IMPORT PER LA VERSIONE 0.12+ ---
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import deepgram, elevenlabs, openai, silero
from typing import Annotated

load_dotenv()
logger = logging.getLogger("real-estate-agent")
logger.setLevel(logging.INFO)

# --- A. DEFINIZIONE DEI TOOL ---
class RealEstateTools(llm.FunctionContext):
    
    @llm.ai_callable(description="Cerca immobili nel database in base a zona e prezzo.")
    async def search_property(self, 
        zona: Annotated[str, llm.TypeInfo(description="La zona richiesta (es. Centro, Periferia)")],
        budget: Annotated[int, llm.TypeInfo(description="Il budget massimo in euro")]
    ):
        logger.info(f"🔎 Cercando casa in zona {zona} con budget {budget}...")
        
        # Simulazione Database
        if "centro" in zona.lower():
            return "Ho trovato un Trilocale in Via Roma a 250.000 euro e un Bilocale in Piazza Duomo a 180.000 euro."
        else:
            return "In quella zona al momento non ho disponibilità immediate, ma posso prendere nota."

# --- B. POST-CALL WEBHOOK ---
async def on_shutdown(ctx: JobContext, chat_ctx: llm.ChatContext):
    logger.info("📞 Chiamata terminata. Invio dati post-call...")
    
    full_transcript = []
    for msg in chat_ctx.messages:
        if msg.role != "system":
            full_transcript.append(f"{msg.role}: {msg.content}")
    
    payload = {
        "room_id": ctx.room.name,
        "transcript": "\n".join(full_transcript)
    }
    
    # URL fittizio per evitare errori se non hai n8n
    logger.info(f"📡 Simulo invio a n8n: {len(full_transcript)} messaggi.")

# --- C. PUNTO DI INGRESSO (Aggiornato) ---
async def entrypoint(ctx: JobContext):
    # Connessione iniziale
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Nelle nuove versioni, è meglio aspettare che ci sia un partecipante
    participant = await ctx.wait_for_participant()
    logger.info(f"Partecipante connesso: {participant.identity}")

    # Memoria Iniziale
    chat_context = llm.ChatContext().append(
        role="system",
        text="""Sei Laura, un agente immobiliare professionale.
        - Chiedi budget e zona.
        - Usa search_property se serve.
        - Rispondi brevemente in italiano."""
    )

    # --- CAMBIAMENTO QUI: VoicePipelineAgent invece di VoiceAssistant ---
    agent = VoicePipelineAgent(
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-2", language="it"),
        llm=openai.LLM(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama3-70b-8192",
        ),
        tts=elevenlabs.TTS(
            api_key=os.getenv("ELEVENLABS_API_KEY"),
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            model_id="eleven_turbo_v2_5"
        ),
        fnc_ctx=RealEstateTools(),
        chat_ctx=chat_context
    )

    # Callback di chiusura
    ctx.add_shutdown_callback(lambda: on_shutdown(ctx, chat_context))

    # Avvio dell'agente (Sintassi aggiornata)
    agent.start(ctx.room, participant)
    
    # Saluto iniziale
    await agent.say("Agenzia Immobiliare Domus, sono Laura. Dimmi tutto!", allow_interruptions=True)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
