import logging
import asyncio
from dotenv import load_dotenv

# Import del core di LiveKit Agents
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)

# Import del nuovo agente "VoicePipelineAgent" (sostituisce il vecchio PipelineAgent)
from livekit.agents.pipeline import VoicePipelineAgent

# Import dei plugin (STT, LLM, TTS, VAD)
from livekit.plugins import openai, deepgram, silero, elevenlabs

# Carica le variabili d'ambiente (.env)
load_dotenv()

# Configurazione Log
logger = logging.getLogger("voice-agent")

async def entrypoint(ctx: JobContext):
    """
    Funzione principale che viene eseguita quando un utente si connette.
    """
    
    # 1. Connessione alla stanza
    # AutoSubscribe.AUDIO_ONLY fa sì che l'agente riceva solo l'audio dell'utente
    logger.info(f"Connessione alla stanza {ctx.room.name}...")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # 2. Attesa del partecipante
    # L'agente aspetta che un utente entri e inizi a trasmettere audio
    participant = await ctx.wait_for_participant()
    logger.info(f"Utente connesso: {participant.identity}")

    # 3. Configurazione del "Cervello" (Il Prompt di sistema)
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "Sei un assistente vocale utile e simpatico creato con LiveKit. "
            "Rispondi in modo breve e colloquiale, come in una vera conversazione telefonica. "
            "Usa l'italiano."
        )
    )

    # 4. Creazione della Pipeline Vocale
    # Qui assembliamo i pezzi: VAD (Rilevamento voce) -> STT (Trascrizione) -> LLM (Intelligenza) -> TTS (Voce sintetica)
    agent = VoicePipelineAgent(
        vad=silero.VAD.load(),      # Rileva quando l'utente parla
        
        # Scegli il tuo STT (Trascrizione). Deepgram è molto veloce.
        stt=deepgram.STT(language="it"), 
        # In alternativa: stt=openai.STT(),

        # Il cervello (GPT-4o-mini è veloce ed economico)
        llm=openai.LLM(model="gpt-4o-mini"),

        # Scegli il tuo TTS (Voce). 
        # Usa OpenAI TTS per semplicità o ElevenLabs per qualità.
        tts=openai.TTS(), 
        # In alternativa: tts=elevenlabs.TTS(),

        chat_ctx=initial_ctx,
    )

    # 5. Avvio dell'Agente
    # Collega l'agente alla stanza e all'utente specifico
    agent.start(ctx.room, participant)

    # 6. Saluto iniziale
    # L'agente parla per primo
    await agent.say("Ciao! Sono pronto. Di cosa vogliamo parlare oggi?", allow_interruptions=True)

# Avvio dell'applicazione
if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
