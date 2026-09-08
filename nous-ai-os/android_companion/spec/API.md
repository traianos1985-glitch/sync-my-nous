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

Security:
- local only
- pairing token required
- dangerous actions blocked
- no payments
- no SMS
- no destructive actions without approval
