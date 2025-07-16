import os
import sys
from datetime import datetime
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

if sys.platform == "win32":
    os.system('chcp 65001 > nul')

ascii_logo = r"""
  __  __ _           _ _____                   
 |  \/  (_)_ __   __| |_   _| __ __ _  ___ ___ 
 | |\/| | | '_ \ / _` | | || '__/ _` |/ __/ _ \
 | |  | | | | | | (_| | | || | | (_| | (_|  __/
 |_|  |_|_|_| |_|\__,_| |_||_|  \__,_|\___\___|
                                              
               MindTrace :: Own Your Mind
"""

# Load DialoGPT model and tokenizer once
model_name = "microsoft/DialoGPT-medium"
print("Loading AI model, please wait...")
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token  # Fix padding error
model = AutoModelForCausalLM.from_pretrained(model_name)
print("Model loaded!")

def generate_ai_response(text, chat_history_ids=None):
    encoded_dict = tokenizer(
        text + tokenizer.eos_token,
        return_tensors='pt',
        padding=True,
        truncation=True
    )
    new_input_ids = encoded_dict['input_ids']
    attention_mask = encoded_dict['attention_mask']

    if chat_history_ids is not None:
        input_ids = torch.cat([chat_history_ids, new_input_ids], dim=-1)
        chat_history_mask = torch.ones(chat_history_ids.shape, dtype=torch.long)
        attention_mask = torch.cat([chat_history_mask, attention_mask], dim=-1)
    else:
        input_ids = new_input_ids

    chat_history_ids = model.generate(
        input_ids,
        attention_mask=attention_mask,
        max_length=1000,
        pad_token_id=tokenizer.eos_token_id,
        do_sample=True,
        top_k=50,
        top_p=0.95,
        temperature=0.7,
        no_repeat_ngram_size=2,
    )

    response = tokenizer.decode(chat_history_ids[:, input_ids.shape[-1]:][0], skip_special_tokens=True)
    return response, chat_history_ids


def load_today_journal(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.read().strip().split("\n")
    return lines

def save_journal(filename, lines):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

def main():
    print(ascii_logo)

    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"journal/{today}.md"
    os.makedirs("journal", exist_ok=True)

    print(f"\n🧠 Journal for {today}")
    choice = ""
    while choice not in ["N", "E"]:
        choice = input("New entry or Edit today's journal? (N/E): ").strip().upper()

    if choice == "E":
        lines = load_today_journal(filename)
        if not lines:
            print("No entries found for today. Starting new journal.")
            lines = []
        else:
            print("Current journal entries:")
            for idx, line in enumerate(lines, 1):
                print(f"{idx}: {line}")
            print("\nAdd new lines below. Press ENTER twice to finish.\n")
    else:
        lines = []
        print("Write your journal entry. Press ENTER twice to finish.\n")

    new_lines = []
    while True:
        try:
            line = input("> ")
            if line == "":
                break
            new_lines.append(line)
        except KeyboardInterrupt:
            break

    all_lines = lines + new_lines
    save_journal(filename, all_lines)

    print(f"\n✅ Saved to {filename}")

    entry_text = "\n".join(all_lines)

    # Generate AI response to the journal entry
    response, _ = generate_ai_response(entry_text)
    print(f"\n🤖 MindTrace AI: {response}")

if __name__ == "__main__":
    main()
