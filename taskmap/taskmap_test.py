import asyncio
import pytest
import time

import taskmap


def a():
    return 5


def b(x):
    return x + 10


def c(x, y):
    return x + y + 20


def test_graph_ready():
    # given
    dependencies = {
        'a': {'b', 'c'},
        'b': {'c'},
        'c': set(),
    }

    funcs = {
        'a': a,
        'b': b,
        'c': c,
    }

    graph = taskmap.create_graph(funcs, dependencies)

    # when
    results = taskmap.get_ready_tasks(graph)

    # then
    assert results == {'c'}


def test_graph_ready_after_task_completed():
    # given
    dependencies = {
        'a': {'b', 'c'},
        'b': {'c'},
        'c': set(),
    }

    funcs = {
        'a': a,
        'b': b,
        'c': c,
    }

    graph = taskmap.create_graph(funcs, dependencies)
    ready = taskmap.get_ready_tasks(graph)

    # when
    for func in ready:
        taskmap.mark_as_done(graph, func)

    results = taskmap.get_ready_tasks(graph)

    # then
    assert results == {'b'}


def test_cyclic_dependency():
    # given
    dependencies = {
        'a': {'b'},
        'b': {'c'},
        'c': {'a'},
    }

    funcs = {
        'a': a,
        'b': b,
        'c': c,
    }

    # then
    with pytest.raises(ValueError):

        # when
        taskmap.create_graph(funcs, dependencies)


def test_absent_tasks():
    # given
    dependencies = {
        'a': {'b', 'c'},
    }

    funcs = {
        'a': a,
        'b': b,
        'c': c,
    }

    # then
    with pytest.raises(ValueError):

        # when
        taskmap.create_graph(funcs, dependencies)


def test_all_names_are_funcs():
    # given
    dependencies = {'d': ['a'], 'a': []}

    funcs = {'a': a, 'b': b, 'c': c}

    # then
    with pytest.raises(ValueError):

        # when
        taskmap.create_graph(funcs, dependencies)


def test_run_pass_args():
    # given
    dependencies = {
        'c': ['a', 'b'],
        'b': ['a'],
        'a': [],

    }

    funcs = {
        'a': a,
        'b': b,
        'c': c,
    }

    graph = taskmap.create_graph(funcs, dependencies)

    # when
    graph = taskmap.run(graph)

    # then
    assert graph.results == {'a': 5, 'b': 15, 'c': 40}


error = RuntimeError('some error')


def d():
    raise error


def test_error_handling():
    # given
    dependencies = {
        'c': ['d'],
        'd': [],
    }

    funcs = {
        'd': d,
        'c': c,
    }

    graph = taskmap.create_graph(funcs, dependencies)

    # when
    graph = taskmap.run_task(graph, 'd')

    # then
    expected = {
        'd': error,
        'c': 'Ancestor task d failed; task not run',
    }
    assert graph.results == expected


def test_get_all_children():
    # given
    # given
    dependencies = {
        'd': ['a'],
        'c': ['b'],
        'b': ['a'],
        'a': [],
    }

    funcs = {
        'a': a,
        'b': b,
        'c': c,
        'd': d,
    }

    graph = taskmap.create_graph(funcs, dependencies)

    # when
    a_children = taskmap.get_all_children(graph, 'a')
    b_children = taskmap.get_all_children(graph, 'b')
    c_children = taskmap.get_all_children(graph, 'c')

    # then
    assert a_children == {'b', 'c', 'd'}
    assert b_children == {'c'}
    assert c_children == set()


def long_task():
    time.sleep(.02)
    return 5


def test_run_parallel():
    # given
    dependencies = {
        'c': ['long_task', 'b'],
        'b': ['long_task'],
        'long_task': [],

    }

    funcs = {
        'long_task': long_task,
        'b': b,
        'c': c,
    }

    graph = taskmap.create_graph(funcs, dependencies)

    # when
    graph = taskmap.run_parallel(graph)

    # then
    assert graph.results == {'long_task': 5, 'b': 15, 'c': 40}


async def ab(x):
    return x + 10


async def ac(x, y):
    return x + y + 20


async def along_task():
    await asyncio.sleep(.02)
    return 5


def test_run_async():
    # given
    dependencies = {
        'ac': ['along_task', 'ab'],
        'ab': ['along_task'],
        'along_task': [],

    }

    funcs = {
        'along_task': along_task,
        'ab': ab,
        'ac': ac,
    }

    graph = taskmap.create_graph(funcs, dependencies)

    # when
    graph = taskmap.run_async(graph)

    # then
    assert graph.results == {'along_task': 5, 'ab': 15, 'ac': 40}


def test_run_parllel_async():
    # given
    dependencies = {
        'ac': ['along_task', 'ab'],
        'ab': ['along_task'],
        'along_task': [],

    }

    funcs = {
        'along_task': along_task,
        'ab': ab,
        'ac': ac,
    }

    graph = taskmap.create_graph(funcs, dependencies)

    # when
    graph = taskmap.run_parallel_async(graph)

    # then
    assert graph.results == {'along_task': 5, 'ab': 15, 'ac': 40}


async def x():
    await asyncio.sleep(.5)
    return 5


async def y():
    await asyncio.sleep(.5)
    return 5


def test_async_speed():
    # given
    funcs = {'x': x, 'y': y}
    dependencies = {'x': [], 'y': []}
    graph = taskmap.create_graph(funcs, dependencies)

    # when
    start = time.time()
    taskmap.run_async(graph)
    end = time.time()

    # then
    assert end - start < 1


def v():
    time.sleep(.5)
    return 5


def u():
    time.sleep(.5)
    return 5


def test_parallel_speed():
    # given
    funcs = {'x': u, 'y': v}
    dependencies = {'x': [], 'y': []}
    graph = taskmap.create_graph(funcs, dependencies)

    # when
    start = time.time()
    taskmap.run_parallel(graph)
    end = time.time()

    # then
    assert end - start < 1


async def r():
    await asyncio.sleep(1)


async def t():
    await asyncio.sleep(1)


async def w():
    time.sleep(1)


async def p():
    time.sleep(1)


def test_async_parallel_speed():
    # given
    funcs = {'r': r, 't': t, 'w': w, 'p': p}
    dependencies = {'r': [], 't': [], 'w': [], 'p': []}
    graph = taskmap.create_graph(funcs, dependencies, io_bound=['r', 't'])

    # when
    start = time.time()
    taskmap.run_parallel_async(graph, ncores=2)
    end = time.time()

    # then
    assert end - start < 2
