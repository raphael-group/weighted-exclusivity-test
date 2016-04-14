#!/usr/bin/env python

import numpy as np, numpy.linalg
from scipy.optimize import fsolve
from scipy.stats import norm

def saddlepoint_exclusive_3(z, m_w, m_x, m_y, p_w, p_x, p_y, verbose=False):

    # Precompute commonly used constants.

    q_w = 1.0-p_w
    q_x = 1.0-p_x
    q_y = 1.0-p_y

    # Define K.

    def L(q, r, s, t):
        return np.exp(q+t)*p_w*q_x*q_y + np.exp(r+t)*q_w*p_x*q_y + np.exp(s+t)*q_w*q_x*p_y + \
               np.exp(q+r)*p_w*p_x*q_y + np.exp(q+s)*p_w*q_x*p_y + np.exp(r+s)*q_w*p_x*p_y + \
               np.exp(q+r+s)*p_w*p_x*p_y + q_w*q_x*q_y

    def K(q, r, s, t):
        return np.sum(np.log(L(q, r, s, t)))

    # Define K'.

    def L_q(q, r, s, t):
        return np.exp(q+t)*p_w*q_x*q_y + \
               np.exp(q+r)*p_w*p_x*q_y + np.exp(q+s)*p_w*q_x*p_y + \
               np.exp(q+r+s)*p_w*p_x*p_y

    def L_r(q, r, s, t):
        return np.exp(r+t)*q_w*p_x*q_y + \
               np.exp(q+r)*p_w*p_x*q_y + np.exp(r+s)*q_w*p_x*p_y + \
               np.exp(q+r+s)*p_w*p_x*p_y


    def L_s(q, r, s, t):
        return np.exp(s+t)*q_w*q_x*p_y + \
               np.exp(q+s)*p_w*q_x*p_y + np.exp(r+s)*q_w*p_x*p_y + \
               np.exp(q+r+s)*p_w*p_x*p_y

    def L_t(q, r, s, t):
        return np.exp(q+t)*p_w*q_x*q_y + np.exp(r+t)*q_w*p_x*q_y + np.exp(s+t)*q_w*q_x*p_y

    def K_q(q, r, s, t):
        return np.sum(L_q(q, r, s, t)/L(q, r, s, t))

    def K_r(q, r, s, t):
        return np.sum(L_r(q, r, s, t)/L(q, r, s, t))

    def K_s(q, r, s, t):
        return np.sum(L_s(q, r, s, t)/L(q, r, s, t))

    def K_t(q, r, s, t):
        return np.sum(L_t(q, r, s, t)/L(q, r, s, t))

    def dK(q, r, s, t):
        return np.array([K_q(q, r, s, t), K_r(q, r, s, t), K_s(q, r, s, t), K_t(q, r, s, t)])

    # Define K''.

    def L_qq(q, r, s, t):
        return np.exp(q+t)*p_w*q_x*q_y + \
               np.exp(q+r)*p_w*p_x*q_y + np.exp(q+s)*p_w*q_x*p_y + \
               np.exp(q+r+s)*p_w*p_x*p_y

    def L_qr(q, r, s, t):
        return np.exp(q+r)*p_w*p_x*q_y + \
               np.exp(q+r+s)*p_w*p_x*p_y

    def L_qs(q, r, s, t):
        return np.exp(q+s)*p_w*q_x*p_y + \
               np.exp(q+r+s)*p_w*p_x*p_y

    def L_qt(q, r, s, t):
        return np.exp(q+t)*p_w*q_x*q_y

    def L_rr(q, r, s, t):
        return np.exp(r+t)*q_w*p_x*q_y + \
               np.exp(q+r)*p_w*p_x*q_y + np.exp(r+s)*q_w*p_x*p_y + \
               np.exp(q+r+s)*p_w*p_x*p_y

    def L_rs(q, r, s, t):
        return np.exp(r+s)*q_w*p_x*p_y + \
               np.exp(q+r+s)*p_w*p_x*p_y

    def L_rt(q, r, s, t):
        return np.exp(r+t)*q_w*p_x*q_y

    def L_ss(q, r, s, t):
        return np.exp(s+t)*q_w*q_x*p_y + \
               np.exp(q+s)*p_w*q_x*p_y + np.exp(r+s)*q_w*p_x*p_y + \
               np.exp(q+r+s)*p_w*p_x*p_y

    def L_st(q, r, s, t):
        return np.exp(s+t)*q_w*q_x*p_y

    def L_tt(q, r, s, t):
        return np.exp(q+t)*p_w*q_x*q_y + np.exp(r+t)*q_w*p_x*q_y + np.exp(s+t)*q_w*q_x*p_y

    def K_qq(q, r, s, t):
        return np.sum(L_qq(q, r, s, t)/L(q, r, s, t) - (L_q(q, r, s, t)**2)/(L(q, r, s, t)**2))

    def K_qr(q, r, s, t):
        return np.sum(L_qr(q, r, s, t)/L(q, r, s, t) - (L_q(q, r, s, t)*L_r(q, r, s, t))/(L(q, r, s, t)**2))

    def K_qs(q, r, s, t):
        return np.sum(L_qs(q, r, s, t)/L(q, r, s, t) - (L_q(q, r, s, t)*L_s(q, r, s, t))/(L(q, r, s, t)**2))

    def K_qt(q, r, s, t):
        return np.sum(L_qt(q, r, s, t)/L(q, r, s, t) - (L_q(q, r, s, t)*L_t(q, r, s, t))/(L(q, r, s, t)**2))

    def K_rr(q, r, s, t):
        return np.sum(L_rr(q, r, s, t)/L(q, r, s, t) - (L_r(q, r, s, t)**2)/(L(q, r, s, t)**2))

    def K_rs(q, r, s, t):
        return np.sum(L_rs(q, r, s, t)/L(q, r, s, t) - (L_r(q, r, s, t)*L_s(q, r, s, t))/(L(q, r, s, t)**2))

    def K_rt(q, r, s, t):
        return np.sum(L_rt(q, r, s, t)/L(q, r, s, t) - (L_r(q, r, s, t)*L_t(q, r, s, t))/(L(q, r, s, t)**2))

    def K_ss(q, r, s, t):
        return np.sum(L_ss(q, r, s, t)/L(q, r, s, t) - (L_s(q, r, s, t)**2)/(L(q, r, s, t)**2))

    def K_st(q, r, s, t):
        return np.sum(L_st(q, r, s, t)/L(q, r, s, t) - (L_s(q, r, s, t)*L_t(q, r, s, t))/(L(q, r, s, t)**2))

    def K_tt(q, r, s, t):
        return np.sum(L_tt(q, r, s, t)/L(q, r, s, t) - (L_t(q, r, s, t)**2)/(L(q, r, s, t)**2))

    def d2K(q, r, s, t):
        return np.array([[K_qq(q, r, s, t), K_qr(q, r, s, t), K_qs(q, r, s, t), K_qt(q, r, s, t)],
                         [K_qr(q, r, s, t), K_rr(q, r, s, t), K_rs(q, r, s, t), K_rt(q, r, s, t)],
                         [K_qs(q, r, s, t), K_rs(q, r, s, t), K_ss(q, r, s, t), K_st(q, r, s, t)],
                         [K_qt(q, r, s, t), K_rt(q, r, s, t), K_st(q, r, s, t), K_tt(q, r, s, t)]])

    # Define K_w and its derivatives.

    def L_w(q):
        return np.exp(q)*p_w + q_w

    def L_wq(q):
        return np.exp(q)*p_w

    def L_wqq(q):
        return np.exp(q)*p_w

    def K_w(q):
        return np.sum(np.log(L_w(q)))

    def dK_w(q):
        return np.sum(L_wq(q)/L_w(q))

    def d2K_w(q):
        return np.sum(L_wqq(q)/L_w(q) - (L_wq(q)**2)/(L_w(q)**2))

    # Define K_x and its derivatives.

    def L_x(r):
        return np.exp(r)*p_x + q_x

    def L_xr(r):
        return np.exp(r)*p_x

    def L_xrr(r):
        return np.exp(r)*p_x

    def K_x(r):
        return np.sum(np.log(L_x(r)))

    def dK_x(r):
        return np.sum(L_xr(r)/L_x(r))

    def d2K_x(r):
        return np.sum(L_xrr(r)/L_x(r) - (L_xr(r)**2)/(L_x(r)**2))

    # Define K_y and its derivatives.

    def L_y(s):
        return np.exp(s)*p_y + q_y

    def L_ys(s):
        return np.exp(s)*p_y

    def L_yss(s):
        return np.exp(s)*p_y

    def K_y(s):
        return np.sum(np.log(L_y(s)))

    def dK_y(s):
        return np.sum(L_ys(s)/L_y(s))

    def d2K_y(s):
        return np.sum(L_yss(s)/L_y(s) - (L_ys(s)**2)/(L_y(s)**2))

    # Solve K_wq(q_h) = m_w.

    def dK_w_wrapper((q, )):
        return np.array([dK_w(q)-m_w])

    def d2K_w_wrapper((q, )):
        return np.array([d2K_w(q)])

    q_h, = fsolve(dK_w_wrapper, 1.0, fprime=d2K_w_wrapper)

    # Solve K_xr(r_h) = m_x.

    def dK_x_wrapper((r, )):
        return np.array([dK_x(r)-m_x])

    def d2K_x_wrapper((r, )):
        return np.array([d2K_x(r)])

    r_h, = fsolve(dK_x_wrapper, 1.0, fprime=d2K_x_wrapper)

    # Solve K_ys(s_h) = m_y.

    def dK_y_wrapper((s, )):
        return np.array([dK_y(s)-m_y])

    def d2K_y_wrapper((s, )):
        return np.array([d2K_y(s)])

    s_h, = fsolve(dK_y_wrapper, 1.0, fprime=d2K_y_wrapper)

    # Solve dK(r_t, s_t, t_t) = (m_x, m_y, z-0.5).

    def dK_wrapper((q, r, s, t)):
        return dK(q, r, s, t)-np.array([m_w, m_x, m_y, z-0.5])

    def d2K_wrapper((q, r, s, t)):
        return d2K(q, r, s, t)

    q_t, r_t, s_t, t_t = fsolve(dK_wrapper, np.ones(4), fprime=d2K_wrapper)

    # Compute saddlepoint approximation.

    w_t_inside = 2.0*((K_w(q_h)+K_x(r_h)+K_y(s_h))-(m_w*q_h+m_x*r_h+m_y*s_h) - \
                      (K(q_t, r_t, s_t, t_t)-(m_w*q_t+m_x*r_t+m_y*s_t+(z-0.5)*t_t)))
    w_t = np.sign(t_t)*np.sqrt(w_t_inside)

    u_t_inside = np.linalg.det(d2K(q_t, r_t, s_t, t_t))/(d2K_w(q_h)*d2K_x(r_h)*d2K_y(s_h))
    u_t = 2.0*np.sinh(0.5*t_t)*np.sqrt(u_t_inside)

    return norm.cdf(-w_t)-norm.pdf(w_t)*(1.0/w_t-1.0/u_t)
