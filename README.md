# Burger Hut

A Flask-based food ordering app.

## Setup

1. Copy `.env.example` to `.env`
2. Fill in your database and mail server values
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the app:

   ```bash
   python app.py
   ```

## Deployment

- Push your code to GitHub, but do not commit `.env`
- Use environment variables in your hosting provider for:
  - `SECRET_KEY`
  - `DATABASE_URL`
  - `MAIL_SERVER`
  - `MAIL_PORT`
  - `MAIL_USE_TLS`
  - `MAIL_USERNAME`
  - `MAIL_PASSWORD`
  - `MAIL_DEFAULT_SENDER`

## Database

- For local dev, use the fallback `DATABASE_URL` in `.env`
- For production, use a managed MySQL or cloud database
- Do not store production credentials in GitHub
