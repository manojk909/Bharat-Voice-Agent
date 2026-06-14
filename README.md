# Bharat_Voice_Agent
Bharat-Voice-Agent India's voice operating system for public services—discover, understand, and apply for schemes, scholarships, and opportunities through conversation.

## 🚀 n8n Form Filling Automation Integration

To automate step-by-step form filling on official government portals (handling navigation, user profile entry, and portal workflow orchestration), you can import the custom n8n workflow defined in the project:

### How to Onboard the n8n Workflow:
1. Open your **n8n Editor Console** (`http://localhost:5678`).
2. Click on the **Menu (Top Right)** -> **Import from File**.
3. Select [n8n_workflow.json](file:///D:/college/sem-5/Bharat_Voice_Agent/n8n_workflow.json) from the project root directory.
4. **Configure Webhook**:
   * The Webhook trigger node is configured to listen at `/webhook/draft-application`. Ensure your n8n active webhook URL matches `settings.N8N_WEBHOOK_URL` in `backend/app/core/config.py`.
5. **Puppeteer Node (Browser Automation)**:
   * The Code node utilizes `puppeteer` to spin up a browser, navigate to the official portal `source_url`, trigger caseworker login alerts (to handle CAPTCHA/OTP entries manually if needed), and auto-fill details step-by-step using the received `user_profile` payload.
6. Click **Active** to activate the workflow. Now, clicking "Draft Application" in the Voice Caseworker Assistant UI will route the workflow directly through n8n!
