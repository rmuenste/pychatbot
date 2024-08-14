import time

import openai

# Replace with your OpenAI API key
openai.api_key = 'your-api-key-here'

# Upload the dataset
file_response = openai.File.create(
  file=open("customer_faq.jsonl", "rb"),
  purpose='fine-tune'
)
file_id = file_response['id']
print(f"File ID: {file_id}")

# Fine-tune the model
fine_tune_response = openai.FineTune.create(
    training_file=file_id,
    model="davinci",
    n_epochs=4,
    batch_size=2
)
fine_tune_id = fine_tune_response['id']
print(f"Fine-tune ID: {fine_tune_id}")

# Monitor the fine-tuning process
while True:
    status = openai.FineTune.retrieve(fine_tune_id)
    status_phase = status['status']
    print(f"Status: {status_phase}")
    
    if status_phase == 'succeeded':
        fine_tuned_model = status['fine_tuned_model']
        print(f"Fine-tuned model: {fine_tuned_model}")
        break
    elif status_phase == 'failed':
        raise Exception("Fine-tuning failed")
    
    time.sleep(60)

# Test the fine-tuned model
response = openai.Completion.create(
  model=fine_tuned_model,
  prompt="What is your return policy?",
  max_tokens=50
)

print(response.choices[0].text.strip())
