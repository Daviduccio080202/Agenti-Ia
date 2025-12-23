import logging
import os
import aiohttp
from dotenv import load_dotenv

# Import per la versione 0.12.x
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import deepgram, elevenlabs, openai, silero
from typing import Annotated

# Carica variabili d'ambiente
load_dotenv()

# Configurazione Logger
logger = logging.getLogger("real-estate-agent")
logger.setLevel(logging.INFO)

# --- DEBUG: Verifica Chiavi ---
if not os.getenv("GROQ_API_KEY"):
    logger.error("❌ ERRORE: Manca GROQ_API_KEY!")
if not os.getenv("ELEVENLABS_API_KEY"):
    logger.error("❌ ERRORE: Manca ELEVENLABS_API_KEY!")

# --- 1. DEFINIZIONE TOOL (Le Capacità) ---
class RealEstateTools(llm.FunctionContext):
    
    @llm.ai_callable(description="Cerca immobili nel database in base a zona e budget.")
    async def search_property(self, 
        zona: Annotated[str, llm.TypeInfo(description="Zona richiesta (es. Centro)")],
        budget: Annotated[int, llm.TypeInfo(description="Budget massimo")]
    ):
        logger.info(f"🔎 TOOL ATTIVATO: Cerco casa in zona {zona} con budget {budget}...")
        
        # Qui un giorno collegherai n8n. Per ora simulo:
        if "centro" in zona.lower():
            return "Risultato DB: Trilocale Via Roma (250k), Bilocale Piazza Duomo (180k)."
        return "Risultato DB: Nessun immobile trovato in questa zona."

# --- 2. GESTIONE CHIUSURA CHIAMATA ---
async def on_shutdown(ctx: JobContext, chat_ctx: llm.ChatContext):
    logger.info("📞 Chiamata terminata. Salvataggio transcript...")
    # Qui potrai inviare i dati a n8n in futuro

# --- 3. CONFIGURAZIONE AGENTE (Il Cuore) ---
async def entrypoint(ctx: JobContext):
    # Connessione
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Aspetta che l'utente entri nella stanza (Importante!)
    participant = await ctx.wait_for_participant()
    logger.info(f"Utente connesso: {participant.identity}")
    
    # Personalità Iniziale
    initial_ctx = llm.ChatContext().append(
        role="system",
        text="""Sei Laura, un'agente immobiliare professionale, empatica e sintetica.
        - Il tuo obiettivo è capire cosa cerca il cliente (zona, budget, numero camere).
        - Usa il tool 'search_property' se ti chiedono disponibilità.
        - Parla in italiano naturale."""
    )

    # Creazione Pipeline
    agent = VoicePipelineAgent(
        # A. Rilevamento Voce (VAD) - Configurato per ignorare rumori brevi
        vad=silero.VAD.load(
            min_speech_duration=0.1, # Deve sentire voce per almeno 0.1s
            min_silence_duration=0.5, # Aspetta 0.5s di silenzio prima di considerare finita la frase
        ),
        
        # B. Orecchie (STT) - Deepgram Nova 2 (Veloce e preciso in IT)
        stt=deepgram.STT(model="nova-2", language="it"),
        
        # C. Cervello (LLM) - Groq (Llama 3.3)
        llm=openai.LLM(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.3-70b-versatile", # Ultimo modello stabile
        ),
        
        # D. Bocca (TTS) - ElevenLabs
        tts=elevenlabs.TTS(
            api_key=os.getenv("ELEVENLABS_API_KEY"),
            voice=elevenlabs.Voice(
                id="JBFqnCBsd6RMkjVDRZzb", # ID Voce (George)
                name="George",
                category="premade"
            ),
            model="eleven_turbo_v2_5"
        ),
        
        # E. Collegamenti Extra
        fnc_ctx=RealEstateTools(),
        chat_ctx=initial_ctx,
        
        # --- PARAMETRI DI STABILITÀ (Anti-Interruzione) ---
        # 1. Quanto deve durare un suono per interrompere l'agente (0.6s = difficile interrompere per sbaglio)
        interrupt_speech_duration=0.6, 
        
        # 2. Sensibilità all'interruzione (Parole vs Rumore)
        interrupt_min_words=0, 
        
        # 3. Ritardo prima di rispondere (Evita risposte sovrapposte)
        min_endpointing_delay=0.8,
        # --------------------------------------------------
    )

    # Callback di chiusura
    ctx.add_shutdown_callback(lambda: on_shutdown(ctx, initial_ctx))

    # Avvio Agente
    agent.start(ctx.room, participant)
    
    # Saluto iniziale
    await agent.say("Agenzia Immobiliare Domus, sono Laura. Come posso aiutarti?", allow_interruptions=True)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
