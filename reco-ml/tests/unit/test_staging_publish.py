from unittest.mock import Mock
from pathlib import Path

import pytest

from reco_ml.staging_publish import publish_snapshot


@pytest.mark.parametrize('coverage', [-1, 1.1, float('nan'), float('inf')])
def test_invalid_threshold_does_not_touch_database(coverage):
    conn = Mock()
    with pytest.raises(ValueError, match='min_coverage'):
        publish_snapshot(conn, 'unused', Path('unused'), min_coverage=coverage)
    conn.execute.assert_not_called()
