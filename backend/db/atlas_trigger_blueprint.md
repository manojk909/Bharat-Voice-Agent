# MongoDB Atlas Trigger & Function Blueprint

This blueprint describes how to configure the native MongoDB Atlas Triggers to fire an event to your n8n webhook when a user profile becomes "Eligible" after vector search validation.

## 1. Setup Atlas Function
Navigate to **Atlas App Services** -> **Functions** and create a new function called `notify_n8n_on_eligibility`.

**Code:**
```javascript
exports = async function(changeEvent) {
  // Only proceed if the operation is an update
  if (changeEvent.operationType !== "update") {
    return;
  }
  
  const fullDocument = changeEvent.fullDocument;
  
  // Verify the status changed to 'eligible'
  if (fullDocument && fullDocument.status === "eligible") {
    console.log(`Profile ${fullDocument._id} is eligible. Notifying n8n...`);
    
    // N8N Webhook URL (Ensure this is stored in Atlas App Services Secrets if preferred)
    const n8nWebhookUrl = context.values.get("N8N_WEBHOOK_URL");
    
    const payload = {
        userId: fullDocument._id.toString(),
        name: fullDocument.name,
        occupation: fullDocument.occupation,
        eligible_schemes: fullDocument.eligible_schemes,
        document_urls: fullDocument.document_urls
    };
    
    try {
      const response = await context.http.post({
        url: n8nWebhookUrl,
        body: JSON.stringify(payload),
        headers: { "Content-Type": ["application/json"] }
      });
      console.log("n8n notified successfully", response.statusCode);
    } catch(err) {
      console.error("Error notifying n8n", err);
    }
  }
};
```

## 2. Setup Atlas Trigger
Navigate to **Atlas App Services** -> **Triggers** and create a Database Trigger.

- **Trigger Type:** Database
- **Name:** `onProfileEligible`
- **Cluster:** `Cluster0` (or your cluster name)
- **Database:** `bharat_voice_agent`
- **Collection:** `user_profiles`
- **Operation Type:** `Update`
- **Full Document:** ON
- **Match Expression:**
```json
{
  "updateDescription.updatedFields.status": "eligible"
}
```
- **Event Type:** Function
- **Function:** Select `notify_n8n_on_eligibility`
