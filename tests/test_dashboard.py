from pathlib import Path
from streamlit.testing.v1 import AppTest

def test_dashboard_default_and_empty_filters():
 app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'dashboard/app.py')).run(timeout=90)
 assert not app.exception
 app.sidebar.multiselect[0].set_value([]).run()
 assert not app.exception
 assert any('No players' in w.value for w in app.warning)
