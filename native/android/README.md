# PDI Vault — Android (Jetpack Compose)

A native Android app in Kotlin + Jetpack Compose, wired to the PDI vault
backend. Same token sign-in and three screens as the other targets —
**Overview → Vault → Audit** — calling `/records` and `/audit`.

## Run in the emulator

Open `native/android` in **Android Studio** (Koala or newer) and press **Run**,
or from the command line:

```bash
cd native/android
gradle wrapper --gradle-version 8.9   # first time only — generates ./gradlew
./gradlew installDebug                 # installs onto a running emulator/device
```

> The Gradle **wrapper JAR** is intentionally not committed (it's a binary).
> Android Studio adds it automatically on first open, or run the
> `gradle wrapper` line above with a local Gradle.

Start the backend on the host first:

```bash
# from the repo root
PDI_CORS_ORIGINS=* uvicorn pdi.api:app
```

Sign in by pasting a tenant token (`pdi_…`). The default base URL is
**`http://10.0.2.2:8000`** — that is how the Android emulator reaches `localhost`
on your machine (not `127.0.0.1`). On a physical device, set the server field to
your computer's LAN IP. Cleartext http to that host is allowed via
`usesCleartextTraffic` in the manifest.

## Layout

| Path | Role |
| --- | --- |
| `app/build.gradle.kts` | module config (Compose, SDK 34, Kotlin 2.0) |
| `.../MainActivity.kt` | entry point + bottom-nav shell / sign-in switch |
| `.../ApiClient.kt` | coroutine client (`HttpURLConnection` + `org.json`) |
| `.../AppState.kt` | `VaultViewModel` — token + base URL, persisted |
| `.../ui/Theme.kt` | the dark-OLED palette + card modifier |
| `.../ui/Screens.kt` | Welcome (sign-in), Overview, Vault, Audit |

## Versions

AGP 8.5.2 · Kotlin 2.0.20 (Compose compiler plugin) · Compose BOM 2024.09.02 ·
compileSdk 34 · minSdk 26. No third-party network library — plain
`HttpURLConnection` keeps the dependency surface small.
