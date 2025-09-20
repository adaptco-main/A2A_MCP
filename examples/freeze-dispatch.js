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

