import numpy as np
from sklearn.decomposition import PCA
from sklearn.covariance import MinCovDet


class fiber_orientation:
    def __init__(self, name: str, node_list: np.ndarray) -> None:
        self.name = name
        self.node_list = node_list
        self.mean_vector = np.mean(node_list, axis=0)
        self.centered_nodes = node_list - self.mean_vector
        self.eigenvector: np.ndarray
        self.eigenvalues: np.ndarray
        self.eigenvector, self.eigenvalues = self.nodes_PCA()

        self.max_axis = np.argmax(self.eigenvalues)

        self.rectangle_system = self.rectangle()

        # print(self.rectangle_system)

    def nodes_PCA(self):
        # Robust covariance estimation
        robust_cov = MinCovDet().fit(self.centered_nodes)
        # Use regularized PCA
        pca = PCA(n_components=3, svd_solver="full")
        pca.fit(robust_cov.covariance_)
        return pca.components_, pca.explained_variance_

    def rectangle(self) -> np.ndarray:

        vectors_new_basis = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])

        vectors_original_basis: list[list[np.float64]] = []
        for vector in vectors_new_basis:
            vectors_original_basis.append(np.linalg.solve(self.eigenvector, vector))

        coordinates_rect_sys = [vectors_original_basis[self.max_axis]]

        del vectors_original_basis[self.max_axis]
        coordinates_rect_sys.append(vectors_original_basis[0])
        return np.array(coordinates_rect_sys)


if __name__ == "__main__":
    pass
