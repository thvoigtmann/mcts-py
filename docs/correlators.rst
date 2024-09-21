Correlators and Solvers
=======================
.. include:: <isolat1.txt>

Simple Liquid-Like
------------------

The "simple liquid-like" MCT equations take the form

.. math::

    B_q\partial_t\phi(q,t) + W_q\phi(q,t)
    +\int_0^t M(q,t-t')\partial_{t'}\phi(q,t')\,dt' = 0

where :math:`\phi` and :math:`M` can be scalar or matrix-valued functions
of a single wave-number index and time. The coefficients :math:`B_q`
and :math:`W_q` are model-specific.

We implement a direct solver of these equations, that can be used with
most typical MCT models, including the simple-liquid models
(e.g. :py:class:`mctspy.simple_liquid_model`), models for mixtures
(:py:class:`mctspy.mixture_model`), or even active-particle models
(e.g. :py:class:`mctspy.abp_model_2d`). The underlying algorithm is
essentially the same, although the matrix implementation is somewhat
different from the scalar one.


.. autoclass:: mctspy.correlator
    :members:
    :inherited-members:


MSD and related
---------------

.. autoclass:: mctspy.mean_squared_displacement
    :members:
    :inherited-members:

    The MCT equation for the mean-squared displacement :math:`\delta r^2(t)`
    are (in 3D, and for Brownian dynamics) is

    .. math::

        \partial_t\delta r^2(t)
        + D_0^s\int_0^tm^s_0(t-t')\partial_{t'}\delta r^2(t')\,dt'=6D_0^s

    where the memory kernel is given by the :math:`q\to0` limit of a
    specific model, for example :py:class:`mctspy.tagged_particle_q0`.

.. autoclass:: mctspy.non_gaussian_parameter
    :members:
    :inherited-members:

    The MCT equation for the non-Gaussian parameter :math:`\alpha_2(t)` is
    (in 3D, and for Brownian dynamics) written in terms of the function
    :math:`a(t)=(1-\alpha_2(t))(\delta r^2(t))^2` where
    :math:`\delta r^2(t)` is the mean-squared displacement, which needs
    to be calculated first and separately. Then, this class allows to solve

    .. math::

        \begin{multline}
        \partial_ta(t)+D_0^s\int_0^tm^s_0(t-t')\partial_{t'}a(t')\,dt'\\
        =12D_0^s\delta r^2(t)+6D_0^2\int_0^t\tilde m^s_0(t-t')
        \partial_{t'}\delta r^2(t')\,dt'
        \end{multline}

    where the memory kernels are given by the specific model.
    For example, the simple-liquid model in 3d specifies, via
    :py:class:`mctspy.tagged_particle_ngp`,

    .. math::

        \begin{align}
        m^s_0&=\frac1{6\pi^2}\int\rho S_k(c_k^s)^2k^4f_kf_k^s\,dk\\
        \tilde m^s_0&=\frac1{10\pi^2}\int\rho S_k(c_k^s)^2k^4
            (\partial_k^2f^s_k+(2/3k)\partial_kf^s_k)\,dk
        \end{align}

    The memory kernel :math:`m^s_0(t)` is exactly that of the MSD.
    For technical reasons, the implementation expects the model to
    define a two-correlator model, comprised of the two memory kernels
    needed by the NGP equation. The first "correlator" entry in the
    solutions will be the quantity :math:`a(t)` while the second will be
    a copy of the base model's MSD, so that :math:`\alpha_2(t)` can be
    reconstructed for finite times. For very small times, expect this to
    be inaccurate due to cancellation errors; it is best to restrict the
    temporal range where the data is plotted.

Asymptotics
-----------

The :math:`\beta`-scaling equation of MCT is

.. math::

     \sigma - \delta t + \lambda (g(t))^2 = \frac{d}{dt}(g\ast g)(t)

where :math:`\ast` denotes the time-domain convolution. This equation has
to be solved with initial condition :math:`g(t)\sim(t/t_0)^{-a}` for
short times. The exponent :math:`a` is determined by the exponent parameter
:math:`lambda` (see :py:func:`mctspy.exponents`), which can be calculated
from a specific model and a specific glass-transition point.
The parameter :math:`\sigma` is a measure of the distance from the transition
point, such that :math:`\sigma>0` signifies a glass-like solution
(for which :math:`g(t)` approaches a positive constant at long times)
and :math:`\sigma<0` a liquid-like solution. For the latter, the
asymptotic behavior at long times is :math:`g(t)\sim-B_\lambda(t/t_\sigma)^b`,
the celebrated von Schweidler law of MCT. The parameter
:math:`B_\lambda` needs to be determined numerically,
see [Goetze1990]_ and :py:func:`mctspy.util.Blambda`.

The parameter :math:`\delta` is the so-called "hopping" term, which was
introduced to describe asymptotically the decay of correlation functions
even in the ideal-glass state of MCT. See [Goetze1987]_ for details.

.. [Goetze1987] W. G\ |ouml|\ tze and L. Sj\ |ouml|\ gren,
   Z. Phys. B 65, 415 (1987),
   `DOI:10.1007/BF01303763 <https://doi.org/10.1007/BF01303763>`_

.. [Goetze1990] W. G\ |ouml|\ tze,
   J. Phys.: Condens. Matter 2, 8485 (1990),
   `DOI:10.1088/0953-8984/2/42/025 <https://doi.org/10.1088/0953-8984/2/42/025>`_


.. autoclass:: mctspy.beta_scaling_function
    :members:

.. autofunction:: mctspy.util.Blambda

    The table was calculated using the following code:

    .. code-block:: python

        ltab = np.linspace(0.5,0.98,49)
        Btab = []
        for l in ltab:
            g = mct.beta_scaling_function (lam=l, sigma=-1.0, delta=0.0, store=True)
            mct.CorrelatorStack([g]).solve_all()
            a, b = mct.util.exponents(l)
            Btab.append(np.mean((g.phi[1:,0]*np.power(g.t[1:],-b))[-50:]))
        Btab = np.array(Btab)

    The values in our table closely match and extend the ones given by
    G\ |ouml|\ tze, although some deviations appear in the third digit.


High-level interface
--------------------

.. autoclass:: mctspy.CorrelatorStack
    :members:

