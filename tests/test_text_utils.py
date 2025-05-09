import pytest
from toolkitx.text_utils import truncate_text_smart, split_text_by_word_count


# 基本测试用例
def test_empty_string():
    assert truncate_text_smart("", 10) == ""
    assert truncate_text_smart("", 10, mode="word") == ""


def test_text_shorter_than_limit():
    text = "hello"
    assert truncate_text_smart(text, 10) == text
    assert truncate_text_smart(text, 10, mode="word") == text
    assert truncate_text_smart(text, 5) == text  # 等于长度
    assert truncate_text_smart(text, 5, mode="word") == text


# 'char' 模式测试
def test_char_mode_basic_truncation():
    text = "hello world"
    assert (
        truncate_text_smart(text, 8, mode="char", suffix="...") == "hello..."
    )  # 8 - 3 = 5 -> "hello" + "..."
    assert (
        truncate_text_smart(text, 5, mode="char", suffix="...") == "hello..."
    )  # 5 - 3 = 2 -> "he" + "..."
    assert (
        truncate_text_smart(text, 12, mode="char", suffix="") == "hello world"
    )  # 5 - 3 = 2 -> "he" + "..."

    assert (
        truncate_text_smart(text, 2, mode="char", suffix="") == "hello"
    )  # 5 - 3 = 2 -> "he" + "..."

def test_char_mode_custom_suffix():
    text = "hello world"
    assert (
        truncate_text_smart(text, 8, mode="char", suffix="--") == "hello--"
    )  # 8 - 2 = 6 -> "hello " + "--"


# 'word' 模式测试
def test_word_mode_basic_truncation():
    text = "This is a very long sentence."
    assert (
        truncate_text_smart(text, 10, mode="word", suffix="...") == "This is a very long sentence."
    )  # "This is a" (len 9) + "..."
    assert (
        truncate_text_smart(text, 3, mode="word", suffix="...", tolerance=1) == "This is a..."
    )  # "This is a very" (len 14) + "..."
    assert (
        truncate_text_smart(text, 3, mode="word", suffix="...", tolerance=5) == "This is a very long sentence."
    )  #

def test_word_mode_no_truncation_needed():
    text = "Short text."
    assert truncate_text_smart(text, 20, mode="word", suffix="...") == "Short text."


def test_word_mode_limit_allows_one_word():
    text = "Firstword second"
    assert (
        truncate_text_smart(text, 9, mode="word", suffix="...") == "Firstword second"
    )

# 错误处理测试
def test_invalid_mode():
    with pytest.raises(ValueError, match="mode must be 'char' or 'word'"):
        truncate_text_smart("text", 10, mode="invalid")


def test_split_empty_text():
    assert split_text_by_word_count("", max_words=10, overlap=2) == []

def test_split_text_shorter_than_max_words():
    text = "This is a short text." # 5 words
    expected = ["This is a short text."]
    assert split_text_by_word_count(text, max_words=10, overlap=2) == expected

def test_split_no_overlap():
    text = "one two three four five six seven eight nine ten" # 10 words
    expected = ["one two three four five", "six seven eight nine ten"]
    assert split_text_by_word_count(text, max_words=5, overlap=0) == expected

def test_split_with_overlap():
    text = "one two three four five six seven eight nine ten" # 10 words
    # max_words=5, overlap=2. step = 5-2 = 3
    # 1. words[0:5] -> "one two three four five"
    # 2. words[3:3+5] -> words[3:8] -> "four five six seven eight"
    # 3. words[6:6+5] -> words[6:11] -> "seven eight nine ten" (actual: "seven eight nine ten")
    expected = [
        "one two three four five",
        "four five six seven eight",
        "seven eight nine ten"
    ]
    assert split_text_by_word_count(text, max_words=5, overlap=2) == expected

def test_split_exact_multiple_with_overlap():
    text = "a b c d e f g h i" # 9 words
    # max_words=5, overlap=2. step = 3
    # 1. words[0:5] -> "a b c d e"
    # 2. words[3:8] -> "d e f g h"
    # 3. words[6:11] -> "g h i" (actual: "g h i")
    expected = ["a b c d e", "d e f g h", "g h i"]
    assert split_text_by_word_count(text, max_words=5, overlap=2) == expected

def test_split_not_exact_multiple_with_overlap():
    text = "a b c d e f g h i j" # 10 words
    # max_words=4, overlap=1. step = 3
    # 1. words[0:4] -> "a b c d"
    # 2. words[3:7] -> "d e f g"
    # 3. words[6:10] -> "g h i j"
    # 4. words[9:13] -> "j" (actual: "j")
    expected = ["a b c d", "d e f g", "g h i j",]
    assert split_text_by_word_count(text, max_words=4, overlap=1) == expected

