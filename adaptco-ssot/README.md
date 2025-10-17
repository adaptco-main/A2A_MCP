# core-orchestrator

This branch hosts the preview-ready assets, helper snippets, and reference docs that power AdaptCo's core orchestrator video workflows.

> **Note:** This README is duplicated across the packaged artifact directories in this branch (`adaptco-core-orchestrator/`, `adaptco-previz/`, and `adaptco-ssot/`) so that every bundle ships with the same documentation. Update this file to make changes everywhere.

## selector.preview.bundle.v1 overview

The active preview bundle focuses on giving collaborators a shared rehearsal surface while feedback is collected.

### Modules currently live
- **HUD Walkthrough** – Guided tour of the interactive overlay so reviewers can orient themselves quickly.
- **Rehearsal Prompts** – Rotating prompt palette for exploring emotional or tonal variations before final capture.
- **Compliance Overlay** – Lightweight checks that surface policy or brand guardrails directly inside the preview.

### Rehearsal prompt palette
Choose one of the prompt macros below when requesting a rehearsal render. Each macro pairs a thematic cue with sensory guidance the renderer will honor.

| Prompt key          | Visual + emotive cues            |
| ------------------- | -------------------------------- |
| `rupture.flare`     | irony shimmer + spark trace      |
| `restoration.loop`  | breath sync + glyph fidelity     |
| `mesh.response`     | empathy shimmer + echo match     |

## Requesting a rehearsal visualization
1. **Select a prompt** – Start with one of the keys above to anchor the vibe of the pass you need.
2. **Add scenario notes** – Provide any narrative beats, dialogue hints, or camera timing that should accompany the prompt.
3. **Specify delivery context** – Note the target surface (HUD walkthrough, compliance overlay, etc.) so the correct module frames the render.
4. **Confirm review timing** – Mention deadlines or live review slots so the orchestration bot can schedule the preview drop appropriately.

## GitHub dispatch helper snippet
If you need to freeze a generated artifact before sharing, you can trigger a GitHub repository dispatch by adapting the snippet below (replace the placeholder values before running it in Node.js 18+ or any fetch-capable runtime):

```javascript
// Example: Freeze button dispatch
fetch("https://api.github.com/repos/your-org/your-repo/dispatches", {
  method: "POST",
  headers: {
    "Authorization": "Bearer YOUR_TOKEN",
    "Accept": "application/vnd.github.v3+json"
  },
  body: JSON.stringify({
    event_type: "freeze_artifact",
    client_payload: {
      artifact_id: "abc123"
    }
  })
});
```

For convenience, the same example lives at `examples/freeze-dispatch.js` so you can edit and execute it locally.
