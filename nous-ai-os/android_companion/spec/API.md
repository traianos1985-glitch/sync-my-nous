# NOUS Android Companion v1

Purpose:

- Give NOUS real Android device control through Accessibility Service.
- NOUS Core sends approved actions.
- Companion executes only allowlisted actions.

Capabilities:

- read_ui_tree
- tap_node
- tap_coordinates
- swipe
- input_text
- press_back
- press_home
- current_app
- screen_snapshot_metadata

## Broadcast contract

The exported explicit ADB receiver requires all of the following:

- Explicit component: `com.nous.companion/.CommandReceiver`
- Action: `com.nous.companion.COMMAND`
- Allowlisted `command` extra: `state`, `ui_tree`, `back`, `home`, or `tap`
- A valid per-install `pairing_token` extra copied from the companion app

Example:

```sh
adb shell am broadcast \
  -n com.nous.companion/.CommandReceiver \
  -a com.nous.companion.COMMAND \
  --es command state \
  --es pairing_token 'PASTE_TOKEN_FROM_COMPANION'
```

For a tap, also pass finite non-negative coordinates with `--ef x 100.0 --ef y 200.0`.
The token is stored in private app preferences, is not written to logcat, and must
not be committed or placed in shared scripts. Copy it from the app only to a
trusted local ADB workflow. Reinstalling the app creates a new token.

Android 14 and newer also check the broadcast sender UID, allowing only adb shell
or the companion app UID. On older Android versions the platform API used for
that UID check is unavailable, so the random per-install pairing token is the
required protection against arbitrary third-party apps sending broadcasts.

Security:

- local only
- pairing token required on every supported Android version
- dangerous actions blocked
- no payments
- no SMS
- no destructive actions without approval
- UI-tree text is sensitive and must never be logged
