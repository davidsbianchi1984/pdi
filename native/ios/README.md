# PDI Vault — iOS (SwiftUI)

A native SwiftUI app for iPhone, wired to the PDI vault backend. A token sign-in
plus three screens — **Overview → Vault → Audit** — hitting the real `/records`
and `/audit` endpoints.

## Run in the Simulator (macOS)

Requires Xcode 15+ and [XcodeGen](https://github.com/yonyz/XcodeGen)
(`brew install xcodegen`).

```bash
cd native/ios
xcodegen generate          # writes PdiVault.xcodeproj from project.yml
open PdiVault.xcodeproj    # then ⌘R with an iPhone simulator selected
```

Start the backend first, on the host (the Simulator shares your Mac's network,
so `127.0.0.1` resolves):

```bash
# from the repo root
PDI_CORS_ORIGINS=* uvicorn pdi.api:app
```

Sign in by pasting a tenant token (`pdi_…`). The default base URL is
`http://127.0.0.1:8000` (see `Sources/ApiClient.swift`); `Info` in `project.yml`
sets `NSAllowsLocalNetworking` so the Simulator can reach plain-http localhost.

## Layout

| File | Role |
| --- | --- |
| `project.yml` | XcodeGen spec (bundle id, iOS 16 target, ATS exception) |
| `Sources/PdiVaultApp.swift` | `@main` app + root tab bar / sign-in switch |
| `Sources/ApiClient.swift` | async `URLSession` client + wire models |
| `Sources/AppState.swift` | tenant token + base URL, persisted |
| `Sources/Theme.swift` | the dark-OLED palette |
| `Sources/Views/*` | Welcome (sign-in), Overview, Vault, Audit, Sources (Robots/Connectors), Transfers (Outbound/Intake) |

## Not yet wired

This is a functional scaffold, not the full screen gallery. The connected-apps
catalog and (admin-gated) key rotation remain backend-only surfaces.
