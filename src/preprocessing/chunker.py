<<<<<<< HEAD
def split_into_chunks(text, tokenizer, max_tokens=14000):
    """
    Splits long text into token-based chunks
    compatible with LED model.
    """

    tokens = tokenizer.encode(text)

    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i:i + max_tokens]
        chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
        chunks.append(chunk_text)

=======
def split_into_chunks(text, tokenizer, max_tokens=14000):
    """
    Splits long text into token-based chunks
    compatible with LED model.
    """

    tokens = tokenizer.encode(text)

    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i:i + max_tokens]
        chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
        chunks.append(chunk_text)

>>>>>>> 273dcd41279759bf77f4e5d4c52464f035c48e21
    return chunks