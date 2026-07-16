from google import genai

client = genai.Client(
    vertexai=True,
    project="cs-sail-2b08",
    location="us-central1",
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Reply with exactly the word: working",
)
print(response.text)