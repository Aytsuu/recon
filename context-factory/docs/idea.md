# Universal Customer-Support Access Layer

> Speak your problem once. The platform figures out who needs to hear it, what information they need, and contacts them for you.

## Conceptual workflow

```mermaid
flowchart TD
    Speech[Human speech] --> STT[AssemblyAI Realtime STT]
    STT --> Transcript[Live transcript stream]
    Transcript --> Extraction[Event extraction]
    Extraction --> Orchestrator[Orchestrator]

    Orchestrator --> Intent[Intent Agent]
    Orchestrator --> Context[Context Agent]
    Orchestrator --> Contact[Contact Agent]

    Intent --> Concern[Concern type, desired outcome, severity, and timeline]
    Context --> Provider[Provider, product/service, and relevant facts]
    Contact --> Request[Compose message, attach context, translate if needed, and send or submit ticket]

    Concern --> Confirmation[Orchestrator]
    Provider --> Confirmation
    Request --> Confirmation
    Confirmation --> UserConfirmation[User confirmation]
    UserConfirmation --> Support[Customer support]
```

## Agents

### 1. Orchestrator

The Orchestrator owns the entire workflow. It decides whether the system has:

1. Understood the problem.
2. Identified the provider.
3. Collected enough support information.

Once those conditions are satisfied, it invokes the Contact Agent.

```mermaid
flowchart TD
    Start[Support request] --> Problem{Do I understand the problem?}
    Problem -- No --> ClarifyProblem[Ask for clarification]
    Problem -- Yes --> Provider{Do I know the provider?}
    Provider -- No --> ClarifyProvider[Ask for provider details]
    Provider -- Yes --> Information{Do I have enough support information?}
    Information -- No --> Gather[Gather missing information]
    Information -- Yes --> Contact[Invoke Contact Agent]
```

### 2. Intent Agent

The Intent Agent converts casual speech into a structured support request.

**Example input**

> “Our internet has been terrible since last night. It keeps disconnecting every five minutes and I already restarted the router twice.”

**Example output**

```json
{
  "category": "internet_connectivity",
  "problem": "intermittent_connection",
  "started": "last night",
  "severity": "high",
  "attempted_resolutions": [
    "router_restart"
  ],
  "desired_resolution": "restore_stable_connection"
}
```

### 3. Context Agent

The Context Agent determines:

- The company or provider
- The product or service
- The equipment model
- The problem category
- Troubleshooting already performed
- Information required by that company's support team

**Example input**

> “My Converge connection keeps dropping and the LOS light keeps blinking red.”

**Example context**

| Field | Value |
| --- | --- |
| Provider | Converge ICT |
| Service | Residential fiber internet |
| Equipment | Fiber ONU/router |
| Indicator | LOS blinking red |
| Likely category | Fiber optical signal / connectivity issue |
| Already attempted | Router restart |

**Information potentially required**

- Account number
- Subscriber name
- Service address
- Router status

### 4. Contact Agent

The Contact Agent is the action agent. It receives structured context such as:

```json
{
  "provider": "Converge ICT",
  "problem": "...",
  "customer_context": "...",
  "preferred_channel": "email"
}
```

It turns that context into an appropriate support request.

**Example generated message**

> Hello Converge Support,
>
> I'm experiencing intermittent internet connectivity since approximately 10 PM yesterday. The LOS indicator on my ONU is blinking red, and the connection disconnects approximately every five minutes.
>
> I have already restarted the router, but the issue persists.
>
> Could you please check whether there is an outage or line issue affecting my connection?

**Example confirmation**

> **Ready to contact Converge**
>
> - **Channel:** Email
> - **Issue:** Internet connectivity
> - **Priority:** High
>
> [Review Message] [Send]

## Native-language input

Someone should not need to know how to communicate a technical problem in formal English. They can describe the issue naturally in their own language.

**Example input (Cebuano)**

> “Sige ra gyud og kawala among internet unya pula ang LOS. Gi restart na nako ang router pero mao gihapon.”

The system's conceptual pipeline becomes:

```mermaid
flowchart TD
    NativeSpeech[Native speech] --> Recognition[Speech recognition]
    Recognition --> Normalize[Normalize or translate internally]
    Normalize --> Extract[Extract actual problem]
    Extract --> Technical[Gather technical context]
    Technical --> Generate[Generate professional support request]
    Generate --> Provider[Provider]
```
