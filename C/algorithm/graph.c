#include "graph.h"
#include <stdlib.h>

int vertex_add_edge(vertex_t *vertex,int dest,int id){
	if (vertex == NULL)
		return -1;
	if (vertex->edges == NULL) {
		vertex->edges = malloc(sizeof(edge_t));
		if (vertex->edges == NULL)
			return -1;
		vertex->cnt = 1;
	}else {
		vertex->edges = realloc(vertex->edges,sizeof(edge_t) * (vertex->cnt+1));
		if (vertex->edges == NULL)
			return -1;
		++vertex->cnt;
	}
	vertex->edges[vertex->cnt-1] = edge_init(dest, id);
	return 0;
}

edge_t vertex_pop_edge(vertex_t *vertex){
	if (vertex == NULL)
		return (edge_t){-1};
	if (vertex->edges == NULL)
		return (edge_t){-1};

	edge_t edge = vertex->edges[--vertex->cnt];
	if (vertex->cnt <= 0) {
		free(vertex->edges);
		vertex->edges = NULL;
		return edge;
	}
	vertex->edges = realloc(vertex->edges,sizeof(edge_t) * (vertex->cnt));
	if (vertex->edges == NULL)
		return (edge_t){-1};

	return edge;
}

int graph_add_vertex(graph_t *graph){
	if (graph == NULL)
		return -1;
	if (graph->vertexes == NULL) {
		graph->vertexes = malloc(sizeof(vertex_t));
		if (graph->vertexes == NULL)
			return -1;
		graph->cnt = 1;
	}else {
		graph->vertexes = realloc(graph->vertexes,sizeof(vertex_t) * (graph->cnt+1));
		if (graph->vertexes == NULL)
			return -1;
		++graph->cnt;
	}

	graph->vertexes[graph->cnt-1] = vertex_init();
	return 0;
}

int graph_add_edge(graph_t *graph,int src,int dest){
	if (graph == NULL)
		return -1;
	if (graph->vertexes == NULL)
		return -1;
	if (graph->cnt <= src)
		return -1;
	if (graph->cnt <= dest)
		return -1;

	vertex_add_edge(&graph->vertexes[src],dest,graph->id_cnt);
	vertex_add_edge(&graph->vertexes[dest],src,graph->id_cnt);
	++graph->id_cnt;
	return 0;
}

void graph_free(graph_t graph){
	for (int i = 0;i < graph.cnt;++i) {
		free(graph.vertexes[i].edges);
	}
	free(graph.vertexes);
}

int graph_copy(graph_t* src,graph_t* copy){
	if (src == NULL || copy == NULL)
		return -1;
	for (int i = 0;i < src->cnt; ++i) {
		graph_add_vertex(copy);
	}
	for (int i = 0;i < src->cnt;++i) {
		for (int k = 0;k < src->vertexes[i].cnt; ++k) {
			if (src->vertexes[i].edges[k].vertex < i)
				continue;
			graph_add_edge(copy,i,src->vertexes[i].edges[k].vertex);
		}
	}
	return 0;
}
