# Grand Line Draft 3.6.1 – Hotfix

- Fixed `StreamlitWidgetAlreadyInstantiatedError` when applying the game mode and player names.
- The mode radio's session-state key is no longer reassigned after the widget has been instantiated. Its selected value is still read normally, and the correct internal game-mode value is applied before the active game is reset.
- No draft rules, character ratings, or interface behavior were otherwise changed.
