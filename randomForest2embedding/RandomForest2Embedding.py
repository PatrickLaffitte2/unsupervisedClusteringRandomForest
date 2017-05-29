from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import division

import numpy as np
import scipy.sparse as sp
from sklearn.ensemble.forest import BaseForest
from sklearn.tree import DecisionTreeClassifier
from sklearn.utils import check_random_state, check_array
from sklearn.preprocessing import OneHotEncoder
from sklearn import manifold


def bootstrap_sample_column(X, n_samples=None, random_state=12345):
    """bootstrap_sample_column

    Bootstrap sample the column of a dataset.

    Parameters
    ----------
    X : np.ndarray (n_samples,)
        Column to bootstrap

    n_samples : int
        Number of samples to generate. If `None` then generate
        a bootstrap of size of `X`.

    random_state : int
        Seed to the random number generator.

    Returns
    -------
    np.ndarray (n_samples,):
        The bootstrapped column.
    """
    random_state = check_random_state(random_state)
    if n_samples is None:
        n_samples = X.shape[0]

    return random_state.choice(X, size=n_samples, replace=True)


def uniform_sample_column(X, n_samples=None, random_state=12345):
    """uniform_sample_column

    Sample a column uniformly between its minimum and maximum value.

    Parameters
    ----------
    X : np.ndarray (n_samples,)
        Column to sample.

    n_samples : int
        Number of samples to generate. If `None` then generate
        a bootstrap of size of `X`.

    random_state : int
        Seed to the random number generator.

    Returns
    -------
    np.ndarray (n_samples,):
        Uniformly sampled column.
    """
    random_state = check_random_state(random_state)
    if n_samples is None:
        n_samples = X.shape[0]

    min_X, max_X = np.min(X), np.max(X)
    return random_state.uniform(min_X, max_X, size=n_samples)


def generate_synthetic_features(X, method='bootstrap', random_state=12345):
    """generate_synthetic_features

    Generate a synthetic dataset based on the random distribution of `X`.

    Parameters
    ----------
    X : np.ndarray (n_samples, n_features)
        with X distribution is used to generate the
        synthetic dataset.

    method :'bootstrap' or  'uniform' 
        Method to use to generate the synthetic dataset.
        `bootstrap` each column with replacement using random choice for X
        `uniform` generates a new column uniformly sampled between the minimum and
        maximum value of each column.

    random_state : int
        Seed to the random number generator.

    Returns
    -------
    synth_X : np.ndarray (n_samples, n_features)
        The synthetic dataset.
    """
    
    random_state = check_random_state(random_state)
    n_features = int(X.shape[1])
    synth_X = np.empty_like(X)
    for column in range(n_features):
        if method == 'bootstrap':
            synth_X[:, column] = bootstrap_sample_column(
                X[:, column], random_state=random_state)
        elif method == 'uniform':
            synth_X[:, column] = uniform_sample_column(
                X[:, column], random_state=random_state)
        else:
            raise ValueError('method must be either `bootstrap` or `uniform`.')

    return synth_X


def generate_discriminative_dataset(X, method='bootstrap', random_state=1234):
    """generate_discriminative_dataset.

    Generate a synthetic dataset based on the empirical distribution
    of `X`. A target column will be returned that is 0 if the row is
    from the real distribution, and 1 if the row is synthetic. The
    number of synthetic rows generated is equal to the number of rows
    in the original dataset.

    Parameters
    ----------
    X : np.ndarray (n_samples, n_features)
        Dataset whose empirical distribution is used to generate the
        synthetic dataset.

    method : str {'bootstrap', 'uniform'}
        Method to use to generate the synthetic dataset. `bootstrap`
        samples each column with replacement. `uniform` generates
        a new column uniformly sampled between the minimum and
        maximum value of each column.

    random_state : int
        Seed to the random number generator.

    Returns
    -------
    X_ : np.ndarray (2 * n_samples, n_features)
        Feature array for the synthetic dataset. The rows
        are randomly shuffled, so synthetic and actual samples should
        be intermixed.

    y_ : np.ndarray (2 * n_samples)
        Target column indicating whether the row is from the actual
        dataset (0) or synthetic (1).
    """
    random_state = check_random_state(random_state)
    n_samples = int(X.shape[0])

    synth_X = generate_synthetic_features(
        X, method=method, random_state=random_state)
    X_ = np.vstack((X, synth_X))
    y_ = np.concatenate((np.ones(n_samples), np.zeros(n_samples)))

    permutation_indices = random_state.permutation(np.arange(X_.shape[0]))
    X_ = X_[permutation_indices, :]
    y_ = y_[permutation_indices]

    return X_, y_


def calcul_embedding (nodes, n_components = 2) :
    """
    takes array =  nodes 1=1 if used 0 not for each row
    and using hamming metric return a projection of data in n_components dimensions
    using manifold.TSNE
    
    warning : n_components > 2 is very very very slow
    """
    projecteur = manifold.TSNE(n_components = n_components, random_state=12345, metric='hamming')
    return projecteur.fit_transform(nodes)


class RandomForest2Embedding(BaseForest):
    """Very similar to sklearn's RandomTreesEmbedding;
    however, the forest is trained as a discriminator.
    """
    def __init__(self,
                 n_estimators=10,
                 criterion='gini',
                 max_depth=5,
                 min_samples_split=2,
                 min_samples_leaf=1,
                 min_weight_fraction_leaf=0.,
                 max_features='auto',
                 max_leaf_nodes=None,
                 bootstrap=True,
                 method='bootstrap',
                 n_jobs=-1,
                 random_state=None,
                 verbose=0,
                 warm_start=False):
        super(RandomForest2Embedding, self).__init__(
                base_estimator=DecisionTreeClassifier(),
                n_estimators=n_estimators,
                estimator_params=("criterion", "max_depth", "min_samples_split",
                                  "min_samples_leaf", "min_weight_fraction_leaf",
                                  "max_features", "max_leaf_nodes",
                                  "random_state"),
                bootstrap=bootstrap,
                oob_score=False,
                n_jobs=n_jobs,
                random_state=random_state,
                verbose=verbose,
                warm_start=warm_start)

        self.criterion = criterion
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.min_weight_fraction_leaf = min_weight_fraction_leaf
        self.max_features = max_features
        self.max_leaf_nodes = max_leaf_nodes
        self.method = method

    def _set_oob_score(self, X, y):
        raise NotImplementedError("OOB score not supported")

    def fit(self, X, y=None, sample_weight=None):
        self.fit_transform(X, y, sample_weight=sample_weight)
        return self

    def fit_transform(self, X, y=None, sample_weight=None, n_components = 2 ):
        X = check_array(X, accept_sparse=['csc'], ensure_2d=False)

        if sp.issparse(X):
            # Pre-sort indices to avoid that each individual tree of the
            # ensemble sorts the indices.
            X.sort_indices()

        X_, y_ = generate_discriminative_dataset(X, method = self.method )

        super(RandomForest2Embedding, self).fit(X_, y_,
                                               sample_weight=sample_weight)
        
        return self.transform( X, n_components = n_components )
        

    def transform(self, X, n_components = 2):
        path, _ = super(RandomForest2Embedding, self).decision_path(X)
        return calcul_embedding (path.toarray(), n_components = n_components )
        
