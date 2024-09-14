import numpy as np

from numba import njit

import h5py

from .__util__ import model_base, loaded_model


@njit
def _decimize (phi, m, dPhi, dM, blocksize):
    halfblocksize = blocksize//2
    imid = halfblocksize//2
    for i in range(1,imid):
        di = i+i
        dPhi[i] = 0.5 * (dPhi[di-1] + dPhi[di])
        dM[i] = 0.5 * (dM[di-1] + dM[di])
    for i in range(imid,halfblocksize):
        di = i+i
        dPhi[i] = 0.25 * (phi[di-2] + 2*phi[di-1] + phi[di])
        dM[i] = 0.25 * (m[di-2] + 2*m[di-1] + m[di])
    dPhi[halfblocksize] = phi[blocksize-1]
    dM[halfblocksize] = m[blocksize-1]
    for i in range(halfblocksize):
        di = i+i
        phi[i] = phi[di]
        m[i] = m[di]
@njit
def _solve_block (istart, iend, h, Bq, Wq, phi, m, dPhi, dM, kernel, maxiter, accuracy, calc_moments, pre_m):

    for i in range(istart,iend):
        mpre = pre_m[i-istart]
        A = mpre*dM[1] + Wq + 1.5*Bq / h
        B = mpre*(-dPhi[1] + phi[0]) / A

        ibar = i//2
        C = -(m[i-1]*dPhi[1] + phi[i-1]*dM[1])
        for k in range(2,ibar+1):
            C += (m[i-k+1] - m[i-k]) * dPhi[k]
            C += (phi[i-k+1] - phi[i-k]) * dM[k]
        if (i-ibar > ibar):
            C += (phi[i-ibar] - phi[i-ibar-1]) * dM[k]
        C += m[i-ibar] * phi[ibar]
        C = mpre*C + (-2.0*phi[i-1] + 0.5*phi[i-2]) * Bq/h
        C = C/A

        iterations = 0
        converged = False
        newphi = phi[i-1]
        while (not converged and iterations < maxiter):
            phi[i] = newphi
            kernel (m[i], phi[i], i, h*i)
            newphi = B*m[i] - C
            iterations += 1
            if np.isclose (newphi, phi[i],
                           rtol=accuracy, atol=accuracy).all():
                converged = True
                phi[i] = newphi
                if calc_moments:
                    dPhi[i] = 0.5 * (phi[i-1] + phi[i])
                    dM[i] = 0.5 * (m[i-1] + m[i])

@njit
def _solve_block_mat (istart, iend, h, Bq, Wq, phi, m, dPhi, dM, M, kernel, maxiter, accuracy, calc_moments):

    Ainv = np.zeros_like(Wq)
    B = np.zeros_like(Wq)
    C = np.zeros_like(Wq)

    for q in range(M):
        Ainv[q] = np.linalg.inv(Wq[q] + dM[1,q] + Bq[q]*1.5/h)
        B[q] = -dPhi[1,q] + phi[0,q]

    for i in range(istart,iend):
        ibar = i//2
        for q in range(M):
            C[q] = -( m[i-1,q] @ dPhi[1,q] + dM[1,q] @ phi[i-1,q] )
        for k in range(2,ibar+1):
            for q in range(M):
                C[q] += (m[i-k+1,q] - m[i-k,q]) @ dPhi[k,q] \
                      + dM[k,q] @ (phi[i-k+1,q] - phi[i-k,q])
        if (i-ibar > ibar):
            for q in range(M):
                C[q] += dM[k,q] @ (phi[i-ibar,q] - phi[i-ibar-1,q])
        for q in range(M):
            C[q] += m[i-ibar,q] @ phi[ibar,q]
            C[q] += Bq[q] @ (-2*phi[i-1,q] + 0.5*phi[i-2,q]) / h
            C[q] = Ainv[q] @ C[q]

        iterations = 0
        converged = False
        newphi = phi[i-1].copy()
        while (not converged and iterations < maxiter):
            phi[i] = newphi
            kernel (m[i], phi[i], i, h*i)
            for q in range(M):
                newphi[q] = Ainv[q] @ m[i,q] @ B[q] - C[q]
            iterations += 1
            if np.isclose(newphi.reshape(-1), phi[i].reshape(-1),
                          rtol=accuracy, atol=accuracy).all():
                converged = True
                phi[i,...] = newphi
                if calc_moments:
                    dPhi[i] = 0.5 * (phi[i-1] + phi[i])
                    dM[i] = 0.5 * (m[i-1] + m[i])

