"""Curated normalization corpus for whitespace-handling equivalence tests."""


# List of (input_string, expected_normalized_output) tuples
# These cover all whitespace canonicalization edge cases:
# - Single vs. multiple spaces
# - Tabs, CRLF, LF, mixed line endings
# - Leading/trailing whitespace
# - Unicode whitespace (NBSP)
# - Empty and multiline OCR artifacts

NORMALIZATION_CORPUS = [
    # Single and multiple spaces
    ("Alice Wonder", "Alice Wonder"),
    ("Alice   Wonder", "Alice Wonder"),
    ("Alice     Wonder", "Alice Wonder"),
    
    # Tabs
    ("Alice\tWonder", "Alice Wonder"),
    ("Alice\t\tWonder", "Alice Wonder"),
    ("Alice \t Wonder", "Alice Wonder"),
    
    # Line endings: CRLF, LF, mixed
    ("Alice\r\nWonder", "Alice Wonder"),
    ("Alice\nWonder", "Alice Wonder"),
    ("Alice\r\nBob\nCarol", "Alice Bob Carol"),
    ("Alice\n\nBob", "Alice Bob"),
    
    # Leading and trailing whitespace
    ("  Alice Wonder  ", "Alice Wonder"),
    ("\t Alice Wonder \t", "Alice Wonder"),
    ("\r\nAlice Wonder\r\n", "Alice Wonder"),
    ("   \t  Alice  \n  ", "Alice"),
    
    # Empty strings
    ("", ""),
    ("   ", ""),
    ("\t\t\n\r\n", ""),
    
    # Mixed edge cases (OCR artifacts)
    ("Page  1:\r\n  TITLE  ", "Page 1: TITLE"),
    ("Line1\nLine2\nLine3", "Line1 Line2 Line3"),
    
    # Unicode whitespace (NBSP = \xa0)
    ("Alice\xa0Wonder", "Alice Wonder"),
    ("Alice \xa0 Wonder", "Alice Wonder"),
    
    # Real OCR multiline scenarios
    ("Name:\r\nAlice\r\n\r\nAge: 30", "Name: Alice Age: 30"),
    ("Product   Code\n\n  12345", "Product Code 12345"),
    
    # Edge: single character
    ("A", "A"),
    (" A ", "A"),
    
    # Edge: repeated spaces in middle
    ("A" + " " * 10 + "B", "A B"),
]


def get_corpus():
    """Return the full normalization corpus as list of (input, expected) tuples."""
    return NORMALIZATION_CORPUS


def get_normalize_for_matching_subset():
    """Return subset of corpus applicable to OCRService.normalize_for_matching.
    
    normalize_for_matching also calls .strip(), so we expect leading/trailing
    whitespace to be removed. Return only entries where expected output
    has no leading/trailing spaces (i.e., already stripped).
    """
    return [
        (inp, exp) for inp, exp in NORMALIZATION_CORPUS
        if exp == exp.strip()  # Only entries where strip() does nothing
    ]
