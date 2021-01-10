from collections import namedtuple
from scipy import linalg, optimize
import numpy as np
import pandas as pd

class RSVDSeasonalRegularizer(object):

    def _log(self, *args):
        print(*args)

    def __init__(self, signal, season_period, max_r):
        
        self.season_period = season_period
        self.max_r = max_r

        if type(signal) == pd.Series:
            signal = signal.to_numpy()
        
        self.signal = signal[signal.shape[0]-int(signal.shape[0] / self.season_period)*self.season_period:]
        self.X = self.signal.reshape(-1, self.season_period)

        self.periods, _ = self.X.shape

        """
        roughness penalty operator:

        mat_D <- matrix(0, nrow=num_period-2,ncol=num_period)
        for (i in 1:nrow(mat_D))  mat_D[i, i:(i+2)] <- c(1,-2,1)
        mat_Omega <- t(mat_D)%*% mat_D
        """
        
        self.D2 = np.eye(N=self.periods-2,M=self.periods)+np.eye(N=self.periods-2,M=self.periods, k=2)-2*np.eye(N=self.periods-2,M=self.periods, k=1)
        self.Omega = np.dot(self.D2.T, self.D2)

        """
        work on first differences as the non seasonal component is non-stationary

        mat_Delta <- matrix(0, nrow=length(dgp_y)-1,ncol=length(dgp_y))
        for (i in 1:nrow(mat_Delta)) mat_Delta[i,i:(i+1)] <- c(-1,1)
        mat_Delta_sq <- t(mat_Delta)%*% mat_Delta
        """
        len_s = self.signal.shape[0]
        self.Delta = np.eye(N=len_s-1,M=len_s,k=1) - np.eye(N=len_s-1,M=len_s,k=0)
        self.Delta2 = np.dot(self.Delta.T, self.Delta)
        self.X_D = np.diff(self.X)

        """
        demeaning operator:

        mat_Q_n <- diag(1,num_period) - matrix(1/num_period,nrow = num_period,ncol=num_period)
        mat_Y_remain <- mat_Q_n%*%mat_Y
        """
        self.Q = np.eye(N=self.periods)-np.full(shape=(self.periods,self.periods), fill_value=1/self.periods)

    def _fit(self, X):

        """

        # R-lang original function

        func_RSVD <- function(mat_X){ 

            criter <- 999
            iter<- 0
            u_ini <- princomp(mat_X)$scores[,1]

            while (criter > 1e-3 & iter<100){
                
                v <- t(mat_X)%*%u_ini
                v <- v / sqrt(sum(v^2))
                
                gcv <-function(nu)  mean(sum(((diag(1,nrow(mat_X)) - solve(diag(1,nrow(mat_X)) + (10^nu)* mat_Omega)) %*% mat_X %*% v)^2)) / (1- mean(diag(solve(diag(1,nrow(mat_X)) + (10^nu)* mat_Omega))))^2
                re_gcv <- optim(0, gcv , method = "Brent", lower = -6, upper = 6)
                
                alpha_star <- 10^(re_gcv$par)
                u <- solve(diag(1,nrow(mat_X)) + alpha_star* mat_Omega)%*% mat_X %*% v
                criter <- mean((u-u_ini)^2)
                iter <- iter + 1
                u_ini <- u
            }
            output<-list(u_hat=as.vector(u),v_hat=as.vector(v),alpha_star=alpha_star)
        }
        """

        rows_X, cols_X = X.shape

        I = np.eye(rows_X)

        criter = 999
        iter = 0
        _,_,vh = linalg.svd(X, full_matrices=False)
        u_ini = np.dot(vh, X.T)[0,:]

        while criter > 10.**(-3) and iter < 100:
            v = np.dot(X.T, u_ini)
            v = v / np.sqrt(np.sum(v**2))

            def gcv(nu):
                M_nu = linalg.solve(I + (10.**nu) * self.Omega, I)
                #M_nu = linalg.inv(I + (10.**nu) * self.Omega)
                return (1/rows_X) * np.sum(np.dot(np.dot((I - M_nu), X), v) ** 2) / (1 - np.trace(M_nu)/rows_X) ** 2

            re_gcv = optimize.minimize_scalar(gcv, bounds=(-6,6), method='bounded')

            alpha_star = 10.**(re_gcv.x)
            u = np.dot(np.dot(linalg.inv(I + alpha_star * self.Omega), X), v)
            criter = np.mean((u-u_ini)**2)
            iter = iter + 1
            u_ini = u
        fitout = namedtuple('fitout', ['u_hat', 'v_hat', 'alpha_star'])
        return fitout(u, v, alpha_star)


    def _eval(self, u_hat, num_r):
        """
        func_EVAL <- function(mat_u_hat1){
            
            mat_Z <- cbind( matrix(1,nrow=num_period) %x% diag(1,season_period), mat_u_hat1 %x% diag(1,season_period) )
            beta_hat <- MASS::ginv(t(mat_Z)%*%mat_Z)%*%(t(mat_Z)%*%matrix(dgp_y,ncol=1) )
            mat_R <- diag( num_r+1 ) %x% matrix(1,nrow=1,ncol=season_period)
            vect_q <- matrix(0,ncol=1,nrow=num_r+1)
            beta_tilde <- beta_hat-MASS::ginv(t(mat_Z)%*%mat_Z)%*%t(mat_R)%*%MASS::ginv( mat_R%*%MASS::ginv(t(mat_Z)%*%mat_Z)%*%t(mat_R))%*%( mat_R%*%beta_hat-vect_q)
            
            mat_v_fixed <- cbind(beta_tilde[1:season_period])
            mat_fixed_hat <-  cbind(rep(1,num_period)) %x% t(mat_v_fixed)
            mat_v_hat2 <- matrix(beta_tilde[-(1:season_period)],nrow=season_period)
            
            matrix_season_hat <- mat_fixed_hat + mat_u_hat1 %*%t(mat_v_hat2)
            season_svd <- as.vector(t(matrix_season_hat))
            
            info_cri <- log(mean((dgp_y-season_svd)^2)) + num_r * log(num_period)/num_period
            
            output <- list(info_cri = info_cri, 
                        mat_u_hat = mat_u_hat1, mat_v_fixed = mat_v_fixed, 
                        mat_v_hat = mat_v_hat2, season_svd = season_svd)
            
        }

        """
        I_seas = np.eye(self.season_period)

        Z = np.hstack((
            np.kron(np.ones((self.periods, 1)), I_seas),
            np.kron(u_hat, I_seas).T
        ))
        Z_D_2_inv = linalg.pinv(Z.T @ self.Delta2 @ Z)
        beta_hat = Z_D_2_inv @ Z.T @ self.Delta2 @ self.signal

        R = np.kron(np.eye(num_r + 1), np.ones((1, self.season_period)))

        # why do we need to subtract zeroes?
        q = np.zeros((num_r+1,))

        beta_tilde = beta_hat - Z_D_2_inv @ R.T @ linalg.pinv(R @ Z_D_2_inv @ R.T) @ (R @ beta_hat - q)
        
        v_fixed = beta_tilde[:self.season_period]
        fixed_hat = np.kron(np.ones((self.periods, 1)), v_fixed.T)
        self._fixed_hat = fixed_hat

        v_hat2 = beta_tilde[self.season_period:].reshape((self.season_period, -1))
        self._v_hat2 = v_hat2

        season_hat = fixed_hat + u_hat.reshape((self.periods,-1)) @ v_hat2.T
        self._season_hat = season_hat

        season_svd = season_hat.reshape(1,-1).squeeze()
    
        info_cri = np.log(np.mean(np.diff(self.signal-season_svd)**2)) + num_r * np.log(self.periods)/self.periods
            
        evalout = namedtuple('evalout', ['info_cri', 'u_hat', 'v_fixed', 'v_hat2', 'season_svd'])
        return evalout(info_cri, u_hat, v_fixed, v_hat2, season_svd)


    def fit(self):
        
        X_D_remain = np.dot(self.Q, self.X_D)

        u_hat1 = []


        info_cri_old = np.Inf
        er_last = None
        er_final = None

        for num_r in range(1, self.max_r):

            self._log("################################################")
            self._log("num_r: ", num_r)

            self._X_D_remain = X_D_remain
            fr = self._fit(X_D_remain)
            self._fr = fr
    
            self._log("alpha_star: ", fr.alpha_star)

            u_hat1.append(fr.u_hat)

            er_cur = self._eval(np.hstack(u_hat1), num_r)

            if er_cur.info_cri > info_cri_old:
                final_r = num_r-1
                er_final = er_last
                break
            else:
                if num_r < self.max_r:
                    info_cri_old = er_cur.info_cri
                    u_hat1 = [er_cur.u_hat]
                    X_D_remain = X_D_remain - fr.u_hat.reshape((self.periods, 1)) @ fr.v_hat.reshape((1, fr.v_hat.shape[0]))
                    er_last = er_cur
                else:
                    final_r = num_r
                    er_final = er_cur


        multifitresult = namedtuple('multifitresult', ['info_cri', 'u_hat', 'v_fixed', 'v_hat2', 'season_svd', 'final_r'])
        return multifitresult(*er_final, final_r)
