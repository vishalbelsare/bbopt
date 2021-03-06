"""
Example of using BBopt to tune Keras hyperparameters. Uses the full
BBopt API instead of just the boilerplate and implements its own
(very basic) command-line interface instead of using BBopt's. By
implementing our own optimization loop, we are able to avoid the
overhead of running the entire file multiple times, which is what
the BBopt command line does.

To run this example, just run:
    > python ./keras_example.py
"""

# Imports:
import sys
import os
from argparse import ArgumentParser
from pprint import pprint

import numpy as np

from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import SGD
from keras.utils import to_categorical
from keras.regularizers import l1_l2


# BBopt setup:
from bbopt import BlackBoxOptimizer
bb = BlackBoxOptimizer(file=__file__)


# Load raw data:
data_folder = os.path.join(os.path.dirname(__file__), "data")
house_votes = np.loadtxt(
    os.path.join(data_folder, "house_votes.csv"),
    dtype=str,
    delimiter=",",
)


# Process data into X and y:
def type_error(msg):
    """Raise a TypeError with the given message."""
    raise TypeError(msg)

X = np.vectorize(lambda x:
    1 if x == "y"
    else -1 if x == "n"
    else 0 if x == "?"
    else type_error("unknown vote {}".format(x))
)(house_votes[:,1:])

y = to_categorical(np.vectorize(lambda x:
    1 if x == "democrat"
    else 0 if x == "republican"
    else type_error("unknown party {}".format(x))
)(house_votes[:,0]))


# Split data into training, validation, and testing:
train_split = int(.6*len(X))
validate_split = train_split + int(.2*len(X))

X_train, X_validate, X_test = X[:train_split], X[train_split:validate_split], X[validate_split:]
y_train, y_validate, y_test = y[:train_split], y[train_split:validate_split], y[validate_split:]


def run_trial():
    """Run one trial of hyperparameter optimization."""
    # Start BBopt:
    bb.run(backend="scikit-optimize")

    # Create model:
    model = Sequential([
        Dense(
            units=bb.randint("hidden neurons", 1, 15, guess=2),
            input_dim=len(X_train[0]),
            kernel_regularizer=l1_l2(
                l1=bb.uniform("l1", 0, 0.1, guess=0.005),
                l2=bb.uniform("l2", 0, 0.1, guess=0.05),
            ),
            activation="relu",
        ),
        Dense(
            units=2,
            activation="softmax",
        ),
    ])

    # Compile model:
    model.compile(
        loss="categorical_crossentropy",
        optimizer=SGD(
            lr=bb.uniform("learning rate", 0, 0.5, guess=0.15),
            decay=bb.uniform("decay", 0, 0.01, guess=0.0005),
            momentum=bb.uniform("momentum", 0, 1, guess=0.5),
            nesterov=bool(bb.getrandbits("nesterov", 1, guess=1)),
        ),
        metrics=["accuracy"],
    )

    # Train model:
    train_history = model.fit(
        X_train,
        y_train,
        epochs=50,
        batch_size=bb.randint("batch size", 1, 32, guess=16),
        verbose=0,
    )

    train_loss, train_acc = train_history.history["loss"][-1], train_history.history["acc"][-1]

    validation_loss, validation_acc = model.evaluate(X_validate, y_validate, verbose=0)

    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)

    # Store BBopt information:
    bb.remember({
        "training loss": train_loss,
        "training accuracy": train_acc,
        "validation loss": validation_loss,
        "validation accuracy": validation_acc,
        "test loss": test_loss,
        "test accuracy": test_acc,
    })

    bb.minimize(validation_loss)


# Setup command-line interface:
parser = ArgumentParser()
parser.add_argument(
    "-n", "--num-trials",
    metavar="trials",
    type=int,
    default=20,
    help="number of trials to run (defaults to 20)",
)


# Main loop:
if __name__ == "__main__":
    args = parser.parse_args()

    for i in range(args.num_trials):
        run_trial()
        print("Summary of run {}/{}:".format(i+1, args.num_trials))
        pprint(bb.get_current_run())
        print()

    print("\nSummary of best run:")
    pprint(bb.get_optimal_run())
