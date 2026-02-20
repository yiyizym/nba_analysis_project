import numpy as np
import pytest
from ml_framework.preprocessing.preprocessor import WinsorizationTransformer, ClippingTransformer

def test_winsorization_transformer():
    X = np.array([
        [1, 10],
        [2, 20],
        [3, 30],
        [4, 40],
        [5, 50],
        [6, 60],
        [7, 70],
        [8, 80],
        [9, 90],
        [10, 100]
    ], dtype=float)

    # Percentiles: 10% and 90%
    # Col 1: [1..10], 10th=1.9, 90th=9.1
    # Col 2: [10..100], 10th=19, 90th=91
    transformer = WinsorizationTransformer(lower=0.1, upper=0.9)
    transformer.fit(X)

    X_transformed = transformer.transform(X)

    # Check shape
    assert X_transformed.shape == X.shape

    # Check values are clipped
    assert np.all(X_transformed[0] >= transformer.lower_bounds_)
    assert np.all(X_transformed[-1] <= transformer.upper_bounds_)

    # Explicit check for some values
    # Col 1: 1 -> 1.9, 10 -> 9.1
    # Col 2: 10 -> 19, 100 -> 91
    assert np.allclose(X_transformed[0], [1.9, 19.0])
    assert np.allclose(X_transformed[-1], [9.1, 91.0])
    assert np.allclose(X_transformed[5], [6.0, 60.0]) # Middle value should be unchanged

def test_clipping_transformer():
    X = np.array([
        [1, 100],
        [1.1, 110],
        [0.9, 90],
        [10, 1000] # Outlier
    ], dtype=float)

    transformer = ClippingTransformer(std_threshold=1)
    transformer.fit(X)

    # Means: [3.25, 325]
    # Stds: [3.899, 389.9]
    # Lower bounds: [3.25 - 3.899, 325 - 389.9] = [-0.649, -64.9]
    # Upper bounds: [3.25 + 3.899, 325 + 389.9] = [7.149, 714.9]

    X_transformed = transformer.transform(X)

    # Outlier (10, 1000) should be clipped to (7.149, 714.9)
    assert np.allclose(X_transformed[3], [7.149, 714.9], atol=1e-3)
    # Others should be unchanged
    assert np.allclose(X_transformed[0], [1, 100])

def test_single_column():
    X = np.array([[1], [2], [10]], dtype=float)
    transformer = ClippingTransformer(std_threshold=1)
    transformer.fit(X)
    X_transformed = transformer.transform(X)
    assert X_transformed.shape == (3, 1)

if __name__ == "__main__":
    # If run manually and numpy is available
    try:
        test_winsorization_transformer()
        test_clipping_transformer()
        test_single_column()
        print("All tests passed!")
    except Exception as e:
        print(f"Tests failed or could not run: {e}")
