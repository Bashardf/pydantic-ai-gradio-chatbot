import os

# Muss vor app-Import gesetzt werden
os.environ.setdefault("SKIP_CONFIG_VALIDATION", "1")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake-not-real-key12345")
