# Contributing

Thanks for considering a contribution to `youtube-downloader`.

## Before opening an issue

- Search existing issues for duplicates.
- Include your operating system and versions of Python, `uv`, and FFmpeg.
- Share the command you ran with private or sensitive parts removed.
- Include relevant error messages, but do not attach copyrighted media or credentials.

## Development setup

```bash
uv sync
```

Run the automated tests before submitting a pull request:

```bash
uv run python -m unittest discover -s tests -v
```

## Pull requests

- Keep changes focused and explain the problem they solve.
- Add or update tests for behavior changes.
- Update `README.md` and `USER_MANUAL.md` when options or behavior change.
- Do not add credentials, cookies, personal paths, downloaded media, reports, or local archives.
- Do not add features intended to bypass DRM, paywalls, or access controls.
