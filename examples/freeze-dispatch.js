async function main() {
  if (typeof fetch !== "function") {
    throw new Error("This example requires Node.js 18 or later to provide the fetch API.");
  }

  const {
    GITHUB_OWNER,
    GITHUB_REPO,
    GITHUB_TOKEN,
    ARTIFACT_ID,
    DISPATCH_EVENT,
  } = process.env;

  const missingVariables = [
    ["GITHUB_OWNER", GITHUB_OWNER],
    ["GITHUB_REPO", GITHUB_REPO],
    ["GITHUB_TOKEN", GITHUB_TOKEN],
    ["ARTIFACT_ID", ARTIFACT_ID],
  ]
    .filter(([, value]) => !value)
    .map(([name]) => name);

  if (missingVariables.length) {
    throw new Error(
      `Missing required environment variables: ${missingVariables.join(", ")}`
    );
  }

  const eventType = DISPATCH_EVENT || "freeze_artifact";
  const endpoint = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/dispatches`;

  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${GITHUB_TOKEN}`,
      Accept: "application/vnd.github.v3+json",
    },
    body: JSON.stringify({
      event_type: eventType,
      client_payload: {
        artifact_id: ARTIFACT_ID,
      },
    }),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(
      `GitHub API request failed with ${response.status} ${response.statusText}: ${errorBody}`
    );
  }

  console.log(
    `Dispatch event "${eventType}" queued for artifact "${ARTIFACT_ID}" in ${GITHUB_OWNER}/${GITHUB_REPO}.`
  );
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});

