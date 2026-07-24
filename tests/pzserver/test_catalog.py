"""
Tests for pzserver/catalog.py
"""

import pandas as pd

from pzserver.catalog import Catalog, SpeczCatalog, TrainingSet


def make_metadata(columns):
    return {"main_file": {"columns_association": columns}}


def test_catalog_stores_data_and_displays_metadata():
    metadata_df = pd.DataFrame({"column": ["ra"], "alias": ["RA"]})
    catalog = Catalog(
        data=pd.DataFrame({"ra": [1.0]}),
        metadata=make_metadata([]),
        metadata_df=metadata_df,
    )

    assert list(catalog.data.columns) == ["ra"]
    assert catalog.metadata_df is metadata_df
    assert catalog.columns == []

    # The method is notebook-oriented; this assertion verifies it remains callable.
    catalog.display_metadata()


def test_specz_catalog_plot_saves_figure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    catalog = SpeczCatalog(
        data=pd.DataFrame(
            {
                "ra": [10.0, 20.0],
                "dec": [-2.0, -3.0],
                "z": [0.1, 0.2],
            }
        ),
        metadata=make_metadata(
            [
                {"ucd": "pos.eq.ra;meta.main", "column_name": "ra"},
                {"ucd": "pos.eq.dec;meta.main", "column_name": "dec"},
                {"ucd": "src.redshift", "column_name": "z"},
            ]
        ),
    )

    filename = catalog.plot(savefig=True)

    assert filename == "specz_catalog.png"
    assert (tmp_path / filename).is_file()


def test_specz_catalog_plot_returns_none_when_required_columns_are_missing():
    catalog = SpeczCatalog(
        data=pd.DataFrame({"ra": [10.0], "z": [0.1]}),
        metadata=make_metadata(
            [
                {"ucd": "pos.eq.ra;meta.main", "column_name": "ra"},
                {"ucd": "src.redshift", "column_name": "z"},
            ]
        ),
    )

    assert catalog.plot() is None


def test_training_set_plot_saves_redshift_figure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    catalog = TrainingSet(
        data=pd.DataFrame({"z": [0.05, 0.3, 0.8]}),
        metadata=make_metadata([{"ucd": "src.redshift", "column_name": "z"}]),
    )

    filename = catalog.plot(savefig=True)

    assert filename == "train_set.png"
    assert (tmp_path / filename).is_file()


def test_training_set_plot_supports_magnitude_panel(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    catalog = TrainingSet(
        data=pd.DataFrame({"z": [0.05, 0.3, 0.8], "mag_i": [15.5, 21.0, 31.0]}),
        metadata=make_metadata([{"ucd": "src.redshift", "column_name": "z"}]),
    )

    filename = catalog.plot(mag_name="mag_i", savefig=True)

    assert filename == "train_set.png"
    assert (tmp_path / filename).is_file()


def test_training_set_plot_returns_none_without_redshift_column():
    catalog = TrainingSet(
        data=pd.DataFrame({"mag_i": [21.0]}),
        metadata=make_metadata([{"ucd": "phot.mag", "column_name": "mag_i"}]),
    )

    assert catalog.plot() is None
