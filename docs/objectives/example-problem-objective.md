# Realtime Conversational Website - TeamBot Objective

## Objective

**Goal**: Build a conversational website with real-time voice and text communication to Azure OpenAI GPT Realtime model

**Problem Statement**: Need a web interface that enables natural conversations with AI using both text and voice input. The system must support voice interruption - allowing users to interrupt the AI's response mid-speech and immediately provide new input, mimicking natural human conversation patterns.

**Success Criteria**:
- [ ] Users can send text messages and receive AI responses in real-time
- [ ] Users can use push-to-talk button to communicate via voice
- [ ] Voice responses can be interrupted when user presses push-to-talk during AI speech
- [ ] AI stops speaking and listening immediately (<500ms) when interrupted
- [ ] Application runs locally in devcontainer
- [ ] Application is deployable to Azure
- [ ] End-to-end voice latency < 2 seconds (measured via performance monitoring)
- [ ] Voice interruption response time < 500ms
- [ ] WebSocket reconnection with exponential backoff on failure
- [ ] Security baseline implemented (authentication, rate limiting, input validation)

---

## Technical Context

**Target Codebase**: /workspaces/realtime-website/

**Primary Language/Framework**: Python (FastAPI backend) / JavaScript (React + Vite frontend)

**Testing Preference**: Hybrid (TDD for backend API/critical paths, Code-First for UI components)

**Key Constraints**:
- Must use Azure OpenAI Realtime API (gpt-4-realtime-preview or later)
- Requires Azure OpenAI account with Realtime API access
- **Must use RBAC (Role-Based Access Control) for authentication - API keys are disabled**
- RBAC Authentication Approach:
  - **Production**: Azure Managed Identity (recommended)
  - **Local Development**: Azure CLI authentication (`az login` + DefaultAzureCredential)
  - **Note**: Local development requires Azure RBAC role assignment to developer identity (minimum: `Cognitive Services OpenAI User` role on the Azure OpenAI resource)
- Must use push-to-talk for voice input (not automatic voice detection initially)
- Must support both local devcontainer and Azure deployment
- Audio streaming must use lowest latency method available
- Simple chat UI initially (will be expanded in future)
- WebSocket-based real-time communication

---

## Additional Context

**Architecture Approach**:
- SPA frontend (React + Vite) with WebSocket client
- FastAPI backend with WebSocket server
- Azure OpenAI Realtime API integration
- WebRTC MediaStream API for browser audio capture
- Docker-based deployment strategy

**Key Features**:
1. **Text Chat**: Basic chat interface with message history
2. **Voice Input**: Push-to-talk button with audio streaming
3. **Voice Output**: Audio playback from AI responses
4. **Interruption**: Immediate stop of playback and backend streaming when user interrupts

**Future Expansion Ready**:
- Voice Activity Detection (VAD) for hands-free mode
- Conversation persistence to database
- Enhanced UI features (formatting, reactions, avatars)
- Multi-user support

---

## Prerequisites

- Azure OpenAI account with Realtime API access
- Azure subscription for deployment
- Azure RBAC configuration:
  - Managed Identity OR Service Principal with roles:
    - `Cognitive Services OpenAI User` (minimum, for API access)
    - `Cognitive Services OpenAI Contributor` (if model deployment needed)
  - Identity must be assigned to the Azure OpenAI resource
- For local development: Azure CLI installed and authenticated (`az login`)
- Docker installed for local development

## Known Limitations (MVP)

- Push-to-talk only (Voice Activity Detection in future)
- In-memory conversation storage (no persistence)
- Single user per session

---

## Important Notes

⚠️ **RBAC Requirement Impact**: The implementation plan (v2.0) was created assuming API key authentication. Phase 1, Task SETUP-3 must be updated to use Azure RBAC authentication with `DefaultAzureCredential` instead of API keys before implementation begins.

**Required Plan Updates:**
- SETUP-3: Replace API key logic with `DefaultAzureCredential` from `azure-identity` package
- Environment variables: Update `.env-sample` for RBAC (Azure endpoint only, no API keys)
- Dependencies: Add `azure-identity` package to Python requirements
- Devcontainer: Mount Azure CLI credentials or document `az login` requirement

**RBAC Implementation Reference:**
```python
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI

credential = DefaultAzureCredential()
client = AzureOpenAI(
    azure_endpoint="https://<resource>.openai.azure.com/",
    azure_ad_token_provider=credential.get_token("https://cognitiveservices.azure.com/.default")
)
```

---

**Detailed Plan**: See `/home/vscode/.copilot/session-state/teambot-pm/plan.md` (v2.0, post-review) for full implementation plan with 38 tasks across 7 phases.

**Complexity**: Medium-High (38 tasks, 7 phases)

**To Run**: `uv run teambot run docs/realtime-conversational-website.md`
