
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


    return chunks