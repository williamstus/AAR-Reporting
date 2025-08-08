def test_sample_dataset_fixture(sample_dataset):
    assert sample_dataset.total_soldiers == 3
    assert sample_dataset.total_records == 150
