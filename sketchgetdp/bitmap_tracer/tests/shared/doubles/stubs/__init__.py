"""
Test doubles for the complete diagram tracing system.

Provides a comprehensive set of stubs for all architectural layers, from gateways
and entities to use cases and infrastructure. Enables fully isolated unit tests
by simulating real component behavior with predictable, configurable responses.
"""
from .configuration_stubs import *
from .entity_stubs import *
from .gateway_stubs import *
from .infrastructure_stubs import *
from .service_stubs import *
from .use_case_stubs import *