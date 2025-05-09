import re


# Define sentence terminators as a tuple for easy checking
SENTENCE_TERMINATORS = ('.', '!', '?')

def truncate_text_smart(text: str, limit: int = 100, mode: str = "char", suffix: str = "...",  tolerance: int = 10) -> str:
    """
    Smartly truncates text based on character or word limit, with tolerance.

    :param text: The original string.
    :param limit: The target truncation length (in characters or words).
    :param mode: Truncation mode: 'char' for character-based, 'word' for word-based.
    :param suffix: The suffix to append after truncation.
    :param tolerance: The allowed deviation from the limit for smart truncation.
    :return: The truncated string.
    :raises ValueError: If the mode is not 'char' or 'word'.
    """
    if not isinstance(text, str):
        # Or handle non-string input differently, e.g., convert to string or raise TypeError
        return str(text) # Basic handling for non-string input

    if mode == 'char':
        # If text is already within or at the limit, no truncation needed.
        if len(text) <= limit:
            return text

        # If the limit is too small to even hold the suffix,
        # return the suffix truncated to the limit.
        if limit <= len(suffix):
            return suffix[:limit] if limit > 0 else ""

        # Ideal length of the text part before the suffix.
        ideal_text_part_len = limit - len(suffix)
        # Maximum length of the text part we are willing to consider (within tolerance).
        max_potential_text_len = min(len(text), limit + tolerance - len(suffix))
        # Minimum length for the text part for smart truncation (within tolerance).
        min_potential_text_len = max(0, limit - tolerance - len(suffix))
        # Ensure min_potential_text_len is not greater than max_potential_text_len.
        min_potential_text_len = min(min_potential_text_len, max_potential_text_len)

        # The chunk of text to search for smart cut points.
        # We search up to max_potential_text_len.
        candidate_chunk_for_search = text[:max_potential_text_len]

        # Attempt 1: Find a sentence boundary.
        # Search backwards for the last sentence terminator in the candidate_chunk.
        # The cut should result in a text part whose length is between min_potential_text_len and max_potential_text_len.
        best_sentence_cut_len = -1
        for i in range(len(candidate_chunk_for_search) - 1, -1, -1):
            char_at_i = candidate_chunk_for_search[i]
            # Check if it's a sentence terminator and the resulting part is long enough.
            if char_at_i in SENTENCE_TERMINATORS:
                # The length of the text part would be i + 1.
                current_cut_len = i + 1
                if current_cut_len >= min_potential_text_len:
                    # Check if it's a proper sentence end (e.g., followed by space or end of chunk)
                    # This check is simplified; more robust NLP might be needed for edge cases like "U.S.A."
                    is_actual_sentence_end = (i + 1 == len(candidate_chunk_for_search)) or \
                                             (i + 1 < len(candidate_chunk_for_search) and candidate_chunk_for_search[i+1] == ' ')
                    if is_actual_sentence_end:
                        best_sentence_cut_len = current_cut_len
                        break # Found the latest possible sentence cut within tolerance.
        
        if best_sentence_cut_len != -1:
            # .rstrip() to handle cases like "Sentence.  " before adding suffix.
            return text[:best_sentence_cut_len].rstrip() + suffix

        # Attempt 2: Find a word boundary.
        # Search backwards for the last space in the candidate_chunk.
        # The cut should result in a text part whose length is between min_potential_text_len and max_potential_text_len.
        best_word_cut_len = -1
        for i in range(len(candidate_chunk_for_search) - 1, -1, -1):
            char_at_i = candidate_chunk_for_search[i]
            if char_at_i == ' ':
                # The length of the text part would be i (cutting before the space).
                current_cut_len = i
                if current_cut_len >= min_potential_text_len:
                    best_word_cut_len = current_cut_len
                    break # Found the latest possible word cut within tolerance.

        if best_word_cut_len != -1:
            # .rstrip() just in case, though text[:best_word_cut_len] should not have trailing spaces.
            return text[:best_word_cut_len].rstrip() + suffix
            
        # Fallback: Hard truncate to the ideal_text_part_len.
        return text[:ideal_text_part_len] + suffix

    elif mode == 'word':
        words = text.split()

        # If word count is already within or at the limit, no truncation needed.
        if len(words) <= limit:
            return text

        best_word_count_for_cut = -1

        # Attempt 1: Find a sentence boundary within word tolerance.
        # Iterate from longest possible (limit + tolerance) down to shortest (limit - tolerance).
        # Ensure k is at least 1.
        start_k = min(len(words), limit + tolerance)
        end_k = max(1, limit - tolerance)

        for k in range(start_k, end_k - 1, -1):
            if k == 0: continue # Should not happen with max(1, ...)
            current_phrase_words = words[:k]
            current_phrase_str = " ".join(current_phrase_words)
            # Check if the formed phrase ends with a sentence terminator.
            if current_phrase_str.rstrip().endswith(SENTENCE_TERMINATORS):
                best_word_count_for_cut = k
                break # Found the longest suitable sentence-ending phrase.
        
        if best_word_count_for_cut != -1:
            final_words = words[:best_word_count_for_cut]
            result_text = " ".join(final_words)
            # Add suffix only if actual truncation happened relative to original word count.
            if len(words) > len(final_words):
                result_text += suffix
            return result_text

        # Fallback: Truncate to the 'limit' number of words.
        # This also handles cases where no sentence boundary was found in tolerance.
        final_words = words[:limit]
        result_text = " ".join(final_words)
        if len(words) > len(final_words): # Add suffix only if truncated
            result_text += suffix
        return result_text
    else:
        raise ValueError("mode must be 'char' or 'word'")
 
 

def split_text_by_word_count(
    text: str, max_words: int = 300, overlap: int = 0
) -> list[str]:
    """
    Split a long text into overlapping chunks (trunks), each with at most `max_words` words,
    and `overlap` words overlapping between consecutive trunks.

    Args:
        text (str): The input text.
        max_words (int): Maximum number of words per chunk.
        overlap (int): Number of overlapping words between adjacent chunks.

    Returns:
        List[str]: A list of text chunks.
    """
    assert 0 <= overlap < max_words, "Overlap must be >= 0 and less than max_words"

    words = text.split()
    trunks = []
    step = max_words - overlap

    for i in range(0, len(words), step):
        trunk = " ".join(words[i : i + max_words])
        trunks.append(trunk)
        if i + max_words >= len(words):
            break

    return trunks