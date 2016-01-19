import GPflow
import tensorflow as tf
import numpy as np
import unittest


class TestKernSymmetry(unittest.TestCase):
    def setUp(self):
        self.kernels = GPflow.kernels.Stationary.__subclasses__() + [GPflow.kernels.Bias, GPflow.kernels.Linear]
        self.rng = np.random.RandomState()

    def test_1d(self):
        kernels = [K(1) for K in self.kernels]
        x_free = tf.placeholder('float64')
        [k.make_tf_array(x_free) for k in kernels]
        X = tf.placeholder('float64')
        X_data = self.rng.randn(10,1)
        for k in kernels:
            with k.tf_mode():
                Errors = tf.Session().run(
                            k.K(X) - k.K(X, X),
                            feed_dict={x_free:k.get_free_state(), X:X_data})
                self.failUnless(np.allclose(Errors, 0))


    def test_5d(self):
        kernels = [K(5) for K in self.kernels]
        x_free = tf.placeholder('float64')
        [k.make_tf_array(x_free) for k in kernels]
        X = tf.placeholder('float64')
        X_data = self.rng.randn(10,5)
        for k in kernels:
            with k.tf_mode():
                Errors = tf.Session().run(
                            k.K(X) - k.K(X, X),
                            feed_dict={x_free:k.get_free_state(), X:X_data})
                self.failUnless(np.allclose(Errors, 0))




class TestAdd(unittest.TestCase):
    """
    add a rbf and linear kernel, make sure the result is the same as adding
    the result of the kernels separaetely
    """
    def setUp(self):
        self.rbf = GPflow.kernels.RBF(1)
        self.lin = GPflow.kernels.Linear(1)
        self.k = GPflow.kernels.RBF(1) + GPflow.kernels.Linear(1)
        self.rng = np.random.RandomState(0)

    def test_sym(self):
        x_free = tf.placeholder('float64')
        [k.make_tf_array(x_free) for k in self.rbf, self.lin, self.k]
        X = tf.placeholder('float64')
        X_data = self.rng.randn(10,1)
        for k in [self.rbf, self.lin, self.k]:
            with k.tf_mode():
                k._K = tf.Session().run(k.K(X), feed_dict={x_free:k.get_free_state(), X:X_data})

        self.failUnless(np.allclose(self.rbf._K + self.lin._K, self.k._K))

    def test_asym(self):
        x_free = tf.placeholder('float64')
        [k.make_tf_array(x_free) for k in self.rbf, self.lin, self.k]
        X = tf.placeholder('float64')
        Z = tf.placeholder('float64')
        X_data = self.rng.randn(10,1)
        Z_data = self.rng.randn(12,1)
        for k in [self.rbf, self.lin, self.k]:
            with k.tf_mode():
                k._K = tf.Session().run(k.K(X), feed_dict={x_free:k.get_free_state(), X:X_data, Z:Z_data})

        self.failUnless(np.allclose(self.rbf._K + self.lin._K, self.k._K))





class TestWhite(unittest.TestCase):
    """the white kernel should not give the same result when called with k(X) and k(X, X)"""
    def setUp(self):
        self.k = GPflow.kernels.White(1)
        self.rng = np.random.RandomState(0)

    def test(self):
        x_free = tf.placeholder('float64')
        self.k.make_tf_array(x_free)
        X = tf.placeholder('float64')
        X_data = self.rng.randn(10,1)
        with self.k.tf_mode():
            K_sym = tf.Session().run(self.k.K(X), feed_dict={x_free:self.k.get_free_state(), X:X_data})
            K_asym = tf.Session().run(self.k.K(X, X), feed_dict={x_free:self.k.get_free_state(), X:X_data})

        self.failIf(np.allclose(K_sym, K_asym))


class TestSlice(unittest.TestCase):
    """
    make sure the results of a sliced kernel is the ame as an unsliced kernel with correctly sliced data...
    """
    def setUp(self):
        self.rng = np.random.RandomState(0)
        self.k1 = GPflow.kernels.RBF(1, active_dims=[0])
        self.k2 = GPflow.kernels.RBF(1, active_dims=[1])
        self.k3 = GPflow.kernels.RBF(1)
        self.X = tf.placeholder('float64')

        #make kernel functions in python
        self.x_free = tf.placeholder('float64')

    def test(self):
        X = self.rng.randn(20,2)

        with self.k1.tf_mode():
            with self.k2.tf_mode():
                with self.k3.tf_mode():
                    self.k1.make_tf_array(self.x_free)
                    self.k2.make_tf_array(self.x_free)
                    self.k3.make_tf_array(self.x_free)
                    K1 = tf.Session().run(self.k1.K(self.X), feed_dict={self.X:X, self.x_free:np.ones(2)})
                    K2 = tf.Session().run(self.k2.K(self.X), feed_dict={self.X:X, self.x_free:np.ones(2)})
                    K3 = tf.Session().run(self.k3.K(self.X), feed_dict={self.X:X[:,:1], self.x_free:np.ones(2)})
                    K4 = tf.Session().run(self.k3.K(self.X), feed_dict={self.X:X[:,1:], self.x_free:np.ones(2)})
        self.failUnless(np.allclose(K1, K3))
        self.failUnless(np.allclose(K2, K4))


        





if __name__ == "__main__":
    unittest.main()