def test_split_overlap_zero():
    text = "one two three four five six" # 6 words
    # max_words=3, overlap=0. step = 3
    # 1. words[0:3] -> "one two three"
    # 2. words[3:6] -> "four five six"
    expected = ["one two three", "four five six"]
    assert split_text_by_word_count(text, max_words=3, overlap=0) == expected

def test_split_max_overlap():
    text = "one two three four five six" # 6 words
    # max_words=3, overlap=2. step = 1
    # 1. words[0:3] -> "one two three"
    # 2. words[1:4] -> "two three four"
    # 3. words[2:5] -> "three four five"
    # 4. words[3:6] -> "four five six"
    # 5. words[4:7] -> "five six" (actual: "five six")
    # 6. words[5:8] -> "six" (actual: "six")
    expected = [
        "one two three",
        "two three four",
        "three four five",
        "four five six",
    ]
    assert split_text_by_word_count(text, max_words=3, overlap=2) == expected

def test_split_max_words_one_no_overlap():
    text = "a b c"
    expected = ["a", "b", "c"]
    assert split_text_by_word_count(text, max_words=1, overlap=0) == expected

def test_split_max_words_one_with_overlap_invalid_assert():
    # overlap must be < max_words. So overlap=0 is the only valid case if max_words=1
    text = "a b c"
    with pytest.raises(AssertionError, match="Overlap must be >= 0 and less than max_words"):
        split_text_by_word_count(text, max_words=1, overlap=1)

def test_split_invalid_overlap_too_large():
    text = "one two three four"
    with pytest.raises(AssertionError, match="Overlap must be >= 0 and less than max_words"):
        split_text_by_word_count(text, max_words=3, overlap=3)
    with pytest.raises(AssertionError, match="Overlap must be >= 0 and less than max_words"):
        split_text_by_word_count(text, max_words=3, overlap=4)

def test_split_invalid_overlap_negative():
    text = "one two three four"
    with pytest.raises(AssertionError, match="Overlap must be >= 0 and less than max_words"):
        split_text_by_word_count(text, max_words=3, overlap=-1)

def test_split_long_text_performance_check():
    # This is a basic check, not a rigorous performance test
    words = ["word"] * 1000
    text = " ".join(words)
    chunks = split_text_by_word_count(text, max_words=100, overlap=10)
    assert len(chunks) > 0
    assert " ".join(words[:100]) == chunks[0]
    # step = 100 - 10 = 90. Expected chunks approx 1000/90 ~ 11.11 -> 12 chunks
    # (1000 - 100) / 90 + 1 = 900 / 90 + 1 = 10 + 1 = 11.
    # More precisely: ceil( (len(words) - max_words) / step ) + 1 if len(words) > max_words else 1
    # If len(words) = 1000, max_words = 100, overlap = 10, step = 90
    # First chunk: words[0:100]
    # Second chunk: words[90:190]
    # ...
    # Last full step chunk starts at i where i + max_words < len(words)
    # (len(words) - max_words) / step = (1000-100)/90 = 900/90 = 10. So 10 steps after the first. Total 11 chunks.
    # The loop runs for i = 0, 90, 180, ..., 900.
    # i=900: words[900:1000]
    # Next i=990: words[990:1090], actual words[990:1000] -> "word ... word" (10 words)
    # The loop condition is `if i + max_words >= len(words): break`
    # When i = 900, 900 + 100 = 1000. This chunk is added. Loop breaks.
    # So, 11 chunks.
    # 0, 90, 180, 270, 360, 450, 540, 630, 720, 810, 900. These are 11 start indices.
    assert len(chunks) == 11


def test_split_text_with_extra_spaces():
    text = "word1  word2   word3    word4" # split() handles multiple spaces
    # words = ["word1", "word2", "word3", "word4"]
    expected = ["word1 word2", "word3 word4"]
    assert split_text_by_word_count(text, max_words=2, overlap=0) == expected

    text_overlap = "word1  word2   word3    word4 word5"
    # words = ["word1", "word2", "word3", "word4", "word5"]
    # max_words=3, overlap=1. step = 2
    # 1. words[0:3] -> "word1 word2 word3"
    # 2. words[2:5] -> "word3 word4 word5"
    # 3. words[4:7] -> "word5"
    expected_overlap = ["word1 word2 word3", "word3 word4 word5",]
    assert split_text_by_word_count(text_overlap, max_words=3, overlap=1) == expected_overlap
