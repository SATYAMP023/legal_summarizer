# src/inference/summarize.py

import streamlit as st
import torch
from transformers import LEDTokenizer, LEDForConditionalGeneration
import os

MODEL_PATH = "satyamp555/legal-led-summarizer"

MAX_INPUT_TOKENS  = 1024
MAX_OUTPUT_TOKENS = 256

@st.cache_resource(show_spinner="Loading AI model...")
def load_model():
    token = os.environ.get("HF_TOKEN", None)
    tokenizer = LEDTokenizer.from_pretrained(
        "satyamp555/legal-led-summarizer",
        token=token
    )
    model = LEDForConditionalGeneration.from_pretrained(
        "satyamp555/legal-led-summarizer",
        token=token
    )
    device = torch.device("cpu")
    model.to(device)
    model.eval()
    return tokenizer, model


def summarize_chunk(text: str, tokenizer, model, device) -> str:
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
    tokenizer, model = load_model()
    device = next(model.parameters()).device

    tokens = tokenizer.encode(text)
    if len(tokens) <= MAX_INPUT_TOKENS:
        return summarize_chunk(text, tokenizer, model, device)

    # Chunk long documents
    words = text.split()
    chunk_word_size = 600
    overlap = 50
    chunks = []
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i: i + chunk_word_size]))
        i += chunk_word_size - overlap

    chunk_summaries = [summarize_chunk(c, tokenizer, model, device) for c in chunks]

    if len(chunk_summaries) == 1:
        return chunk_summaries[0]

    return summarize_chunk(" ".join(chunk_summaries), tokenizer, model, device)