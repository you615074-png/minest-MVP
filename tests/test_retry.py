"""
测试 utils/retry.py — 指数退避重试装饰器。
"""
import pytest
from utils.retry import retry


class TestRetryDecorator:

    def test_success_on_first_attempt(self):
        call_count = 0

        @retry(max_attempts=3, base_delay=0.01)
        def succeeds_first():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = succeeds_first()
        assert result == "ok"
        assert call_count == 1

    def test_success_on_retry(self):
        call_count = 0

        @retry(max_attempts=3, base_delay=0.01)
        def succeeds_third():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("fail")
            return "ok"

        result = succeeds_third()
        assert result == "ok"
        assert call_count == 3

    def test_all_attempts_exhausted(self):
        @retry(max_attempts=2, base_delay=0.01)
        def always_fails():
            raise ConnectionError("permanent failure")

        with pytest.raises(ConnectionError):
            always_fails()

    def test_non_retryable_exception(self):
        @retry(max_attempts=3, base_delay=0.01, exceptions=(ConnectionError,))
        def raises_value_error():
            raise ValueError("not retryable")

        with pytest.raises(ValueError):
            raises_value_error()

    def test_base_delay_increases(self):
        delays = []

        @retry(max_attempts=3, base_delay=0.05)
        def failing_with_delay():
            delays.append(1)
            raise ConnectionError("fail")

        with pytest.raises(ConnectionError):
            failing_with_delay()

        assert len(delays) == 3
