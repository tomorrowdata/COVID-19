from scipy import linalg, optimize
import numpy as np
import pandas as pd

class RSVDSeasonalRegularizer(object):

    def _log(self, *args):
        print(*args)

    def __init__(self, signal, season_period, num_r):
        
        self.season_period = season_period
        self.num_r = num_r

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
        self.D = np.eye(N=self.periods-2,M=self.periods)+np.eye(N=self.periods-2,M=self.periods, k=2)-2*np.eye(N=self.periods-2,M=self.periods, k=1)
        self.Omega = np.dot(self.D.T, self.D)

        """
        demeaning operator:

        mat_Q_n <- diag(1,num_period) - matrix(1/num_period,nrow = num_period,ncol=num_period)
        mat_Y_remain <- mat_Q_n%*%mat_Y
        """
        self.Q = np.eye(N=self.periods)-np.full(shape=(self.periods,self.periods), fill_value=1/self.periods)

        self.X_remain = np.dot(self.Q, self.X)

    def RSVD(self, X):

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
        u_ini,_,_ = linalg.svd(X, full_matrices=False)

        while criter > 10.**(-3) and iter < 100:
            v = np.dot(X.T, u_ini)
            v = v / np.sum(v**2)

            def gcv(nu):
                M_nu = linalg.inv(I + (10.**nu) * self.Omega)
                return (1/rows_X) * np.sum(np.dot(np.dot((I - M_nu), X), v) ** 2) / (1 - np.trace(M_nu)/rows_X) ** 2

            re_gcv = optimize.minimize_scalar(gcv, bounds=(-6,6), method='brent')

            alpha_star = 10^(re_gcv.x)
            u = np.dot(np.dot(np.inv(I + alpha_star * self.Omega), X), v)
            criter = np.mean((u-u_ini)^2)
            iter = iter + 1
            u_ini = u
        
        return u, v, alpha_star


    def eval(self, u_hat):
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
        Z = np.hstack(
            np.kron(np.ones((self.periods, self.periods)), I_seas),
            np.kron(u_hat, I_seas)
        )
        
        Z_2_inv = linalg.pinv(np.dot(Z.T, Z))
        beta_hat = np.dot(Z_2_inv, np.dot(Z.T, self.signal))

        R = np.kron(np.eye(self.num_r + 1), np.ones(1, self.season_period))

        q = np.zeros((self.num_r+1, 1))

        beta_tilde = beta_hat - np.dot(
            Z_2_inv, 
            np.dot(
                np.dot(
                    R.T, 
                    linalg.pinv(np.dot(np.dot(R, Z_2_inv), R.T))
                ),
                (np.dot(R, beta_hat - q))
            )
        )

        v_fixed = beta_tilde[1:self.season_period].T
        fixed_hat = np.kron(np.ones((self.periods, 1)), v_fixed.T)

        v_hat2 = beta_tilde[self.season_period:].reshape((self.season_period, -1))

        season_hat = fixed_hat + np.dot(u_hat, v_hat2.T)

        season_svd = season_hat.T.reshape(1,-1).squeeze()
    
        info_cri = np.log(np.mean((self.signal-season_svd)**2)) + self.num_r * np.log(self.periods)/self.periods
            
        return info_cri, u_hat, v_fixed, v_hat2, season_svd

