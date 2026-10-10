# NOUS Built-in Utility Toolkit

The utility toolkit is offline-first and uses Python's standard library. It is available through the existing chat command router; no extra package, API key, or network service is required.

## Discover tools

- `/tools`
- `tools`
- `tool catalog`
- `διαθέσιμα εργαλεία`

The catalog returns tool names, categories, descriptions, command examples, risk classes, and whether approval is always required or depends on the runtime action.

## Commands

| Command                            | Example                      | Purpose                                                                |
| ---------------------------------- | ---------------------------- | ---------------------------------------------------------------------- |
| `calculate` / `calc` / `υπολόγισε` | `calculate sqrt(81) + 2*pi`  | Safe arithmetic and approved math functions; never uses Python `eval`. |
| `convert` / `μετατροπή`            | `convert 12 km to miles`     | Length, mass, volume, speed, and temperature conversion.               |
| `time`                             | `time Europe/Athens`         | Local time by default, or time in an IANA timezone, plus UTC.          |
| `text stats`                       | `text stats hello world`     | Character, word, line, and paragraph counts.                           |
| `json validate`                    | `json validate {"ok": true}` | JSON syntax validation, top-level type, and parse location.            |
| `sha256`                           | `sha256 NOUS`                | SHA-256 checksum of supplied UTF-8 text.                               |

Greek aliases are supported for calculation, conversion, text statistics, and JSON validation.

## Limits and trust boundaries

- The calculator accepts numeric literals, parentheses, basic arithmetic, the constants `pi` and `e`, and a fixed list of mathematical functions. It rejects attribute access, imports, comprehensions, and arbitrary function calls.
- Unit conversion rejects unknown or incompatible units.
- The checksum tool hashes the text provided to it; it does not hash a file on disk.
- The catalog is descriptive metadata, not a substitute for runtime authorization. State-changing and agent actions must still pass through their existing control paths.
- These tools do not claim external facts and do not require credentials.
