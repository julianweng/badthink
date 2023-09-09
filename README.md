# badthink

AI-powered Slack integration to automate workplace morale best(worst)-practices and align employee incentives.

To run, use:

```
uvicorn app:api --reload
ngrok http --domain subtle-pigeon-newly.ngrok-free.app 8000 (replace with your domain)
```

Environment variables to set in ``.env``:

* `OPENAI_API_KEY`
* ```
  CAPITAL_ONE_API_KEY
  ```
* ```
  SLACK_BOT_TOKEN
  ```
* ```
  SLACKSIGNINGSECRET
  ```
