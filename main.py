import logging
import os
import aiohttp
from dotenv import load_dotenv

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import deepgram, elevenlabs, openai, silero
from typing import Annotated

load_dotenv()
logger = logging.getLogger("real-estate-agent")
logger.setLevel(logging.INFO)

# --- A. DEFINIZIONE DEI TOOL (Le mani dell'agente) ---
class RealEstateTools(llm.FunctionContext):
    
    @llm.ai_callable(description="Cerca immobili nel database in base a zona e prezzo.")
    async def search_property(self, 
        zona: Annotated[str, llm.TypeInfo(description="La zona richiesta (es. Centro, Periferia)")],
        budget: Annotated[int, llm.TypeInfo(description="Il budget massimo in euro")]
    ):
        logger.info(f"🔎 Cercando casa in zona {zona} con budget {budget}...")
        
        # QUI UN GIORNO CHIAMERAI N8N. PER ORA SIMULIAMO:
        if "centro" in zona.lower():
            return "Ho trovato un Trilocale in Via Roma a 250.000 euro e un Bilocale in Piazza Duomo a 180.000 euro."
        else:
            return "In quella zona al momento non ho disponibilità immediate, ma posso prendere nota."

# --- B. DEFINIZIONE POST-CALL WEBHOOK (La memoria finale) ---
async def on_shutdown(ctx: JobContext, chat_ctx: llm.ChatContext):
    logger.info("📞 Chiamata terminata. Invio dati post-call...")
    
    full_transcript = []
    for msg in chat_ctx.messages:
        if msg.role != "system":
            full_transcript.append(f"{msg.role}: {msg.content}")
    
    # Payload da mandare a n8n
    payload = {
        "room_id": ctx.room.name,
        "transcript": "\n".join(full_transcript)
    }
    
    # Inserisci qui il tuo URL di n8n (Webhook) quando lo avrai
    webhook_url = "https://tuo-n8n.com/webhook/fine-chiamata"
    
    # Simuliamo l'invio (per non far crashare se non hai n8n attivo)
    logger.info(f"📡 Simulo invio a n8n: {len(full_transcript)} messaggi.")
    # (Quando avrai n8n, togli il commento sotto)
    # async with aiohttp.ClientSession() as session:
    #     await session.post(webhook_url, json=payload)

# --- C. PUNTO DI INGRESSO (L'avvio) ---
async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Memoria Iniziale
    chat_context = llm.ChatContext().append(
        role="system",
        text="""Sei Laura, un agente immobiliare professionale e gentile.
        - Chiedi sempre budget e zona preferita.
        - Se chiedono disponibilità, USA IL TOOL search_property.
        - Rispondi in italiano in modo conciso."""
    )

    # Configurazione Agente
    assistant = VoiceAssistant(
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-2", language="it"),
        llm=openai.LLM(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama3-70b-8192",
        ),
        tts=elevenlabs.TTS(
            api_key=os.getenv("ELEVENLABS_API_KEY"),
            voice_id="JBFqnCBsd6RMkjVDRZzb", # George (Cambia con voce femminile se vuoi)
            model_id="eleven_turbo_v2_5"
        ),
        fnc_ctx=RealEstateTools(), # Colleghiamo i Tool
        chat_ctx=chat_context
    )

    # Colleghiamo il Post-Call
    ctx.add_shutdown_callback(lambda: on_shutdown(ctx, chat_context))

    assistant.start(ctx.room)
    await assistant.say("Agenzia Immobiliare Domus, sono Laura. Come posso aiutarti oggi?")

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))