from __future__ import annotations

"""Unit tests for normalization parity and regex precompile optimization.

Tests that:
1. normalize_for_matching produces identical output before/after regex precompile
2. normalize_name produces identical output before/after regex precompile
3. _RE_WHITESPACE is precompiled at module level (import-time)
4. Performance test shows no re.compile calls during batch normalization
"""

import re
import pytest
from unittest.mock import patch, MagicMock

from tests.fixtures import normalization_corpus
from src.services import ocr_service, analysis_service


class TestNormalizationParity:
    """T014: Verify normalize_for_matching equivalence across all corpus entries."""
    
    def baseline_normalize_for_matching(self, text: str) -> str:
        """Reference implementation using inline re.sub."""
        text = (text or "").replace("\n", " ").replace("\r", " ")
        return re.sub(r"\s+", " ", text).strip()
    
    @pytest.mark.parametrize("input_text,expected", normalization_corpus.NORMALIZATION_CORPUS)
    def test_normalize_for_matching_parity(self, input_text, expected):
        """T014: normalize_for_matching should match expected output for all corpus entries."""
        result = ocr_service.OCRService.normalize_for_matching(input_text)
        assert result == expected, f"Parity mismatch for input={repr(input_text)}"
        
        # Also verify against baseline
        baseline_result = self.baseline_normalize_for_matching(input_text)
        assert result == baseline_result, \
            f"Candidate differs from baseline for input={repr(input_text)}"


class TestNormalizeNameParity:
    """T015: Verify normalize_name equivalence on applicable corpus entries."""
    
    def baseline_normalize_name(self, name: str) -> str:
        """Reference implementation using inline re.sub."""
        collapsed = re.sub(r"\s+", " ", (name or "").strip())
        return collapsed.lower()
    
    @pytest.mark.parametrize("input_text,_", normalization_corpus.NORMALIZATION_CORPUS)
    def test_normalize_name_parity(self, input_text, _):
        """T015: normalize_name should match expected output for all inputs."""
        result = analysis_service.AnalysisService.normalize_name(input_text)
        baseline_result = self.baseline_normalize_name(input_text)
        
        assert result == baseline_result, \
            f"Candidate differs from baseline for input={repr(input_text)}"
        assert result == result.lower(), "Result should be lowercase"


class TestRegexPrecompile:
    """T016: Verify _RE_WHITESPACE is precompiled at module level."""
    
    def test_re_whitespace_precompiled_ocr_service(self):
        """T016: OCRService should have _RE_WHITESPACE as compiled Pattern at module level."""
        assert hasattr(ocr_service, '_RE_WHITESPACE'), \
            "ocr_service module missing _RE_WHITESPACE constant"
        
        re_whitespace = getattr(ocr_service, '_RE_WHITESPACE')
        assert isinstance(re_whitespace, re.Pattern), \
            f"_RE_WHITESPACE should be re.Pattern, got {type(re_whitespace)}"
        assert re_whitespace.pattern == r"\s+", \
            f"_RE_WHITESPACE pattern should be r'\\s+', got {re_whitespace.pattern}"
    
    def test_re_whitespace_precompiled_analysis_service(self):
        """T016: AnalysisService should have _RE_WHITESPACE as compiled Pattern at module level."""
        assert hasattr(analysis_service, '_RE_WHITESPACE'), \
            "analysis_service module missing _RE_WHITESPACE constant"
        
        re_whitespace = getattr(analysis_service, '_RE_WHITESPACE')
        assert isinstance(re_whitespace, re.Pattern), \
            f"_RE_WHITESPACE should be re.Pattern, got {type(re_whitespace)}"
        assert re_whitespace.pattern == r"\s+", \
            f"_RE_WHITESPACE pattern should be r'\\s+', got {re_whitespace.pattern}"


class TestNormalizationPerformance:
    """T017: Performance test - normalization batch with zero re.compile calls."""
    
    def test_normalization_performance_no_compile_calls(self):
        """T017: 10,000 normalize_for_matching calls should not trigger re.compile.
        
        Verifies that regex precompile optimization eliminates re.compile overhead.
        """
        test_inputs = [
            "hello  world",
            "test\n\ntext",
            "mixed  \t  spaces",
            "   leading",
            "trailing   ",
        ] * 2000  # 10,000 total
        
        compile_call_count = 0
        original_compile = re.compile
        
        def counting_compile(*args, **kwargs):
            nonlocal compile_call_count
            compile_call_count += 1
            return original_compile(*args, **kwargs)
        
        with patch('re.compile', side_effect=counting_compile):
            for text in test_inputs:
                result = ocr_service.OCRService.normalize_for_matching(text)
                assert result is not None
        
        # Should be zero compile calls (all from precompiled _RE_WHITESPACE)
        assert compile_call_count == 0, \
            f"Expected 0 re.compile calls during batch, got {compile_call_count}"
    
    def test_normalization_performance_name_no_compile_calls(self):
        """T017b: normalize_name batch should also have zero re.compile calls."""
        test_inputs = [
            "John  Doe",
            "Jane\n\nSmith",
            "Mixed  \t  Case",
        ] * 3333  # ~10,000 total
        
        compile_call_count = 0
        original_compile = re.compile
        
        def counting_compile(*args, **kwargs):
            nonlocal compile_call_count
            compile_call_count += 1
            return original_compile(*args, **kwargs)
        
        with patch('re.compile', side_effect=counting_compile):
            for name in test_inputs:
                result = analysis_service.AnalysisService.normalize_name(name)
                assert result is not None
        
        assert compile_call_count == 0, \
            f"Expected 0 re.compile calls during batch, got {compile_call_count}"
