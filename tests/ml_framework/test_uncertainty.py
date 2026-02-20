
import sys
import pytest
import warnings
import importlib

# Mock core dependencies that might be missing in the test environment
for module in ['pandas', 'matplotlib', 'matplotlib.pyplot', 'pyyaml', 'seaborn', 'plotly', 'boto3', 'botocore']:
    if module not in sys.modules:
        sys.modules[module] = type(f'Mock{module.capitalize()}', (object,), {})

def test_uncertainty_module_import_warning():
    """Test that importing ml_framework.uncertainty raises a DeprecationWarning."""
    # Ensure the module is reloaded to trigger the warning
    if 'ml_framework.uncertainty' in sys.modules:
        del sys.modules['ml_framework.uncertainty']

    with pytest.warns(DeprecationWarning, match="The ml_framework.uncertainty module is currently empty"):
        import ml_framework.uncertainty
