MCT Models
==========

Simple Liquids
--------------

"Simple liquid" models are the "standard models" of MCT. The liquid is
assumed to be isotropic, homogeneous, and composed of identical particles
without relevant internal degrees of freedom, so that their positions provide
full information on the configuration.
The MCT equations then take the form of scalar-valued
equations for each :math:`\phi(q,t)`, where :math:`q` is the wave number.
The different :math:`q` only couple through the memory kernel, and
for its implementation, the values are usually chosen on a regular grid
(although model implementations may deal with more general wave-number
grids).

For these models, :math:`\phi(q,t)` is usually normalized
such that :math:`\phi(q,t=0)=1`. For the memory kernel, we adopt
the convention that :math:`\hat m(q,t)=q^2m(q,t)` is the quantity that is
calculated and stored, on the basis that in equilibrium dynamics, this
quantity possesses a non-singular :math:`q\to0` limit.

The evolution equations of simple-liquid models are thus

.. math::

    q^2\omega_q^{-1}\partial_t\phi(q,t) + q^2\phi(q,t)
    + \int_0^t\hat m(q,t-t')\partial_{t'}\phi(q,t)=0





.. autoclass:: mctspy.simple_liquid_model
    :members:
    :inherited-members:


Common Additions to Simple-Liquid Models
----------------------------------------

.. autoclass:: mctspy.tagged_particle_model

.. autoclass:: mctspy.tagged_particle_q0

.. autoclass:: mctspy.tagged_particle_ngp
    :members:
    :inherited-members:

    In essence, we define the following two memory kernels that correspond
    to those needed for the MCT equations for the NGP:

    .. math::

        \begin{align}
        m^s_0&=\frac1{6\pi^2}\int\rho S_k(c_k^s)^2k^4f_kf_k^s\,dk\\
        \tilde m^s_0&=\frac1{10\pi^2}\int\rho S_k(c_k^s)^2k^4
            (\partial_k^2f^s_k+(2/3k)\partial_kf^s_k)\,dk
        \end{align}

    Here, :math:`f^s_k` is the tagged-particle correlator, obtained from
    `self.base` which is set to `model_base.base.base` by the initialization
    method of this class; :math:`f_k` is the collective correlator,
    obtained from `model_base.base.base.base`.

    The first memory kernel is the one that also appears in the MSD,
    however we re-calculate it here. Note however that the MSD is not
    re-calculated (for the sake of modularity, since calculation of the MSD
    is kept to its separate solver).


Mixtures
--------

Mixture models here refer to mixtures of simple-liquid components,
so that the only addition to the case of simple liquids is a particle-species
index. The MCT equations are thus matrix-valued evolution equations
of the form

