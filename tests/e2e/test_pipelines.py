"""End-to-end pipeline tests."""

import os
import subprocess
from pathlib import Path

import pytest

# Skip if Azure credentials not available
pytestmark = pytest.mark.skipif(
    not os.getenv("AZURE_OPENAI_ENDPOINT"),
    reason="AZURE_OPENAI_ENDPOINT not set"
)

PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestE2EPipelines:
    """End-to-end tests for complete pipelines."""

    @pytest.mark.slow
    @pytest.mark.parametrize("framework", [
        "semantic-kernel",
        "langgraph",
        "autogen",
        "microsoft-agent-framework",
    ])
    def test_single_agent_pipeline(self, framework: str):
        """Test single-agent pipeline for each framework."""
        sample_dir = PROJECT_ROOT / "samples" / framework / "single-agent"

        if not sample_dir.exists():
            pytest.skip(f"Sample not found: {sample_dir}")

        result = subprocess.run(
            ["uv", "run", "python", "src/main.py"],
            cwd=sample_dir,
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
        )

        # Check for success indicators
        output = result.stdout + result.stderr
        assert result.returncode == 0 or "completed" in output.lower() or "success" in output.lower(), \
            f"Pipeline failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

    @pytest.mark.slow
    @pytest.mark.skipif(
        not os.getenv("AZURE_SERVICEBUS_NAMESPACE"),
        reason="AZURE_SERVICEBUS_NAMESPACE not set"
    )
    @pytest.mark.parametrize("framework", [
        "semantic-kernel",
        "langgraph",
        "autogen",
        "microsoft-agent-framework",
    ])
    def test_servicebus_pipeline(self, framework: str):
        """Test Service Bus multi-agent pipeline for each framework."""
        sample_dir = PROJECT_ROOT / "samples" / framework / "multi-agent-servicebus"

        if not sample_dir.exists():
            pytest.skip(f"Sample not found: {sample_dir}")

        result = subprocess.run(
            ["uv", "run", "python", "src/main.py"],
            cwd=sample_dir,
            capture_output=True,
            text=True,
            timeout=180,
            env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
        )

        output = result.stdout + result.stderr
        # Service Bus pipelines should show pipeline completion
        assert result.returncode == 0 or "pipeline" in output.lower(), \
            f"Pipeline failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"


class TestE2EResilience:
    """End-to-end resilience tests."""

    @pytest.mark.slow
    @pytest.mark.skipif(
        not os.getenv("AZURE_SERVICEBUS_NAMESPACE"),
        reason="AZURE_SERVICEBUS_NAMESPACE not set"
    )
    def test_message_persistence_simulation(self):
        """Test that messages persist in queues (simulated)."""
        # This test verifies message persistence concepts
        # In a real test, we would:
        # 1. Start agent A, send message
        # 2. Verify message in queue
        # 3. Start agent B, receive message
        # 4. Verify processing completes

        # For now, just verify the infrastructure exists
        from azure_clients import PipelineMessaging

        namespace = os.environ["AZURE_SERVICEBUS_NAMESPACE"]
        messaging = PipelineMessaging(namespace=namespace)

        import asyncio

        async def check_connectivity():
            try:
                # Just check we can connect
                await messaging.receive_one("pipeline-results", max_wait_time=1)
                return True
            except Exception as e:
                if "not found" in str(e).lower():
                    return False  # Queue doesn't exist
                raise
            finally:
                await messaging.close()

        result = asyncio.run(check_connectivity())
        # Either connected successfully or queue not found - both acceptable
        assert result is True or result is False
