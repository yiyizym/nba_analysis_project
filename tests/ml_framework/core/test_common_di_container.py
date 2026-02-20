import pytest
from ml_framework.core.common_di_container import CommonDIContainer
from dependency_injector import providers

def test_common_di_container_init():
    """Test that CommonDIContainer can be instantiated and providers are accessible."""
    container = CommonDIContainer()
    assert isinstance(container.app_file_handler, providers.Singleton)
    assert isinstance(container.config, providers.Singleton)
    assert isinstance(container.app_logger, providers.Singleton)
    assert isinstance(container.error_handler_factory, providers.Singleton)
    assert isinstance(container.data_access, providers.Singleton)
    assert isinstance(container.model_registry, providers.Singleton)
    assert isinstance(container.data_validator, providers.Factory)
