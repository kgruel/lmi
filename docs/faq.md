# FAQ

Frequently asked questions about **lmi**, installation, configuration, plugins, and troubleshooting.

## 1. Installation Issues

**Q:** lmi is not found after installation.  
**A:** Ensure your Python environment's `bin` directory is in your PATH. Try restarting your terminal or running `uv pip install lmi` again.

## 2. Config Precedence

**Q:** Which config value is used if I set it in multiple places?  
**A:** lmi uses the first value found in this order: CLI argument > environment variable > env-specific `.env` > main `.env` > default.

## 3. Plugin Safety

**Q:** Are plugins safe to install?  
**A:** Only install plugins from trusted sources. Plugins run in the same process as lmi and can access your system and secrets.

## 4. Token Cache Issues

**Q:** How do I clear a corrupted or expired token cache?  
**A:** Delete the relevant file in `~/.cache/lmi/tokens/` and rerun your command.

## 5. Troubleshooting

**Q:** How do I get more detailed error messages?  
**A:** Use `-v` or `-vv` for more verbose output and check the log file at `~/.local/share/lmi/lmi.log`.

**Q:** Where can I get more help?  
**A:** Use `lmi --help`, check the documentation, or open an issue with logs and error details. 