"""Check ranking math and multi-label counting against transparent synthetic cases."""
import numpy as np
from atlas.geometry import neighborhood, recall_at_ten, tag_overlap


def test_identical_vectors_keep_self_out_and_ties_in_id_order():
    v = np.ones((13,2),dtype=np.float32)
    ids,_ = neighborhood(v,12)
    assert ids[4,0] == 4 and ids[4,1:5].tolist() == [0,1,2,3]
    assert all(i not in ids[i,1:] for i in range(len(v)))


def test_reference_recall_and_multitag_pairs():
    xy = np.column_stack((np.arange(14),np.zeros(14)))
    d = abs(xy[:,0,None]-xy[:,0])
    np.fill_diagonal(d,np.inf)
    ref = np.argsort(d,axis=1,kind="stable")[:,:10]
    assert recall_at_ten(xy,ref) == 1
    assert tag_overlap(np.array([0,0,0,-1]),np.array([1,3,2,1])) == {"shared":2,"pairs":3,"fraction":2/3}
