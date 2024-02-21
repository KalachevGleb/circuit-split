def get_children(graph: ig.GraphBase, turn2vertex_id, t2v_id_size_iter: int):
    previous_t2v_id_size_iter = t2v_id_size_iter
        
    for vertex_id in turn2vertex_id[:previous_t2v_id_size_iter]:

        vertex = graph.vs[vertex_id]
        children = vertex.neighbors(mode='out')

        for child in children:
            if child.index in turn2vertex_id[:t2v_id_size_iter]:
                continue

            parents = child.neighbors(mode='in')
            
            good = True
            for parent in parents:
                if parent.index not in turn2vertex_id[:previous_t2v_id_size_iter]:
                    good = False

                    break
            
            if good:
                turn2vertex_id[t2v_id_size_iter] = child.index
                t2v_id_size_iter += 1

    return t2v_id_size_iter 


def reorder(graph):
    turn2vertex_id = [vertex.index for vertex in graph.vs if len(vertex.neighbors(mode='in')) == 0]
    t2v_id_size_iter = len(turn2vertex_id)
    turn2vertex_id += [-1] * (len(graph.vs) - t2v_id_size_iter)
    turn2vertex_id = np.array(turn2vertex_id, dtype=int)

    time_per_thread = [0] * THREAD_COUNT

    pbar = tqdm(total=len(turn2vertex_id))
    while t2v_id_size_iter != len(graph.vs):

        #print(t2v_id_size_iter, 'of', len(graph.vs))

        proposed_t2v_id_size_iter = get_children(
            graph=graph,
            turn2vertex_id=turn2vertex_id,
            t2v_id_size_iter=t2v_id_size_iter
        )
        
        proposed_as_added = turn2vertex_id[t2v_id_size_iter:t2v_id_size_iter + proposed_t2v_id_size_iter]

        dreamed_t2v_size_iter = get_children(
            graph=graph,
            turn2vertex_id=turn2vertex_id,
            t2v_id_size_iter=proposed_t2v_id_size_iter
        )

        dreamed_as_added = turn2vertex_id[proposed_t2v_id_size_iter:proposed_t2v_id_size_iter + dreamed_t2v_size_iter]








        

        proposed_vertex_dep = [0 for i in range(len(proposed_as_added))]
        for i in range(len(proposed_as_added)):
            
            vertex = graph.vs[proposed_as_added[i]]

            for child in vertex.neighbors(mode='out'):
                if child in dreamed_as_added:
                    proposed_vertex_dep[i] += 1










        thread_costs = [0] * THREAD_COUNT
        thread_queue = [[]] * THREAD_COUNT
        for vertex_id in proposed_as_added:
            vertex = graph.vs[vertex_id]

            thread = vertex['p']

            thread_queue[thread].append(vertex_id)
            
            for parent in vertex.neighbors(mode='in'):
                thread_costs[thread] += parent['w']

        goal = np.amin(thread_costs)

        
        
        
        
        
        for thread in range(THREAD_COUNT):
            queue = thread_queue[thread]

            indices = [proposed_as_added.tolist().index(x) for x in queue]

            deps = [proposed_vertex_dep[x] for x in indices]

            queue = sorted(queue, key=lambda x: deps[queue.index(x)])

            while sum(deps) > goal:
                deps.pop()
                queue.pop()

            thread_queue[thread] = queue

        







        
        
        
        final_queue = []

        for q in thread_queue:
            final_queue += q





       

        

        # skip_costs = [0] * THREAD_COUNT
        # not_skipped = []
        # for vertex_id in added:
        #     vertex = graph.vs[vertex_id]

        #     thread = vertex['p']
        #     if skip_costs[thread] > goal:
        #         continue
            
        #     not_skipped.append(vertex_id)
            
        #     for parent in vertex.neighbors(mode='in'):
        #         if thread == parent['p']:
        #             skip_costs[thread] += parent['w']
        #         else:
        #             skip_costs[thread] += LOSS * parent['w'] + LOSS2










        previous_t2v_id_size_iter = t2v_id_size_iter
        print()
        print(final_queue)
        print(turn2vertex_id[t2v_id_size_iter:t2v_id_size_iter + len(final_queue)])
        turn2vertex_id[t2v_id_size_iter:t2v_id_size_iter + len(final_queue)] = final_queue
        t2v_id_size_iter = t2v_id_size_iter + len(final_queue)

        pbar.update(t2v_id_size_iter - previous_t2v_id_size_iter)








        # for vertex_id in turn2vertex_id[:t2v_id_size_iter]:
        #     vertex = graph.vs[vertex_id]

        #     children = vertex.neighbors(mode='out')

        #     for child in children:
        #         if child['p'] == vertex['p']:
        #             continue

        #         if child.index not in turn2vertex_id[:t2v_id_size_iter]:
        #             turn2vertex_id[t2v_id_size_iter] = child.index
        #             t2v_id_size_iter += 1

    pbar.close()

    return turn2vertex_id.tolist()