"""Check ranking math and multi-label counting against transparent synthetic cases."""
import numpy as np
from atlas.geometry import neighborhood, original_neighbors, recall_at_ten, tag_overlap


def test_identical_vectors_keep_self_out_and_ties_in_id_order():
    v = np.ones((13,2),dtype=np.float32)
    ids,_ = neighborhood(v,12)
    assert ids[4,0] == 4 and ids[4,1:5].tolist() == [0,1,2,3]
    assert all(i not in ids[i,1:] for i in range(len(v)))


def test_original_neighbors_resolve_the_tenth_place_in_double_precision():
    # Nine exact matches leave one slot for two near-identical, representable float32 vectors.
    vectors=np.array([[1.,0.]]*10+[[.5,.5+2**-24],[.5,.5]],dtype=np.float32)
    ranked=original_neighbors(vectors)
    assert ranked[0].tolist()==[*range(1,10),11]
    assert all(i not in row for i,row in enumerate(ranked))


def test_umap_graph_and_recommendations_use_the_same_double_precision_ranks():
    from atlas.geometry import exact_graph
    vec=np.random.default_rng(42).standard_normal((35,8)).astype("float32")
    vec[4]=vec[2]
    ids,dist=exact_graph(vec,30)
    assert ids[:,0].tolist()==list(range(35)) and np.all(dist[:,0]==0)
    assert np.array_equal(ids[:,1:11],original_neighbors(vec))
    assert np.all(np.diff(dist,axis=1)>=0)


def test_independent_cpu_audit_preserves_order_at_a_tie_and_resumes(tmp_path):
    import runpy
    from atlas.io import file_hash, save_json
    from atlas.geometry import exact_graph
    vectors=np.ones((35,8),dtype=np.float32)
    vectors[17,3]+=2**-18
    path=tmp_path/"embeddings.npy";np.save(path,vectors)
    save_json(tmp_path/"embedding-info.json",{"vectors_sha256":file_hash(path)})
    audit=runpy.run_path("scripts/audit_release.py")["independent_neighbors"]
    expected=exact_graph(vectors,30)[0][:,1:11]
    np.testing.assert_array_equal(audit(tmp_path),expected)
    np.testing.assert_array_equal(audit(tmp_path),expected)


def test_reference_recall_and_multitag_pairs():
    xy = np.column_stack((np.arange(14),np.zeros(14)))
    d = abs(xy[:,0,None]-xy[:,0])
    np.fill_diagonal(d,np.inf)
    ref = np.argsort(d,axis=1,kind="stable")[:,:10]
    assert recall_at_ten(xy,ref) == 1
    assert tag_overlap(np.array([0,0,0,-1]),np.array([1,3,2,1])) == {"shared":2,"pairs":3,"fraction":2/3}


def test_independent_contingency_and_incidence_audit():
    import runpy
    from scipy.sparse import csr_matrix
    audit=runpy.run_path("scripts/audit_release.py")
    assert audit["contingency_ari"](np.array([0,0,1,1]),np.array([0,1,0,1]))==-.5
    tags=csr_matrix([[1,0],[1,1],[0,1],[1,0],[0,0]])
    assert audit["incidence_pairs"](np.array([0,0,0,-1,0]),tags)==(2,3)


def test_tree_retrieval_handles_many_coincident_points():
    from scipy.spatial.distance import cdist
    xy=np.random.default_rng(42).integers(0,4,(250,2))
    dist=cdist(xy,xy,"sqeuclidean");np.fill_diagonal(dist,np.inf)
    reference=np.argsort(dist,axis=1,kind="stable")[:,:10]
    assert recall_at_ten(xy,reference)==1
