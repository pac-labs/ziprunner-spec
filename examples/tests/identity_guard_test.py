"""Illustrative test fixture for the *example* verification plan.

Not connected to any real ZipRunner instance or project identity checker.
A real producer MUST package real implementation tests instead of this fixture.
"""

def example_identity_guard(package_project, configured_project):
    return package_project == configured_project


def test_mismatched_project_is_rejected():
    assert not example_identity_guard('other-project', 'example-project')


def test_matching_project_is_accepted():
    assert example_identity_guard('example-project', 'example-project')
