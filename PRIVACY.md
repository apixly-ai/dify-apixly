# Apixly Media plugin privacy notice

Effective date: October 23, 2026. Contact: support@apixly.ai.

## Data collected and transmitted

This plugin uses the Apixly API key stored in the Dify provider's secret credential. It sends that key only as an Authorization header to fixed API routes at `https://apixly.ai/v1`. It also sends the prompts, exact model IDs, model parameters, image references and video/audio reference URLs provided to the tools. These inputs may contain personal data if you include it. Do not provide data you are not authorized to share.

Reference URLs and base64 images are forwarded to Apixly for processing. This plugin does not itself fetch those URLs. Apixly may retrieve the referenced media and route generation inputs to the upstream model service that fulfills the selected model. This notice does not promise zero retention by Apixly, Dify, storage services, or upstream model providers. Review Apixly's published service privacy policy and applicable model-provider terms, and ask support for processing details relevant to your use case before sending sensitive material.

## Storage and logging

The plugin adds no independent analytics, advertising identifiers, telemetry, persistent storage, database, file writes, or request-content logging. Credentials and media necessarily exist in memory while a tool executes. Dify stores provider credentials, application configuration, workflow results, and optional downloaded files according to the Dify workspace/operator's configuration and policies. Apixly maintains account, task, usage/billing and operational records, and retains generated media according to its service policies and task lifetimes. The plugin does not change those retention policies or delete those records.

## Third-party sharing and network destinations

The plugin's expected outbound network domains are `apixly.ai` for API calls and signed downloads, and `platform.apixly.ai` for signed downloads. Result downloads accept only signed Apixly content URLs, do not follow redirects, and send no API key. Data returned to Dify can include task IDs, model IDs, task status/errors, generated media URLs, numeric usage meters and media bytes. A signed result URL permits temporary access to its media; protect it as sensitive data. If you choose to pass media URLs/files to other Dify tools, those later transfers are controlled by your workflow and those services' policies.

## User choices and deletion

You decide which tool inputs and files to submit. Revoke the API key in Apixly to stop future authenticated calls, remove the credential/plugin from Dify, and delete workflow outputs/downloaded files according to your Dify operator's procedures. These actions do not automatically cancel an already submitted generation or erase Apixly/upstream records. For account data, retention or deletion requests, contact support@apixly.ai. For Dify-managed storage and logs, contact your workspace operator or [Dify](https://dify.ai/privacy).
