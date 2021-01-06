from scipy import linalg, optimize
import numpy as np


def RSVD(X, Omega):

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
            M_nu = linalg.inv(I + (10.**nu) * Omega)
            return (1/rows_X) * np.sum(np.dot(np.dot((I - M_nu), X), v) ** 2) / (1 - np.trace(M_nu)/rows_X) ** 2

        re_gcv = optimize.minimize_scalar(gcv, bounds=(-6,6), method='brent')

        alpha_star = 10^(re_gcv.x)
        u = np.dot(np.dot(np.inv(I + alpha_star * Omega), X), v)
        criter = np.mean((u-u_ini)^2)
        iter = iter + 1
        u_ini = u
    
    return u, v, alpha_star


def eval(u_hat, periods, season_period):
    """
    func_EVAL <- function(mat_u_hat1){
        
        mat_Z <- cbind( matrix(1,nrow=num_period) %x% diag(1,season_period), mat_u_hat1 %x% diag(1,season_period) )
        beta_hat <- MASS::ginv(t(mat_Z)%*%mat_Delta_sq%*%mat_Z)%*%(t(mat_Z)%*%mat_Delta_sq%*%matrix(dgp_y,ncol=1) )
        mat_R <- diag( num_r+1 ) %x% matrix(1,nrow=1,ncol=season_period)
        vect_q <- matrix(0,ncol=1,nrow=num_r+1)
        beta_tilde <- beta_hat-MASS::ginv(t(mat_Z)%*%mat_Delta_sq%*%mat_Z)%*%t(mat_R)%*%MASS::ginv( mat_R%*%MASS::ginv(t(mat_Z)%*%mat_Delta_sq%*%mat_Z)%*%t(mat_R))%*%( mat_R%*%beta_hat-vect_q)
        
        mat_v_fixed <- cbind(beta_tilde[1:season_period])
        mat_fixed_hat <-  cbind(rep(1,num_period)) %x% t(mat_v_fixed)
        mat_v_hat2 <- matrix(beta_tilde[-(1:season_period)],nrow=season_period)
        
        matrix_season_hat <- mat_fixed_hat + mat_u_hat1 %*%t(mat_v_hat2)
        season_svd <- as.vector(t(matrix_season_hat))
        
        info_cri <- log(mean((diff(dgp_y-season_svd))^2))  + num_r * log(num_period)/num_period
        
        output <- list(info_cri = info_cri, 
                    mat_u_hat = mat_u_hat1, mat_v_fixed = mat_v_fixed, 
                    mat_v_hat = mat_v_hat2, season_svd = season_svd)
        
    }
    """
    I_seas = np.eye(season_period)
    Z = np.hstack(
        np.kron(np.ones((periods, periods)), I_seas),
        np.kron(u_hat, I_seas)
    )

    Delta_sq = ??
    dgp_y = ??

    Z_Delta_sq = np.dot(Z.T, Delta_sq)
    beta_hat = np.dot(np.pinv(np.dot(Z_Delta_sq, Z)), np.dot(Z_Delta_sq, dgp_y))

        beta_hat <- MASS::ginv(t(mat_Z)%*%mat_Delta_sq%*%mat_Z)%*%(t(mat_Z)%*%mat_Delta_sq%*%matrix(dgp_y,ncol=1) )
        mat_R <- diag( num_r+1 ) %x% matrix(1,nrow=1,ncol=season_period)
        vect_q <- matrix(0,ncol=1,nrow=num_r+1)
        beta_tilde <- beta_hat-MASS::ginv(t(mat_Z)%*%mat_Delta_sq%*%mat_Z)%*%t(mat_R)%*%MASS::ginv( mat_R%*%MASS::ginv(t(mat_Z)%*%mat_Delta_sq%*%mat_Z)%*%t(mat_R))%*%( mat_R%*%beta_hat-vect_q)
        
        mat_v_fixed <- cbind(beta_tilde[1:season_period])
        mat_fixed_hat <-  cbind(rep(1,num_period)) %x% t(mat_v_fixed)
        mat_v_hat2 <- matrix(beta_tilde[-(1:season_period)],nrow=season_period)
        
        matrix_season_hat <- mat_fixed_hat + mat_u_hat1 %*%t(mat_v_hat2)
        season_svd <- as.vector(t(matrix_season_hat))
        
        info_cri <- log(mean((diff(dgp_y-season_svd))^2))  + num_r * log(num_period)/num_period
        
        output <- list(info_cri = info_cri, 
                    mat_u_hat = mat_u_hat1, mat_v_fixed = mat_v_fixed, 
                    mat_v_hat = mat_v_hat2, season_svd = season_svd)
