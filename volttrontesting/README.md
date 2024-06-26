# VOLTTRON Testing
Testing VOLTTRON requires the inclusion of several packages.

Execute the following from a volttron activated console.

```
pip install pytest pytest-bdd pytest-cov
```

## Executing tests
When executing tests the current directory should be at the root of
the VOLTTRON repository.

```
# Execute all tests throughout the repository
pytest

# Execute a specific directory of tests recursively from the
# specified directory.
pytest examples/ListenerAgent

# Execute only tests that are marked as slow
pytest -m slow

# Execute tests that are not marked as slow
pytest -m "not slow"

# Execute only zmq tests
pytest -m zmq
```

## Notes
 * Global configuration is located in the pytest.ini file at the root of the
 volttron repository.
 * In order for a test to pass the required dependencies for the agent
under testing must be met.
