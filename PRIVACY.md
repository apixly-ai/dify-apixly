# Apixly Media plugin privacy notice

Effective date: October 23, 2026. Contact: support@apixly.ai.

## Data collected and transmitted

Manual-key mode uses the API key stored in Dify's secret credential and sends it only to fixed `https://apixly.ai/v1` routes. Optional OAuth mode uses a registered confidential client configured privately by the workspace administrator. Authorization exchanges the one-time code and client proof only with `https://apixly.ai/api/integrations/token`; Dify stores the resulting revocable scoped connection token and nonsecret account/selected-Key metadata. Media and catalog requests send that connection token only to fixed Apixly integration routes. The plugin does not collect a website password, full website JWT, refresh token or underlying API key in OAuth mode. It also sends the prompts, exact model IDs, model parameters, image references and video/audio reference URLs provided to the tools. These inputs may contain personal data if you include it. Do not provide data you are not authorized to share.

Reference URLs and base64 images are forwarded to Apixly for processing. This plugin does not itself fetch those URLs. Apixly may retrieve the referenced media and route generation inputs to the upstream model service that fulfills the selected model. This notice does not promise zero retention by Apixly, Dify, storage services, or upstream model providers. Review Apixly's published service privacy policy and applicable model-provider terms, and ask support for processing details relevant to your use case before sending sensitive material.

## Storage and logging

The plugin adds no independent analytics, advertising identifiers, telemetry, persistent storage, database, file writes, or request-content logging. Credentials and media necessarily exist in memory while a tool executes. Model lists, capabilities, safe errors and hashed cache identities are cached in memory within each plugin process; the cache writes no files and stores no raw credential as a cache key. Dify stores provider credentials, application configuration, workflow results, and optional downloaded files according to the Dify workspace/operator's configuration and policies. Apixly maintains account, task, usage/billing and operational records, and retains generated media according to its service policies and task lifetimes. The plugin does not change those retention policies or delete those records.

## Third-party sharing and network destinations

The plugin's expected outbound network domains are `apixly.ai` for API calls and signed downloads, and `platform.apixly.ai` for signed downloads. Result downloads accept only signed Apixly content URLs, do not follow redirects, and send no API key. Data returned to Dify can include task IDs, model IDs, task status/errors, generated media URLs, numeric usage meters and media bytes. A signed result URL permits temporary access to its media; protect it as sensitive data. If you choose to pass media URLs/files to other Dify tools, those later transfers are controlled by your workflow and those services' policies.

## User choices and deletion

You decide which tool inputs and files to submit. Revoke the manual API key or account connection in Apixly to stop future authenticated calls, remove the credential/plugin from Dify, and delete workflow outputs/downloaded files according to your Dify operator's procedures. A rejected/revoked connection clears that identity's in-process catalog cache when next checked. Dify does not notify this plugin when an operator deletes a credential; cached model metadata contains no raw secret and is not available without a credential. These actions do not automatically cancel an already submitted generation or erase Apixly/upstream records. For account data, retention or deletion requests, contact support@apixly.ai. For Dify-managed storage and logs, contact your workspace operator or [Dify](https://dify.ai/privacy).
