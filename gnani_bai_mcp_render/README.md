# Gnani bAI MCP

Minimal MCP wrapper around Gnani Speech-to-Text for the bAI household meal coordinator.

## Exposed tool

`transcribe_cook_audio(audio_url, language_code="en-IN", output_format="transcribe")`

Use `en-IN` for Latin-script output or `hi-IN` for Hindi/Devanagari output.

## Deploy on Render

1. Put `server.py`, `requirements.txt`, and `render.yaml` in a GitHub repo.
2. In Render, create a Blueprint from that repo, or create a Python Web Service manually.
3. Add environment variable:
   `GNANI_API_KEY` = your actual Gnani API key
4. Deploy.

Your MCP URL will be:

`https://<your-render-service>.onrender.com/mcp`

## Register in AgenticOrg

Go to **Connectors → Register Connector**:

- Connector name: `gnani_mcp_akshit` (or another unique name)
- Check **MCP**
- MCP Server URL: `https://<your-render-service>.onrender.com/mcp`
- Category: `Comms`
- Auth Type: `None`

The Gnani API key stays on Render.

AgenticOrg should discover:

`transcribe_cook_audio`

Then add that connector/tool to bAI.

## Demo

Cook voice → Gnani MCP → transcript → bAI reasoning → household-state update → WhatsApp instruction → Grantex commerce only if needed.

For the fastest demo, use a short public audio URL as the tool input.
