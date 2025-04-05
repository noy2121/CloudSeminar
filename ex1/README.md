# AI Chatbot with AWS Lambda, DynamoDB, and Amplify

This project is a serverless web-based chatbot powered by OpenAI. It uses:
- **AWS Lambda** to handle requests and call the OpenAI API.
- **DynamoDB** to store and retrieve chat history per user.
- **AWS Amplify** to host the frontend (chat UI).

---

## 🔗 URLs

- **Lambda Function URL**  
  `https://qoan3kd6cgzx7j2byxmyeuevgm0rukdq.lambda-url.us-east-1.on.aws/`

- **Amplify Live URL**  
  `https://main.d25b691m10new6.amplifyapp.com/chat.html`

---

## 🗃️ DynamoDB Table: `chat-history`

This table is used to store (maximum 6) user conversations and support context-aware replies.

### Table Schema:
- **Partition key**: `user_id` (String)  
- **Sort key**: `timestamp` (Number)

### Stored attributes per message:
- `user_id` (partition key) – Unique ID for the user/session.
- `timestamp` (sort key) – Milliseconds since epoch; used to sort messages.
- `role` – Either `"user"` or `"assistant"`.
- `content` – The actual message text.