class correlator (object):
    """Class for calculating MCT correlators in the time domain.

    This sets up the standard solver developed for MCT-type equations,
    using a block-wise regular time-domain grid, and a "decimation"
    procedure doubling the step size from block to block.

    Parameters
    ----------
    blocksize : int
        Number of equidistant time steps per block. Will be adjusted
        to be divisible by four.
    h : float
        Stepsize in the first block.
    blocks : int
        Number of blocks to solve for.
    Tend : float, optional
        If larger than zero, fix the number of blocks such that
        the solution at least span the times up to `Tend`.
        If given, the user-specified value of `blocks` will be ignored,
        but both `blocksize` and `h` will be kept. The actual
        final time reached by the solver can be larger than `Tend`.
    maxinit : int, optional
        Number of points in the first block to initialize from a
        short-time expansion of the equations. Must be smaller than
        half the blocksize.
    maxiter : int, optional
        Maximum number of iterations taken per time step.
    accuracy : float, optional
        Accuracy goal for the iterations taken at each time step.
    store : bool, default: False
        If set to True, the full solutions will be stored in memory.
        This is needed for later processing in the main program, and
        for saving. If False, only the last block is kept.
        Mostly there for historical reasons and to save some memory
        if needed.
    model : model_base
        The actual MCT model to solve. This object needs to define
        at least the function returning the value of the memory kernel
        given the current correlator values and will be repeatedly
        called during the iteration for each time step.
    base : correlator, optional
        In case of models that refer to underlying base models, the
        memory-kernel implementation usually assumes the underlying model
        to have been solved one the same time grid. This parameter
        then should point to the underlying correlator for that model,
        and the values of `h`, `blocksize`, and `blocks` will be copied
        from there instead of taking the ones supplied here.

    Notes
    -----
    The accuracy of the solution is determined primarily by the
    parameters `blocksize` and `h`.

    The methods defined here for the solver will usually not be called
    directly, but from the `solve_all` method of the correlator stack.
    The `correlator` object will then be filled with the solution arrays.

    If `store` is `True`, the fields `t`, `phi`, and `m` will be set
    to contain the solutions. They have shape (T,M) for scalar models,
    and shape (T,M,S,S) for matrix-valued models.
    """
    def __init__ (self, blocksize=256, h=1e-9, blocks=60, Tend=0.0,
                  maxinit=50, maxiter=10000, accuracy=1e-9, store=False,
                  model = model_base, base = None):
        if base is None:
            self.h0 = h
            self.halfblocksize = (blocksize//4)*2
            self.blocksize = self.halfblocksize * 2
            if Tend > 0.:
                self.blocks = 1 + int(np.ceil(np.log(Tend/self.h0/(self.blocksize-1))/np.log(2.)))
                print("adjusting to",self.blocks,"blocks")
            else:
                self.blocks = blocks
        else:
            self.h0 = base.h0
            self.blocks = base.blocks
            self.blocksize = base.blocksize
            self.halfblocksize = blocksize//2
            #self.base = base
        self.h = self.h0
        self.maxinit = maxinit
        self.mdimen = len(model)
        self.dim = model.matrix_dimension()
        self.phi_ = np.zeros((self.blocksize,self.mdimen*self.dim**2))
        self.m_ = np.zeros((self.blocksize,self.mdimen*self.dim**2))
        self.dPhi_ = np.zeros((self.halfblocksize+1,self.mdimen*self.dim**2))
        self.dM_ = np.zeros((self.halfblocksize+1,self.mdimen*self.dim**2))
        self.store = store
        if store:
            self.t = np.zeros(self.halfblocksize*(self.blocks+1))
            if model.scalar()==1:
                self.phi = np.zeros((self.halfblocksize*(self.blocks+1),self.mdimen*self.dim**2))
                self.m = np.zeros((self.halfblocksize*(self.blocks+1),self.mdimen*self.dim**2))
            else:
                self.phi = np.zeros((self.halfblocksize*(self.blocks+1),self.mdimen,self.dim,self.dim))
                self.m = np.zeros((self.halfblocksize*(self.blocks+1),self.mdimen,self.dim,self.dim))

        self.maxiter = maxiter
        self.accuracy = accuracy

        self.model = model
        model.set_base(self.phi_)
        self.jit_kernel = model.get_kernel(self.m_[0],self.phi_[0],0,0.0)

        self.solved = -2

    def initial_values (self, imax):
        """Initialize with short-time expansion.

        Parameters
        ----------
        imax : int
            Number of time steps to initialize. Will be adjusted to be
            less than half the blocksize.
        """
        iend = imax
        if (iend >= self.halfblocksize): iend = self.halfblocksize-1
        phi0 = self.model.phi0()
        if self.model.scalar():
            tauinv = self.model.Wq() * phi0 / self.model.Bq()
        else:
            tauinv = np.zeros_like(phi0)
            Bq = self.model.Bq()
            WqSq = self.model.WqSq()
            for q in range(self.mdimen):
                tauinv[q] = np.linalg.inv(Bq[q]) @ WqSq[q]
        for i in range(iend):
             t = i*self.h0
             self.phi_[i] = (phi0 - tauinv * t).reshape(-1)
             self.jit_kernel (self.m_[i].reshape(-1,self.dim,self.dim), self.phi_[i].reshape(-1,self.dim,self.dim), i, t)
        for i in range(1,iend):
             self.dPhi_[i] = 0.5 * (self.phi_[i-1] + self.phi_[i])
             self.dM_[i] = 0.5 * (self.m_[i-1] + self.m_[i])
        self.dPhi_[iend] = self.phi_[iend-1]
        self.dM_[iend] = self.m_[iend-1]
        self.iend = iend

    def decimize (self):
        _decimize (self.phi_, self.m_, self.dPhi_, self.dM_, self.blocksize)
        self.h = self.h * 2.0

    # core interface, can be reimplemented by derived solvers
    # this is not safe to be reused with save/restore functionality
    def solve_block (self, istart, iend):
        if 'kernel_prefactor' in dir(self.model):
            pre_m = self.model.kernel_prefactor(np.arange(istart,iend)*self.h)
        else:
            pre_m = np.ones_like(range(istart,iend))
        if self.model.scalar():
            _solve_block (istart, iend, self.h, self.model.Bq(), self.model.Wq(), self.phi_, self.m_, self.dPhi_, self.dM_, self.jit_kernel, self.maxiter, self.accuracy,(istart<self.blocksize//2), pre_m)
        else:
            if 'kernel_prefactor' in dir(self.model):
                raise NotImplementedError
            _solve_block_mat (istart, iend, self.h, self.model.Bq().reshape(-1,self.dim,self.dim), self.model.Wq().reshape(-1,self.dim,self.dim), self.phi_.reshape(-1,self.mdimen,self.dim,self.dim), self.m_.reshape(-1,self.mdimen,self.dim,self.dim), self.dPhi_.reshape(-1,self.mdimen,self.dim,self.dim), self.dM_.reshape(-1,self.mdimen,self.dim,self.dim), self.mdimen, self.jit_kernel, self.maxiter, self.accuracy,(istart<self.blocksize//2))

    # new interface with reconstruction of already solved cases
    # does not call the jitted _solve_block directly because
    # for example the MSD solver wants to put its own implementation there
    def solve_first (self):
        """Solver interface, solve first half of time-domain block.

        This should be the first method called to solve the correlators.
        It initializes a given number of points from a short-time expansion,
        and fills the first half of the first block by calling the solver.

        Notes
        -----
        If `store` is True, the solver keeps track of whether the solutions
        are already in memory, and only calls the `solve_block` if needed.
        """
        self.h = self.h0
        if not self.store or not self.solved >= -1:
            self.initial_values (self.maxinit)
            self.solve_block (self.iend, self.halfblocksize)
            if self.store:
                N2 = self.halfblocksize
                self.t[:N2] = self.h * np.arange(N2)
                if self.model.scalar():
                    self.phi[:N2,:] = self.phi_[:N2,:]
                    self.m[:N2,:] = self.m_[:N2,:]
                else:
                    self.phi[:N2,:] = self.phi_[:N2,:].reshape(N2,self.mdimen,self.dim,self.dim)
                    self.m[:N2,:] = self.m_[:N2,:].reshape(N2,self.mdimen,self.dim,self.dim)
            self.solved = -1
        else:
            N2 = self.halfblocksize
            self.phi_[:N2,:] = self.phi[:N2,:].reshape(N2,-1)
            self.m_[:N2,:] = self.m[:N2,:].reshape(N2,-1)
            self.dPhi_[1:N2,:] = ((self.phi_[:N2-1,:] + self.phi_[1:N2,:])/2.).reshape(N2-1,-1)
            self.dM_[1:N2,:] = ((self.m_[:N2-1,:] + self.m_[1:N2,:])/2.).reshape(N2-1,-1)
    def solve_next (self, d):
        """Solver interface, solve in a given block.

        This assumes that the first half of the block has been pre-filled
        will valid solutions, and then completes the solutions in the block.
        The assumption will be valid if `solve_first` has been called before.

        Notes
        -----
        If `store` is True, the solver keeps track of whether the solutions
        are already in memory, and only calls the `solve_block` if needed.
        """
        if not self.store or not self.solved >= d:
            self.solve_block (self.halfblocksize, self.blocksize)
            if self.store:
                N2 = self.halfblocksize
                N = self.blocksize
                self.t[d*N2+N2:d*N2+N] = self.h * np.arange(N2,N)
                if self.model.scalar():
                    self.phi[d*N2+N2:d*N2+N,:] = self.phi_[N2:,:]
                    self.m[d*N2+N2:d*N2+N,:] = self.m_[N2:,:]
                else:
                    self.phi[d*N2+N2:d*N2+N,:] = self.phi_[N2:,:].reshape(N2,self.mdimen,self.dim,self.dim)
                    self.m[d*N2+N2:d*N2+N,:] = self.m_[N2:,:].reshape(N2,self.mdimen,self.dim,self.dim)
            self.solved = d
        else:
            N2 = self.halfblocksize
            N = self.blocksize
            self.phi_[N2:,:] = self.phi[d*N2+N2:d*N2+N,:].reshape(N2,-1)
            self.m_[N2:,:] = self.m[d*N2+N2:d*N2+N,:].reshape(N2,-1)

    def save (self, file):
        """Save the correlator data to the given file.

        The data will be stored in the mcspy h5 file format.

        Parameters
        ----------
        file : str
            Filename.
        """
        if not self.store or not self.solved > -2:
            return # should throw an exception
        with h5py.File(file, 'w') as f:
            self.h5save (f)
            self.model.h5save (f)
    def h5save (self, base):
        grp = base.create_group("correlator")
        grp.attrs['type'] = self.type()
        grp2 = grp.create_group("time_domain")
        grp2.create_dataset("t",data=self.t)
        grp2.create_dataset("phi",data=self.phi)
        grp2.create_dataset("m",data=self.m)
        grp2.attrs['solver'] = 'moment'
        grp2.attrs['h0'] = self.h0
        grp2.attrs['blocks'] = self.blocks
        grp2.attrs['solved_blocks'] = self.solved
        grp2.attrs['blocksize'] = self.blocksize
        grp2.attrs['maxiter'] = self.maxiter
        grp2.attrs['accuracy'] = self.accuracy
    def type (self):
        return 'phi'
    @staticmethod
    def load (file):
        """Load correlator from h5 file.

        This is a static method that returns a newly created
        correlator object holding data read from disk. It can be
        used as a base correlator object for the calculation of
        models that need the loaded data as a reference.
        """
        with h5py.File(file, 'r') as f:
            attrs = f['correlator/time_domain'].attrs
            newself = correlator(
                blocksize=attrs['blocksize'], h=attrs['h0'],
                blocks=attrs['blocks'], maxiter=attrs['maxiter'],
                accuracy=attrs['accuracy'], model = loaded_model(f))
            newself.t = np.array(f['correlator/time_domain/t'])
            newself.phi = np.array(f['correlator/time_domain/phi'])
            newself.m = np.array(f['correlator/time_domain/m'])
            newself.store = True
            newself.solved = attrs['solved_blocks']
        return newself

@njit
def _msd_solve_block (istart, iend, h, nutmp, phi, m, dPhi, dM, kernel, maxiter, accuracy, calc_moments):
    A = dM[1] + 1.5*nutmp

    for i in range(istart,iend):
        kernel (m[i], None, i, h*i)

        ibar = i//2
        C = (m[i]-m[i-1])*dPhi[1] - phi[i-1]*dM[1]
        for k in range(2,ibar+1):
            C += (m[i-k+1] - m[i-k]) * dPhi[k]
            C += (phi[i-k+1] - phi[i-k]) * dM[k]
        if (i-ibar > ibar):
            C += (phi[i-k+1] - phi[i-k]) * dM[k]
        C += m[i-ibar] * phi[ibar]
        C += (-2.0*phi[i-1] + 0.5*phi[i-2]) * nutmp
        C += -6.0
        C = C/A

        #kernel (m[i], None, i, h*i)
        phi[i] = - C
        if calc_moments:
            dPhi[i] = 0.5 * (phi[i-1] + phi[i])
            dM[i] = 0.5 * (m[i-1] + m[i])


class mean_squared_displacement (correlator):
    """Solver for the mean-squared displacement.
    """
    def initial_values (self, imax=50):
        iend = imax
        if (iend >= self.halfblocksize): iend = self.halfblocksize-1
        for i in range(iend):
            t = i*self.h0
            self.phi_[i] = np.ones(self.mdimen)*6.*t/self.model.Bq()
            self.jit_kernel (self.m_[i], None, i, t)
        for i in range(1,iend):
            self.dPhi_[i] = 0.5 * (self.phi_[i-1] + self.phi_[i])
            self.dM_[i] = 0.5 * (self.m_[i-1] + self.m_[i])
        self.dPhi_[iend] = self.phi_[iend-1]
        self.dM_[iend] = self.m_[iend-1]
        self.iend = iend

    def solve_block (self, istart, iend):
        _msd_solve_block (istart, iend, self.h, self.model.Bq()/self.h, self.phi_, self.m_, self.dPhi_, self.dM_, self.jit_kernel, self.maxiter, self.accuracy, (istart<self.blocksize//2))

    def type (self):
        return 'MSD'


@njit
def _ngp_solve_block (istart, iend, h, nutmp, phi, m, dPhi, dM, kernel, maxiter, accuracy, calc_moments):
    A = dM[1] + 1.5*nutmp

    for i in range(istart,iend):
        kernel (m[i], None, i, h*i)

        ibar = i//2
        # this is 2-dim, calculates m*a and m2*dr2
        # where a is (1+a2)dr2^2
        # we assume phi[i,1] to be pre-filled
        C = (m[i]-m[i-1])*dPhi[1] - phi[i-1]*dM[1]
        C[1] += phi[i,1]*dM[1,1]
        for k in range(2,ibar+1):
            C += (m[i-k+1] - m[i-k]) * dPhi[k]
            C += (phi[i-k+1] - phi[i-k]) * dM[k]
        if (i-ibar > ibar):
            C += (phi[i-k+1] - phi[i-k]) * dM[k]
        C += m[i-ibar] * phi[ibar]
        C[0] += (-2.0*phi[i-1,0] + 0.5*phi[i-2,0]) * nutmp[0]
        C[0] += -12.0 * phi[i,1] - 6.0 * C[1]
        C = C/A

        #kernel (m[i], None, i, h*i)
        phi[i,0] = - C[0]
        if calc_moments:
            dPhi[i] = 0.5 * (phi[i-1] + phi[i])
            dM[i] = 0.5 * (m[i-1] + m[i])

class non_gaussian_parameter (correlator):
    """Solver for the non-Gaussian parameter.
    """

    def initial_values (self, imax=50):
        iend = imax
        if (iend >= self.halfblocksize): iend = self.halfblocksize-1
        for i in range(iend):
            t = i*self.h0
            self.phi_[i] = np.zeros(self.mdimen)
            self.phi_[i,1] = self.model.phi2()[i,0]
            self.jit_kernel (self.m_[i], None, i, t)
        for i in range(1,iend):
            self.dPhi_[i] = 0.5 * (self.phi_[i-1] + self.phi_[i])
            self.dM_[i] = 0.5 * (self.m_[i-1] + self.m_[i])
        self.dPhi_[iend] = self.phi_[iend-1]
        self.dM_[iend] = self.m_[iend-1]
        self.iend = iend

    def solve_block (self, istart, iend):
        r"""
        Note
        ----
        This solves for :math:`a(t)=(1+\alpha_2(t))\delta r^2(t)^2`
        in component 0. Component 1 of phi will be filled with the MSD.
        """
        self.phi_[istart:iend,1] = self.model.phi2()[istart:iend,0]
        _ngp_solve_block (istart, iend, self.h, self.model.Bq()/self.h, self.phi_, self.m_, self.dPhi_, self.dM_, self.jit_kernel, self.maxiter, self.accuracy, (istart<self.blocksize//2))

    def type (self):
        return 'NGP'
