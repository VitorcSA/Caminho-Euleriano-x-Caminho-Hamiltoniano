#include <string.h>
#include "../list.h"
#include "../graph.h"

list_t hierholzer(graph_t *graph){
	int start = -1;
	for (int i = 0;i < graph->cnt;++i) {
		if (graph->vertexes[i].cnt > 0) {
			start = i;
			break;
		}
	}
	list_t stack = list_init();
	list_t circuit = list_init();
	int used[graph->id_cnt];
	memset(used,0,sizeof(int)*graph->id_cnt);

	if (start >= 0)
		list_append(&stack,start);

	for (int u = list_lookup(&stack);u >= 0;u = list_lookup(&stack)) {
		edge_t edge = vertex_pop_edge(&graph->vertexes[u]);
		if (edge.vertex < 0) {
			list_append(&circuit,list_pop(&stack));
			continue;
		}
		if (used[edge.id])
			continue;
		list_append(&stack,edge.vertex);
		used[edge.id] = 1;
	}
	return circuit;
}
