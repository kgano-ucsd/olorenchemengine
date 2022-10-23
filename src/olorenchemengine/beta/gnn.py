import olorenchemengine as oce
from olorenchemengine.internal import *

class SuperGATModel_beta(oce.BaseLightningModule):

    """ SuperGAT is a network

    Parameters:
        dropout (float, optional): The dropout rate to use for the model. Default is 0.1.
        lr (float, optional): The learning rate to use for training. Default is 1e-4.
        optim (str, optional): The optimizer to use for training. Default is "adam".
    """

    @log_arguments
    def __init__(
        self,
        hidden_channels: int = 8,
        heads: int = 8,
        negative_slope: float = 0.2,
        dropout: float = 0.0,
        add_self_loops: bool = True,
        bias: bool = True,
        attention_type: str = "MX",
        neg_sample_ratio: float = 0.5,
        edge_sample_ratio: float = 1.0,
        is_undirected: bool = True,
        lr: float = 1e-4,
        optim: str = "adam",
    ):
        self.lr = lr
        super().__init__(optim=optim)
        
        self.hidden_channels = hidden_channels
        self.heads = heads
        self.negative_slope = negative_slope
        self.dropout = dropout
        self.add_self_loops = add_self_loops
        self.bias = bias
        self.attention_type = attention_type
        self.neg_sample_ratio = neg_sample_ratio
        self.edge_sample_ratio = edge_sample_ratio
        self.is_undirected = is_undirected
        self.lr = lr
        self.optim = optim

    def create(self, dimensions):
        from torch_geometric.nn import SuperGATConv

        self.conv1 = SuperGATConv(dimensions[0], self.hidden_channels, heads=self.heads,
                                  dropout=self.dropout, attention_type=self.attention_type,
                                  edge_sample_ratio=self.edge_sample_ratio, is_undirected=self.is_undirected,
                                  negative_slope=self.negative_slope, add_self_loops=self.add_self_loops,
                                  bias=self.bias, neg_sample_ratio=self.neg_sample_ratio)
        self.conv2 = SuperGATConv(self.hidden_channels*self.heads, 1, heads=self.heads,
                                  concat=False, dropout=self.dropout, attention_type=self.attention_type,
                                  edge_sample_ratio=self.edge_sample_ratio, is_undirected=self.is_undirected,
                                  negative_slope=self.negative_slope, add_self_loops=self.add_self_loops,
                                  bias=self.bias, neg_sample_ratio=self.neg_sample_ratio)

    def forward(self, batch):
        import torch.nn.functional as F
        from torch_geometric.nn import global_mean_pool

        if batch.x.is_cuda:
            dtype = torch.cuda.FloatTensor
        else:
            dtype = torch.FloatTensor
        x = batch.x.type(dtype)
        edge_index = batch.edge_index
        edge_attr = batch.edge_attr.type(dtype)

        del dtype
        
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = F.elu(self.conv1(x, edge_index))
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv2(x, edge_index)
        x = global_mean_pool(x, batch.batch)
        return F.log_softmax(x, dim=-1)
    
    ##########################
    # train, val, test, steps
    ##########################
    def training_step(self, batch, batch_idx):
        import torch.nn.functional as F
        from torch_geometric.nn import global_mean_pool

        if batch.x.is_cuda:
            dtype = torch.cuda.FloatTensor
        else:
            dtype = torch.FloatTensor
        x = batch.x.type(dtype)
        edge_index = batch.edge_index
        edge_attr = batch.edge_attr.type(dtype)

        del dtype
        
        x = F.dropout(x, p=0.6, training=self.training)
        x = F.elu(self.conv1(x, edge_index))
        att_loss = self.conv1.get_attention_loss()
        x = F.dropout(x, p=0.6, training=self.training)
        
        x = self.conv2(x, edge_index)
        att_loss += self.conv2.get_attention_loss()
        x = global_mean_pool(x, batch.batch)
        y_pred = F.log_softmax(x, dim=-1)
        
        loss = self.loss(y_pred, batch.y)
        loss += 4.0 * att_loss
        return loss
        
    def validation_step(self, batch, batch_idx):
        return self.training_step(batch, batch_idx)
    
    def test_step(self, batch, batch_idx):
        return self.training_step(batch, batch_idx)