# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/01_loss.ipynb (unless otherwise specified).

__all__ = ['mpjpe', 'p_mpjpe', 'mean_velocity_error']

# Cell
def mpjpe(predicted, target):
    """
    Mean per-joint position error (i.e mean Euclidean distance),
    often referred to as "Protocol #1" in many papers.
    """

    assert predicted.shape == target.shape
    return torch.mean(torch.norm(predicted - target, dim=len(target.shape)-1))

# Cell
def p_mpjpe(predicted, target):
    """
    Pose error: MPJPE after rigid alignment (scale, rotation, and translation),
    often referred to as "Protocol #2" in many papers.
    """

    assert predicted.shape == target.shape

    muX = np.mean(target, axis=1, keepdims=True)
    muY = np.mean(predicted, axis=1, keepdims=True)
    # Centering around the mean for the prediction and target vector. Calculates the L2-norm and divides the data with it.
    X0 = target - muX
    Y0 = predicted - muY
    normX = np.sqrt(np.sum(X0**2, axis=(1, 2), keepdims=True))
    normY = np.sqrt(np.sum(Y0**2, axis=(1, 2), keepdims=True))
    X0 /= normX
    Y0 /= normY

    H = np.matmul(X0.transpose(0, 2, 1), Y0)
    U, s, Vt = np.linalg.svd(H)
    V = Vt.transpose(0, 2, 1)
    R = np.matmul(V, U.transpose(0, 2, 1))

    # Avoid improper rotations (reflections), i.e. rotations with det(R) = -1.
    sign_detR = np.sign(np.expand_dims(np.linalg.det(R), axis=1))
    V[:, :, -1] *= sign_detR
    s[:, -1] *= sign_detR.flatten()
    R = np.matmul(V, U.transpose(0, 2, 1)) # Rotation.

    tr = np.expand_dims(np.sum(s, axis=1, keepdims=True), axis=2)

    a = tr * normX / normY # Scale.
    t = muX - a*np.matmul(muY, R) # Translation.

    # Perform rigid transformation on the input.
    predicted_aligned = a*np.matmul(predicted, R) + t

    # Return MPJPE.
    return np.mean(np.linalg.norm(predicted_aligned - target, axis=len(target.shape)-1))


# Cell
def mean_velocity_error(predicted, target):
    """Mean per-joint velocity error (i.e. mean Euclidean distance of the 1st derivative)."""
    assert predicted.shape == target.shape

    velocity_predicted = np.diff(predicted, axis=0)
    velocity_target = np.diff(target, axis=0)

    return np.mean(np.linalg.norm(velocity_predicted - velocity_target, axis=len(target.shape)-1))