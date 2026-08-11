from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Load base model
base_model_name = "microsoft/DialoGPT-small"
tokenizer = AutoTokenizer.from_pretrained(base_model_name)
tokenizer.pad_token = tokenizer.eos_token

# Load base model for CPU inference
# Use .to("cuda") if GPU is available
model = AutoModelForCausalLM.from_pretrained(base_model_name)
model.resize_token_embeddings(len(tokenizer))

# Apply fine-tuned adapter
model = PeftModel.from_pretrained(model, "/Users/ritikchoudhary/virtual-ai-pet/backend/content/pet-chat-adapter")

def chat(user_input):
    prompt = f"User: {user_input}\nPet:"
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(
        **inputs,
        max_new_tokens=50,
        do_sample=True,
        top_p=0.9,
        temperature=0.8,
        pad_token_id=tokenizer.eos_token_id
    )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract text after "Pet:" in response
    answer = response.split("Pet:")[-1].strip()
    return answer

# Test
while True:
    msg = input("You: ")
    if msg.lower() == "quit":
        break
    print("Pet:", chat(msg))