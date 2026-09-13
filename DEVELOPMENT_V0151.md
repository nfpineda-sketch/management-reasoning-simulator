# v0.15.1 — Patient conversation repair

The Talk form was submitting but returned a generic provider-failure message. The exact live failure could not be recovered from that message: the previous handler hid all API/JSON failures. No deployed credentials or provider logs were accessed.

## Changes

- Common opening questions, including “How can I help you?” and Spanish equivalents, select the recorded presenting symptoms immediately without requiring a provider request. They do not supply an unsolicited urinary review of systems.
- Directed history questions in English or Spanish select only matching recorded facts. Urinary symptoms remain available immediately when asked. Associated symptoms keep their existing concise response.
- Other phrasing uses the configured conversation model. Its output remains a validated list of source IDs, never generated clinical content.
- The API budget increases from 500 to 4096 tokens. The [official OpenAI reasoning documentation](https://developers.openai.com/api/docs/guides/reasoning#allocating-space-for-reasoning) explains that the output limit also includes reasoning and may be exhausted before a visible answer. Budget exhaustion is a plausible failure path, not a confirmed diagnosis of this deployment's failure.
- SDK construction, API errors, incomplete replies, refusals and malformed source selection are handled. An unmatched question during a failure asks for rephrasing; it does not claim the clinical information is absent. A valid empty source selection is explicitly “not documented.”
- Logs contain only sanitized failure categories and HTTP status numbers. They exclude questions, credentials, provider bodies and raw error messages.

This repair does not change clinical physiology, simulation time, the source history, the image system or the other published branches. The existing inability to obtain new spoken history from a sedated, obtunded or unresponsive patient is retained. Live provider connectivity is not verified by the mocked test suite.

Verification includes bilingual source selection, the screenshot question through the real Streamlit Talk form, a directed urinary follow-up, provider/initialization failure handling, malformed outputs and preservation of patient state.
