import numpy as np
# credits and installation https://github.com/njchiang/tikhonov.git
from sklearn.linear_model import LinearRegression
from tikhonov.TikhonovRegression import Tikhonov

class TikhonovRegularization(object):

    def _get_filter_matrices(self, timesteps):
        integral_matrix = np.tri(timesteps,timesteps,0)
        derivative_matrix = np.eye(timesteps,timesteps)-(np.tri(timesteps,timesteps,-1)-np.tri(timesteps,timesteps,-2))
        second_derivative_matrix = np.dot(derivative_matrix, derivative_matrix)
        return integral_matrix, second_derivative_matrix 

    def _get_exact_tikhonov_matrix(self):
        X = self._integral_matrix
        G = self._gamma_matrix

        return np.dot(
            np.linalg.inv(
                np.dot(X.T, X) + np.dot(self.alpha * G.T, self.alpha * G)
            ), 
            X.T
        )

    def __init__(self, timesteps, alpha):
        self.timesteps = timesteps
        self.alpha = alpha
        self._integral_matrix, self._gamma_matrix = self._get_filter_matrices(timesteps)
        self._exact_tikhonov_matrix = self._get_exact_tikhonov_matrix()


    def stat_smooth_data(self, y, alpha, verbose=True):
        tic = Tikhonov(alpha=self.alpha)
        tic.fit(y=y, X=self._integral_matrix, L=self._gamma_matrix)
        if verbose:
            print('TIC R2: {}'.format(tic.score(X=self._integral_matrix, y=y)))
        
        return tic.predict(self._integral_matrix)

    def stat_smooth_differentiate(self, y, verbose=True):
        tic = Tikhonov(alpha=self.alpha)
        tic.fit(y=y, X=self._integral_matrix, L=self._gamma_matrix)
        if verbose:
            print('TIC R2: {}'.format(tic.score(X=self._integral_matrix, y=y)))
        
        return tic.coef_


    def exact_smooth_data(self, y):
        return np.dot(self._exact_tikhonov_matrix, y)