.. math::

    q^2\boldsymbol\omega(q)^{-1}\cdot\partial_t\boldsymbol\Phi(q,t)
    +q^2\boldsymbol S(q)^{-1}\cdot\boldsymbol\Phi)(q,t)
    +\int_0^t q^2\boldsymbol M(q,t-t')\cdot\partial_{t'}\boldsymbol
    \Phi(q,t')\,dt'=0

where bold symbols indicate :math:`S\times S` matrices for a mixture
of S different species.

Besides multiplication with :math:`q^2`, the mixture memory kernel is
also multiplied with :math:`\sqrt{x_\alpha x_\beta}`, and in turn the
correlation function is divided by that factor. For a mixture where
one species has vanishing concentration, the corresponding diagonal
element of the correlator matrix then is the tagged-particle correlator.

.. autoclass:: mctspy.mixture_model
    :members:
    :inherited-members:

    The MCT memory-kernel expression for mixtures is given by

    .. math::

        M_{\alpha\beta}(q)=\frac{\varrho}{2q^4}\int\frac{d^3k}{(2\pi)^3}
        \sum_{\alpha'\alpha''\beta'\beta''}
        V_{\alpha\alpha'\alpha''}(\vec q,\vec k\vec p)
        V_{\beta\beta'\beta''}(\vec q,\vec k\vec p)
        F_{\alpha'\beta'}(k)F_{\alpha''\beta''}(p)

    with :math:`\vec q=\vec k+\vec p` and vertices

    .. math::

        V_{\alpha\alpha'\alpha''}(\vec q,\vec k\vec p)
        =(\vec q\vec k)\tilde c_{\alpha\alpha'}(k)\delta_{\alpha\alpha''}
        +(\vec q\vec p)\tilde c_{\alpha\alpha''}(p)\delta_{\alpha\alpha'}
        +q\sqrt{x_\alpha}\tilde c^{(3)}_{\alpha\alpha'\alpha''}(\vec q,\vec k)

    where we have introduced the modified DCF
    :math:`\tilde c_{\alpha\beta}(k)=\sqrt{x_\beta}c_{\alpha\beta}(k)`
    and :math:`\tilde c^{(3)}_{\alpha\beta\gamma}(\vec q,\vec k)
    =\sqrt{x_\beta x_\gamma}c^{(3)}_{\alpha\beta\gamma}(\vec q,\vec k)`.
    The quantities :math:`\boldsymbol F` appearing in the expression are
    assumed to be "normalized" to correspond to :math:`\boldsymbol S`, the
    static structure factor, if taken as equal-time averages.

    The three-particle static correlation function is currently not
    implemented.

    We restrict wave vectors to a finite grid, :math:`q_i = (\Delta q)(i+1/2)`
    and write the discretized integral with
    :math:`M_{\alpha\beta}(q)=(1/q^2)\hat M_{\alpha\beta}(q)`

    .. math::
        \hat M_{\alpha\beta}(q) = \frac{(\Delta q)^2}{32\pi^2q^3}\sum_{kp}
        \sum_{\alpha'\alpha''\beta'\beta''} kp
        \hat V_{\alpha\alpha'\alpha''}(q,k,p)\hat V_{\beta\beta'\beta''}(q,k,p)
        F_{\alpha'\beta'}(k)F_{\alpha''\beta''}(p)

    with

    .. math::

        \hat V_{\alpha\alpha'\alpha''}(q,k,p) = \left[
        \delta_{\alpha\alpha''}(q^2+k^2-p^2)\hat c_{\alpha\alpha'}(k)
        +\delta_{\alpha\alpha'}(q^2-k^2+p^2)\hat c_{\alpha\alpha''}(p)\right]

    and :math:`\hat c_{\alpha\beta}(k)=\sqrt{\varrho_\beta}c_{\alpha\beta}(k)`.

    In the above expression and throughout our mixture-model
    implementation, we normalize the correlation functions to have as their
    initial value the non-singular part of the structure factor, i.e. the
    one whose diagonal matrix elements approach unity for large :math:`q`.
    This differs from the common definition of a partial dynamic density
    correlation function: one has to multiply the :math:`\alpha\beta`
    matrix element of our correlation functions by
    :math:`\sqrt{x_\alpha x_\beta}`, and the memory function has to be divided
    by that expression when transforming to the common notation.

    The model also stores :math:`\hat M` instead of :math:`M`.

    These conventions are consistent throughout the rest of the code.

    The memory-kernel integration here uses the Bengtzelius trick. We have

    .. math::

        \begin{align}
        \hat M_{q,\alpha\beta}[f,g]&=\nu
        \sum_{n=1}^3\Big[\phantom+\,
        \sum_{\alpha'\beta'}
        \sum_k a_{\alpha\alpha'\beta\beta'}^{(n)}(k)f_{k,\alpha'\beta'}
        \sum_{p(q,k)} b^{(n)}(q,p)g_{p,\alpha\beta}\\ 
        &\phantom{=p\sum_{n=1}^3\Big[}+
        \sum_{\alpha''\beta''}
        \sum_k a^{(n)}(k)f_{k,\alpha\beta}
        \sum_{p(q,k)}
          b_{\alpha\alpha''\beta\beta''}^{(n)}(q,p)g_{p,\alpha''\beta''}
        \\
        &\phantom{=\nu\sum_{n=1}^3\Big[}+
        \sum_{\alpha'\beta''}
        \sum_k a_{\alpha\alpha'}^{(n)}(k)f_{k,\alpha'\beta}
        \sum_{p(q,k)} b_{\beta\beta''}^{(n)}(q,p)g_{p,\alpha\beta''}\\
        &\phantom{=\nu\sum_{n=1}^3\Big[}+
        \sum_{\alpha''\beta'}
        \sum_k a_{\beta\beta'}^{(n)}(k)f_{k,\alpha\beta'}
        \sum_{p(q,k)} b_{\alpha\alpha''}^{(n)}(q,p)g_{p,\alpha''\beta}
        \;\phantom+\Big]
        \end{align}

    with :math:`\nu = (\Delta q)^2/(32\pi^2q^3)` as a prefactor. This
    expression does not assume symmetry under swapping :math:`f` with
    :math:`g` and is used for the calculation of the stability matrix.
    For the case of the memory kernel itself, the symmetry allows to further
    reduce to

    .. math::

        \begin{align}
        \hat M_{q,\alpha\beta}&=2\nu\sum_{n=1}^3
        \sum_{\gamma\delta}\Big[\phantom+\,
        \sum_k a_{\alpha\gamma\beta\delta}^{(n)}(k)\Phi_{k,\gamma\delta}
        \sum_{p(q,k)} b^{(n)}(q,p)\Phi_{p,\alpha\beta}\\ \nonumber
        &\phantom{=2\nu\sum_{n=1}^3\sum_{\gamma\delta}\Big[}+
        \sum_k a_{\alpha\gamma}^{(n)}(k)\Phi_{k,\gamma\beta}
        \sum_{p(q,k)} b_{\beta\delta}^{(n)}(q,p)\Phi_{p,\alpha\delta}
        \;\phantom+\Big]
        \end{align}

    In the above expressions, the Bengtzelius coefficients are

    .. math::

        \begin{align}
        a^{(1)}(k)&=k^5
        & a_{\alpha\beta}^{(1)}(k)&=k\tilde c_{\alpha\beta}(k)
        & a_{\alpha\beta\gamma\delta}^{(1)}(k)&=k^5\tilde c_{\alpha\beta}(k)
                                               \tilde c_{\gamma\delta}(k)\\
        a^{(2)}(k)&=-2k^3
        & a_{\alpha\beta}^{(2)}(k)&=-k^5\tilde c_{\alpha\beta}(k)
        & a_{\alpha\beta\gamma\delta}^{(2)}(k)&=2k^3\tilde c_{\alpha\beta}(k)
                                                \tilde c_{\gamma\delta}(k)\\
        a^{(3)}(k)&=k
        & a_{\alpha\beta}^{(3)}(k)&=2k^3\tilde c_{\alpha\beta}(k)
        & a_{\alpha\beta\gamma\delta}^{(3)}(k)&=k\tilde c_{\alpha\beta}(k)
                                             \tilde c_{\gamma\delta}(k)
        \\
        b^{(1)}(q,p)&=p
        & b_{\alpha\beta}^{(1)}(q,p)&=p(q^4\!-\!p^4)\tilde c_{\alpha\beta}(p)
        & b_{\alpha\beta\gamma\delta}^{(1)}(q,p)&=p\tilde c_{\alpha\beta}(p)
                                               \tilde c_{\gamma\delta}(p)\\
        b^{(2)}(q,p)&=p(q^2\!-\!p^2)
        & b_{\alpha\beta}^{(2)}(q,p)&=p\tilde c_{\alpha\beta}(p)
        & b_{\alpha\beta\gamma\delta}^{(2)}(q,p)&=p(q^2\!+\!p^2)
                      \tilde c_{\alpha\beta}(p)\tilde c_{\gamma\delta}(p)\\
        b^{(3)}(q,p)&=p(q^2\!-\!p^2)^2
        & b_{\alpha\beta}^{(3)}(q,p)&=p^3\tilde c_{\alpha\beta}(p)
        & b_{\alpha\beta\gamma\delta}^{(3)}(q,p)&=p(q^2\!+\!p^2)^2
                      \tilde c_{\alpha\beta}(p)\tilde c_{\gamma\delta}(p)
        \end{align}

    As in the scalar case, the performance gain known as Bengtzelius' trick
    comes from realizing that the inner sum can be reduced to a
    :math:`\mathcal O(1)` operation when its value for the previous
    outer wave number is known.




Two-dimensional MCT
-------------------

Two-dimensional MCT differs from the three-dimensional one only by
the dimensionality of the wave-vector integral in the memory kernel
(and by the input structure functions which have different large-wave-number
asymptotics). Especially in 2d this requires some care in how the
memory kernel is evaluated, since the usual discretization employed
for MCT introduces a variable transform with a Jacobian that in 2d
contains a square-root singularity. Specific memory-kernel algorithms
are thus implemented, which take care of better approximation, at the
cost of noticeably higher computational effort, since some of the tricks
introduced in the 3d discretization no longer work in 2d.


.. autoclass:: mctspy.simple_liquid_model_2d
    :members:
    :inherited-members:

    The MCT memory kernel implemented here is of the form

    .. math::

        m_q = \rho\int\frac{d^dk}{(4\pi)^d}\frac{S_q}{q^{d+2}}\Omega_{d-1}
              \int_0^\infty dk\,k\Phi_k\int_{|q-k|}^{q+k}dp\,p\Phi_p
              \frac{((q^2+k^2-p^2)c_k + (q^2+p^2-k^2)c_p)^2}
                   {[4q^2k^2-(q^2+k^2-p^2)^2]^{(3-d)/2}}

    specifically for :math:`d=2`. Here, :math:`\Omega_d=2\pi^{d/2}/\Gamma(d/2)`
    is the volume of the unit sphere, and :math:`\Omega_1=2`. Note that
    :math:`\Phi_k=S_k\phi_k(t)` is the non-normalized correlator.

    The code follows the paper by Caraglio et al [Caraglio2020]_.
    The kernel method calculates the outer integral following the
    trapezoidal rule,

    .. math::

        q_i^2 m_i = \frac{\rho S_i}{8\pi^2q_i^2}\sum_{j=0}^{M-2}
              \frac{q_j\Phi_jA_{ij}+q_{j+1}\Phi_{j+1}A_{i,j+1}}{2}
              (q_{j+1}-q_j)

    with the inner integral

    .. math::

        \begin{align}
        A_{ij}&=\int_{|q_i-q_j|}^{q_i+q_j}dp\,p\Phi_p
        \frac{[(q_i^2+q_j^2-p^2)c_j+(q_i^2+p^2-q_j^2)c_p]^2}
             {\sqrt{4q_i^2q_j^2-(q_i^2+q_j^2-p^2)^2}} \\
        &= 2q_i^2q_j^2\int_{-1}^1dx\,\Phi_{p(x)}
        \frac{[x(c_j-c_{p(x)})+(q_i/q_j)c_{p(x)}]^2}{\sqrt{1-x^2}}
        \end{align}

    after substitution :math:`x=(q_i^2+q_j^2-p^2)/(2q_iq_j)`.
    The key of the integration method is to perform the inner integral
    in a way that acknowledges the square-root singularity in the
    denominator: the functions of :math:`p(x)` are approximated as
    piece-wise linear given by the grid points, and the resulting integrands
    of the form :math:`x^\alpha/\sqrt{1-x^2}` are calculated analytically.
    Specifically, one needs here

    .. math::

        \begin{align}
        \int dx\,\frac1{\sqrt{1-x^2}} &= \arcsin x\\
        \int dx\,\frac{x}{\sqrt{1-x^2}} &= -\sqrt{1-x^2}\\
        \int dx\,\frac{x^2}{\sqrt{1-x^2}} &= (1/2)\arcsin x-(x/2)\sqrt{1-x^2}\\
        \int dx\,\frac{x^3}{\sqrt{1-x^2}} &= -(1/3)\sqrt{1-x^2}(2+x^2)
        \end{align}

    Care is taken to extend the integrals to the interval :math:`x\in[-1,1]`,
    except where the upper cutoff of the wave-number grid is reached.

    The idea to perform the weighted integrals over piece-wise linear
    functions analytically goes back to Filon and Tuck who used it for the
    Fourier transform.

    .. [Caraglio2020] M. Caraglio, L. Schrack, G. Jung, and T. Franosch,
       Commun. Comput. Phys. 29, 628 (2021),
       `DOI:10.4208/cicp.OA-2020-0125 <https://doi.org/10.4208/cicp.OA-2020-0125>`_


Schematic Models
----------------
.. include:: <isolat1.txt>

Schematic models are ad-hoc simplifcations of the MCT equations to one or
at most a few correlation functions. They are often formulated as "dropping
the wave number dependence" from the microscopic MCT models, but should be
more generally thought of as the result of applying bifurcation theory
to MCT, and realizing that the asymptotic dynamics close to the glass
transition is described by universal laws that can be reproduced from
schematic models.

.. autoclass:: mctspy.schematic.generic
    :members:
    :inherited-members:

.. autoclass:: mctspy.f12model
    :members:
    :inherited-members:

.. autoclass:: mctspy.sjoegren_model
    :members:
    :inherited-members:

.. autoclass:: mctspy.bosse_krieger_model
    :members:
    :inherited-members:

.. autoclass:: mctspy.f12gammadot_model
    :members:
    :inherited-members:

    This model builds on the F12 model and deals with a single correlator
    with memory kernel
    :math:`m[\phi(t),t] = h(\dot\gamma t)[v_1 \phi(t) + v_2 \phi(t)^2]`.
    The strain-reduction function is defined to be
    :math:`h(\gamma)=1/(1+\gamma^2)`.
    This model was introduced by Fuchs and Cates as a schematic model to
    calculate the dynamics, especially flow curves under strong shear.


.. autoclass:: mctspy.f12gammadot_tensorial_model
    :members:
    :inherited-members:

    This model is the tensorial extension of `mctspy.f12gammadot_model`.
    While it also works under simple shear, it is computationally more
    expensive since it needs to calculate the deformation tensors as
    matrix-exponentials of a given shear-rate tensor.

    The model is specified by a single correlator with memory kernel

    .. math::

        m[\phi(t),t] = h_{t,0}([\boldsymbol B])[v_1 \phi(t) + v_2\phi(t)^2]

    where the strain-reduction function is modeled as a function of
    the two non-trivial invariants of the Finger tensor,
    :math:`\boldsymbol B_{tt'}=\boldsymbol F_{tt'}\cdot\boldsymbol F^T_{tt'}`
    constructed from the deformation tensor
    :math:`\boldsymbol F_{tt'}=\exp[\boldsymbol\kappa\,(t-t')]`,
    valid in homogeneous stationary flow. Specifically,

    .. math::

        h_{tt'}([\boldsymbol B])=\frac{1}{1 + (\nu I_1(\boldsymbol B_{tt'})
            + (1-\nu)I_2(\boldsymbol B_{tt'}) - 3)/\gamma_c^2}

    where :math:`I_1(\boldsymbol B)=\ext{tr}\boldsymbol B` and
    :math:`I_2(\boldsymbol B)=\text{tr}\boldsymbol B^{-1}` are the two
    invariants of the Finger tensor (valid in incompressible flow).

    If the parameter `use_hhat` is set, the model invokes a modified
    evolution equation for the correlator,

    .. math::

        \partial_t\phi(t) + \phi(t) + \hat h_{t0}([\boldsymbol B])\int_0^t
        m(t-t')\partial_{t'}\phi(t')\,dt' = 0

    with setting :math`\hat h=h`. In this form, the model implemented here
    is the one used by Brader et al. [Brader2009]_. Note that since the
    memory kernel is evaluated at time :math:`t-t'`, this model implies
    two strain reduction factors, one given by :math:`\boldsymbol B_{t,t'}`,
    and one given by :math:`\boldsymbol B_{t,0}`.


    .. [Brader2009] J. M. Brader, T. Voigtmann, M. Fuchs, R. G. Larson,
       and M. E. Cates, Proc. Natl. Acad. Sci. (USA) 106, 15186 (2009),
       `DOI:10.1073/pnas.0905330106 <https://doi.org/10.1073/pnas.0905330106>`_
