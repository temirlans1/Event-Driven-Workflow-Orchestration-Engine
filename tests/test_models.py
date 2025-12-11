from orchestrator.models import DAGNode, Workflow


def test_dag_node_basic_init():
    node = DAGNode(id="n1", handler="noop")
    assert node.id == "n1"
    assert node.handler == "noop"
    assert node.dependencies == []
    assert node.config == {}


def test_dag_node_with_all_fields():
    node = DAGNode(id='n1', handler='noop', dependencies=['a'], config={'x': 1})
    assert node.dependencies == ['a']
    assert node.config == {'x': 1}


def test_workflow_init():
    nodes = [DAGNode(id='a', handler='noop')]
    wf = Workflow(execution_id='id123', name='WF', nodes=nodes)
    assert wf.execution_id == 'id123'
    assert wf.nodes[0].id == 'a'
