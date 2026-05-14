<<<<<<< HEAD
# src/inference/summarize.py

import torch
import re
from transformers import LEDTokenizer, LEDForConditionalGeneration
import os

# ── Load fine-tuned LED model ─────────────────────────────────────────
MODEL_PATH = "satyamp555/legal-led-summarizer"

tokenizer = LEDTokenizer.from_pretrained(MODEL_PATH)
model = LEDForConditionalGeneration.from_pretrained(MODEL_PATH)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()

MAX_INPUT_TOKENS  = 1024
MAX_OUTPUT_TOKENS = 256


def summarize_chunk(text: str) -> str:
    inputs = tokenizer(
        text,
        return_tensors="pt",
        max_length=MAX_INPUT_TOKENS,
        truncation=True,
        padding="max_length",
    ).to(device)

    global_attention_mask = torch.zeros_like(inputs["input_ids"])
    global_attention_mask[:, 0] = 1

    with torch.no_grad():
        summary_ids = model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            global_attention_mask=global_attention_mask,
            max_new_tokens=MAX_OUTPUT_TOKENS,
            num_beams=4,
            length_penalty=2.0,
            early_stopping=True,
            no_repeat_ngram_size=3,
        )
    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)


def summarize_long(text: str) -> str:
    """Chunk-based summarization for long legal documents."""
    tokens = tokenizer.encode(text)

    if len(tokens) <= MAX_INPUT_TOKENS:
        return summarize_chunk(text)

    words = text.split()
    chunk_word_size = 600
    overlap = 50
    chunks = []

    i = 0
    while i < len(words):
        chunk = " ".join(words[i: i + chunk_word_size])
        chunks.append(chunk)
        i += chunk_word_size - overlap

    chunk_summaries = [summarize_chunk(c) for c in chunks]

    if len(chunk_summaries) == 1:
        return chunk_summaries[0]

    combined = " ".join(chunk_summaries)
    return summarize_chunk(combined)
=======
import torch
from transformers import LEDTokenizer, LEDForConditionalGeneration
from src.preprocessing.chunker import split_into_chunks


# =========================
# Model Loading
# =========================

MODEL_PATH = "legal_led_model"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Using device:", device)

tokenizer = LEDTokenizer.from_pretrained(MODEL_PATH)

model = LEDForConditionalGeneration.from_pretrained(MODEL_PATH)
model = model.to(device)

model.eval()


# =========================
# Single Chunk Summary
# =========================

def generate_summary(text,
                     max_input_tokens=4096,
                     max_output_tokens=800,
                     min_output_tokens=300):

    inputs = tokenizer(
        text,
        return_tensors="pt",
        max_length=max_input_tokens,
        truncation=True,
    )

    input_ids = inputs["input_ids"].to(device)
    attention_mask = inputs["attention_mask"].to(device)

    # 🔥 Required for LED
    global_attention_mask = torch.zeros_like(input_ids)
    global_attention_mask[:, 0] = 1

    try:
        with torch.no_grad():
            output = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                global_attention_mask=global_attention_mask,

                max_new_tokens=max_output_tokens,
                min_length=min_output_tokens,

                num_beams=4,
                length_penalty=1.3,
                no_repeat_ngram_size=3,
                early_stopping=True,
                do_sample=False
            )

        summary = tokenizer.decode(output[0], skip_special_tokens=True)

        if summary.strip() == "":
            return "Model returned empty summary."

        return summary

    except Exception as e:
        return f"Error during generation: {str(e)}"


# =========================
# Long Document Summary
# =========================

def summarize_long(text):

    # Split into chunks safely
    chunks = split_into_chunks(text, tokenizer, max_tokens=3500)

    print(f"Total chunks: {len(chunks)}")

    chunk_summaries = []

    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}")

        summary_part = generate_summary(
            chunk,
            max_input_tokens=4096,
            max_output_tokens=600,
            min_output_tokens=200
        )

        chunk_summaries.append(summary_part)

    # 🔥 Hierarchical Summarization (FINAL COMPRESSION STEP)
    print("Generating final combined summary...")

    combined_text = "\n\n".join(chunk_summaries)

    final_summary = generate_summary(
        combined_text,
        max_input_tokens=4096,
        max_output_tokens=1000,
        min_output_tokens=400
    )

    return final_summary
>>>>>>> 273dcd41279759bf77f4e5d4c52464f035c48e21
