import logging
import os
import aiohttp
from dotenv import load_dotenv

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import deepgram, elevenlabs, openai, silero
from typing import Annotated

load_dotenv()
logger = logging.getLogger("real-estate-agent")
logger.setLevel(logging.INFO)

# --- DEBUG CHIAVI ---
groq_key = os.getenv("GROQ_API_KEY")
if not groq_key:
    logger.error("❌ ERRORE CRITICO: Manca la GROQ_API_KEY nelle variabili d'ambiente!")
else:
    logger.info(f"✅ GROQ Key caricata: {groq_key[:4]}...{groq_key[-4:]}")
# --------------------

class RealEstateTools(llm.FunctionContext):
    @llm.ai_callable(description="Cerca immobili nel database.")
    async def search_property(self, zona: Annotated[str, llm.TypeInfo(description="Zona")]):
        logger.info(f"🔎 Cerco casa in zona {zona}...")
        return "Ho trovato un Trilocale in Via Roma a 250.000 euro."

async def on_shutdown(ctx: JobContext, chat_ctx: llm.ChatContext):
    logger.info("📞 Chiamata terminata.")

async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    participant = await ctx.wait_for_participant()
    
    initial_ctx = llm.ChatContext().append(
        role="system",
        text="Sei Laura, agente immobiliare. Rispondi in italiano."
    )

    agent = VoicePipelineAgent(
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-2", language="it"),
        llm=openai.LLM(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY"),
            # CAMBIO MODELLO: Usiamo l'8B che è più veloce e stabile per i test
            model="llama3-8b-8192", 
        ),
        tts=elevenlabs.TTS(
            api_key=os.getenv("ELEVENLABS_API_KEY"),
            voice=elevenlabs.Voice(
                id="JBFqnCBsd6RMkjVDRZzb",
                name="George",
                category="premade"
            ),
            model="eleven_turbo_v2_5"
        ),
        fnc_ctx=RealEstateTools(),
        chat_ctx=initial_ctx
    )

    agent.start(ctx.room, participant)
    await agent.say("Agenzia Immobiliare Domus, sono Laura. Dimmi tutto!", allow_interruptions=True)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
