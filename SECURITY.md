# Security

Do not expose the Streamlit or Ollama ports to the public internet. This project assumes a trusted local desktop and binds both servers to loopback. It is not a multi-user hosted service.

The bookmark URI handler accepts only videosummarizer://open, runs a fixed local command without a shell, and never accepts a video URL or arbitrary command as a protocol argument. Register it only from a trusted copy of this project. Existing unrelated protocol handlers are not overwritten.

For security reports, use this repository's GitHub private vulnerability reporting if enabled; otherwise contact the maintainer before disclosing exploitable details publicly. Never include secrets, browser cookies or private videos in public issues.
