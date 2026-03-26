# Security Notice

## Sensitive Values in This Project

⚠️ **IMPORTANT**: Never commit actual API keys or database credentials to the repository.

### What was exposed?
- A **real NVIDIA OpenAI API key** was previously committed in `backend/.env`
- This key has been **replaced with a placeholder** in the latest commit

### Action Required:
1. **Immediately rotate** the exposed NVIDIA key in your account:
   - Go to https://build.nvidia.com/profile (NVIDIA developer portal)
   - Revoke or regenerate API keys
   - Use the new key in Render dashboard only
   
2. **Never commit secrets again**:
   - `.env` is in `.gitignore` — safe for local dev
   - `.env.example` shows template WITHOUT real values — safe to commit

### Environment Variables Pattern:

**Local Development (`.env` file — never commit)**:
```
ANTHROPIC_API_KEY=sk-ant-your-real-key
NVIDIA_OPENAI_API_KEY=nvapi-your-real-key
DATABASE_URL=sqlite:///data/verimed.sqlite3
```

**Production (Render Dashboard — set via UI, never in code)**:
```
ANTHROPIC_API_KEY=<set via Render dashboard>
NVIDIA_OPENAI_API_KEY=<set via Render dashboard>
DATABASE_URL=<Neon connection string>
ALLOWED_ORIGINS=https://verimed-web.netlify.app,https://verimed-api.onrender.com
```

### Database URL Handling:

- **Local dev**: SQLite path in `.env` → config.py reads it
- **Production on Render**: Neon Postgres connection string set as `DATABASE_URL` env var in Render dashboard
  - Render injects it at runtime
  - config.py respectfully uses `os.getenv("DATABASE_URL", "...")` as fallback

### Verification Checklist:

- [ ] `.env` file is in `.gitignore`
- [ ] `.env.example` committed (no real values)
- [ ] NVIDIA API key rotated/regenerated
- [ ] Render dashboard has new `ANTHROPIC_API_KEY` and `NVIDIA_OPENAI_API_KEY`
- [ ] No other secrets in documentation or comments
- [ ] `git log` history checked for any committed keys (consider `git filter-branch` if found)

### Tools to prevent accidental commits:
```bash
# Scan for API key patterns:
git grep -n "nvapi-\|sk-ant-\|postgresql://" -- ':!.git'

# Use a pre-commit hook (optional):
pip install pre-commit
```

---

**References**:
- [Render Env Vars Documentation](https://render.com/docs/environment-variables)
- [Neon Connection Strings](https://neon.tech/docs/connect/connection-details)
- [OWASP: Secrets Management](https://owasp.org/www-community/controls/Key_Management)
