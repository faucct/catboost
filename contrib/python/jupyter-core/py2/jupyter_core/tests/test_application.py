import os
import shutil
from tempfile import mkdtemp
from ipython_genutils import py3compat

try:
    from unittest.mock import patch
except ImportError:
    # py2
    from mock import patch

import pytest
from traitlets import Integer

from jupyter_core.application import JupyterApp, NoStart

pjoin = os.path.join


@pytest.fixture(autouse=True)
def patch_data_dir(monkeypatch):
    import yatest.common
    monkeypatch.setenv('JUPYTER_DATA_DIR', yatest.common.work_path())


def test_basic():
    app = JupyterApp()


def test_default_traits():
    app = JupyterApp()
    for trait_name in app.traits():
        value = getattr(app, trait_name)

class DummyApp(JupyterApp):
    name = "dummy-app"
    m = Integer(0, config=True)
    n = Integer(0, config=True)

_dummy_config = """
c.DummyApp.n = 10
"""

def test_custom_config():
    app = DummyApp()
    td = mkdtemp()
    fname = pjoin(td, 'config.py')
    with open(fname, 'w') as f:
        f.write(_dummy_config)
    app.initialize(['--config', fname])
    shutil.rmtree(td)
    assert app.config_file == fname
    assert app.n == 10

def test_cli_override():
    app = DummyApp()
    td = mkdtemp()
    fname = pjoin(td, 'config.py')
    with open(fname, 'w') as f:
        f.write(_dummy_config)
    app.initialize(['--config', fname, '--DummyApp.n=20'])
    shutil.rmtree(td)
    assert app.n == 20


def test_generate_config():
    td = mkdtemp()
    app = DummyApp(config_dir=td)
    app.initialize(['--generate-config'])
    assert app.generate_config
    
    with pytest.raises(NoStart):
        app.start()
    
    assert os.path.exists(os.path.join(td, 'dummy_app_config.py'))


def test_load_config():
    config_dir = mkdtemp()
    wd = mkdtemp()
    with open(pjoin(config_dir, 'dummy_app_config.py'), 'w') as f:
        f.write('c.DummyApp.m = 1\n')
        f.write('c.DummyApp.n = 1')
    with patch.object(py3compat, 'getcwd', lambda : wd):
        app = DummyApp(config_dir=config_dir)
        app.initialize([])

    assert app.n == 1, "Loaded config from config dir"
    
    with open(pjoin(wd, 'dummy_app_config.py'), 'w') as f:
        f.write('c.DummyApp.n = 2')

    with patch.object(py3compat, 'getcwd', lambda : wd):
        app = DummyApp(config_dir=config_dir)
        app.initialize([])

    assert app.m == 1, "Loaded config from config dir"
    assert app.n == 2, "Loaded config from CWD"
    
    shutil.rmtree(config_dir)
    shutil.rmtree(wd)


def test_load_bad_config():
    config_dir = mkdtemp()
    wd = mkdtemp()
    with open(pjoin(config_dir, 'dummy_app_config.py'), 'w') as f:
        f.write('c.DummyApp.m = "a\n') # Syntax error
    with patch.object(py3compat, 'getcwd', lambda : wd):
        with pytest.raises(SyntaxError):
            app = DummyApp(config_dir=config_dir)
            app.raise_config_file_errors=True
            app.initialize([])

    shutil.rmtree(config_dir)
    shutil.rmtree(wd)


def test_runtime_dir_changed():
    app = DummyApp()
    td = mkdtemp()
    shutil.rmtree(td)
    app.runtime_dir = td
    assert os.path.isdir(td)
    shutil.rmtree(td)
