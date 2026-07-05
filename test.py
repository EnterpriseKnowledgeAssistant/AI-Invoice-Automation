from google import genai

client = genai.Client(api_key="AQ.Ab8RN6JmKpm5qXZ8q5krcz9b3hESU6ijmbo6AJ2vSQUkWmfaEQ")

response = client.models.generate_content(
    model="gemini-1.5-flash",
    contents="Say hello"
)

print(response.text)