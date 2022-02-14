# AUTOGENERATED! DO NOT EDIT! File to edit: 00_model.ipynb (unless otherwise specified).

__all__ = ['TemporalModelBase', 'TemporalModel']

# Cell
import torch.nn as nn

# Cell
class TemporalModelBase(nn.Module):
    """Do not instantiate this class. This class is for inheritance."""
    def __init__(self, num_joints_in, in_features, num_joints_out, filter_witdhs, causal, dropout, channels):
        super().__init__()
        # Validate filter (Kernals) witdh input.
        for fw in filter_witdhs:
            assert fw % 2 != 0, "Only odd filter widths are supported."

        self.num_joints_in = num_joints_in
        self.in_features = in_features
        self.num_joints_out = num_joints_out
        self.filter_widths = filter_witdhs

        self.drop = nn.Dropout(dropout)
        self.relu = nn.ReLU(inplace=True)

        self.pad = [filter_witdhs[0] // 2] # Pad size that makes output the same size as the input after going through filter.
        self.expand_bn = nn.BatchNorm1d(channels, momentum=0.1)
        self.shrink = nn.Conv1d(channels, num_joints_in*3, 1)

    def set_bn_momentum(self, momentum):
        """Sets the batch norm momentum and updates the corresponding layers where it is used."""
        self.expand_bn = momentum
        for bn in self.layers_bn:
            bn.momentum = momentum

    def receptive_field(self):
        """Return the total receptive field of this model as number of frames."""
        frames = 0
        for f in self.pad:
            frames += f
        return 1 + 2*frames

    def total_causal_shift(self):
        """
        Return the asymmetric offset for sequence padding.
        The returned value is typically 0 if causal convolutions are disabled,
        otherwise it is half the receptive field.
        Causal convolutions ensures the model cannot violate the ordering in which we model the temporal data.
        """
        frames = self.causal_shift[0]
        next_dilation = self.filter_widths[0]
        for i in range(1, len(self.filter_widths)):
            frames += self.causal_shift[i] * next_dilation
            next_dilation *=self.filter_widths[i]
        return frames


    def forward(self, x):
        assert len(x.shape) == 4 # [~, ~, num_joints_in, in_features]
        assert x.shape[-2] == self.num_joints_in
        assert x.shape[-1] == self.in_features

        sz = x.shape[0]
        x = x.view(x.shape[0], x.shape[1], -1)  # The size -1 is inferred from other dimensions.
        x = x.permute(0, 2, 1)

        x = self._forward_blocks(x) # Creates a forward block that subclasses implement.

        x = x.permute(0, 2, 1)
        x = x.view(sz, -1, self.num_joints_out, 3)

        return x

# Cell
class TemporalModel(TemporalModelBase):
    """3D pose estimation model with temporal convolutions."""

    def __init__(self, num_joints_in, in_features, num_joints_out, filter_widths, causal=False, dropout=0.25,
                 channels=1024,   dense=False):
        """
        Initialize the temporal model.

        Arguments:
        num_joints_in -- Number of input joints to our model.
        in_features -- Number of input features for each joint (typically 2 for 2D input).
        num_joints_out -- Number of output joints (can be different than input).
        filter_widths -- List of convolutions, which also determines the number of blocks and receptive field.
        causal -- Use causal convolutions instead of symmetric convolutions (for real-time applications).
        dropout -- Dropout probability.
        channels -- Number of convolution channels.
        dense -- Use regular dense convolutions instead of dilated convolutions (ablation experiment).
        """

        super().__init__(num_joints_in, in_features, num_joints_out, filter_widths, causal, dropout, channels)
        self.expand_conv = nn.Conv1d(num_joints_in*in_features, channels, filter_widths[0], bias=False)
        self.causal_shift = [ (filter_widths[0] // 2) if causal else 0 ]

        # Initialize and build layers and the stores them in a list.
        layers_conv = []
        layers_bn = []
        next_dilation = filter_widths[0]
        for i in range(1, len(filter_widths)):
            self.pad.append((filter_widths[i] - 1)*next_dilation // 2 )
            self.causal_shift.append((filter_widths[i]//2 * next_dilation) if causal else 0)

            layers_conv.append(nn.Conv1d(channels, channels, filter_widths[i] if not dense else (2*self.pad[-1] + 1),
                                         dilation=next_dilation if not dense else 1, bias=False))
            layers_bn.append(nn.BatchNorm1d(channels, momentum=0.1))
            layers_conv.append(nn.Conv1d(channels, channels, 1, dilation=1, bias=False))
            layers_bn.append(nn.BatchNorm1d(channels, momentum=0.1))

            next_dilation *= filter_widths[i]

        # Add the lists to a ModuleList that holds submodules visible by all Module methods.
        self.layers_conv = nn.ModuleList(layers_conv)
        self.layers_bn = nn.ModuleList(layers_bn)

    def _forward_blocks(self, x):
        x = self.drop(self.relu(self.expand_bn(self.expand_conv(x))))

        for i in range(len(self.pad) - 1):
            pad = self.pad[i+1]
            shift = self.causal_shift[i+1]
            res = x[:, :, pad + shift : x.shape[2] - pad + shift]
            x = self.drop(self.relu(self.layers_bn[2*i](self.layers_conv[2*i](x))))
            x = res + self.drop(self.relu(self.layers_bn[2*i + 1](self.layers_conv[2*i + 1](x))))

        # Fits the last layer so that it matches our output preferences.
        x = self.shrink(x)
        return x