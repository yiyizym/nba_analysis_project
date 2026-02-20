import numpy as np
import time
from ml_framework.preprocessing.preprocessor import ClippingTransformer, WinsorizationTransformer

def benchmark_clipping():
    X = np.random.randn(100000, 100)
    clipper = ClippingTransformer(std_threshold=3)
    clipper.fit(X)

    start_time = time.time()
    for _ in range(10):
        clipper.transform(X)
    end_time = time.time()

    print(f"ClippingTransformer average time: {(end_time - start_time) / 10:.4f}s")

def benchmark_winsorization():
    X = np.random.randn(100000, 100)
    winsorizer = WinsorizationTransformer()
    winsorizer.fit(X)

    start_time = time.time()
    for _ in range(10):
        winsorizer.transform(X)
    end_time = time.time()

    print(f"WinsorizationTransformer average time: {(end_time - start_time) / 10:.4f}s")

if __name__ == "__main__":
    benchmark_clipping()
    benchmark_winsorization()
