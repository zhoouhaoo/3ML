import collections
import numpy as np

from threeML.classicMLE.joint_likelihood_set import JointLikelihoodSet
from threeML.data_list import DataList
from astromodels import clone_model


class GoodnessOfFit(object):

    def __init__(self, joint_likelihood_instance, like_data_frame):

        self._jl_instance = joint_likelihood_instance

        # Restore best fit and store the reference value for the likelihood
        self._jl_instance.restore_best_fit()

        self._reference_like = like_data_frame['-log(likelihood)']

    def by_mc(self, n_iterations=1000, continue_on_failure=False):
        """
        Compute goodness of fit by generating Monte Carlo datasets and fitting the current model on them. The fraction
        of synthetic datasets which have a value for the likelihood larger or equal to the observed one is a measure
        of the goodness of fit

        :param n_iterations: number of MC iterations to perform (default: 1000)
        :param continue_of_failure: whether to continue in the case a fit fails (False by default)
        :return: tuple (goodness of fit, frame with all results, frame with all likelihood values)
        """

        # Define the get_data and the get_model functions for the JointLikelihoodSet instance

        def get_data(id):

            # Generate a new data set for each plugin contained in the data list

            new_datas = []

            for dataset in self._jl_instance.data_list.values():

                new_data = dataset.get_simulated_dataset("%s_sim" % dataset.name)

                new_datas.append(new_data)

            new_data_list = DataList(*new_datas)

            return new_data_list

        def get_model(id):

            # Make a copy of the best fit model, so that we don't touch the original model during the fit, and we
            # also always restart from the best fit (instead of the last iteration)

            new_model = clone_model(self._jl_instance.likelihood_model)

            return new_model

        # Create the joint likelihood set
        jl_set = JointLikelihoodSet(get_data, get_model, n_iterations, iteration_name='simulation')

        # Use the same minimizer as in the joint likelihood object

        minimizer_name, algorithm = self._jl_instance.minimizer_in_use
        jl_set.set_minimizer(minimizer_name, algorithm)

        # Run the set
        data_frame, like_data_frame = jl_set.go(continue_on_failure=continue_on_failure)

        # Compute goodness of fit

        gof = collections.OrderedDict()

        # Total
        idx = like_data_frame['-log(likelihood)'][:, "total"].values >= self._reference_like['total']  # type: np.ndarray

        gof['total'] = np.sum(idx) / float(n_iterations)

        for dataset in self._jl_instance.data_list.values():

            sim_name = "%s_sim" % dataset.name

            idx = (like_data_frame['-log(likelihood)'][:, sim_name].values >= self._reference_like[dataset.name])

            gof[dataset.name] = np.sum(idx) / float(n_iterations)

        return gof, data_frame, like_data_frame