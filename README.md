# SMS Horse Tips

## Quickstart

```
python -m venv .horse-tips
pip install -r requirements.txt
cp .env.template .env
docker compose -d up
flask db upgrade
flask run
```