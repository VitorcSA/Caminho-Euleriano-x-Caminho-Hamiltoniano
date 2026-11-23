#ifndef GRAPH_H
#define GRAPH_H

typedef struct edge_t{
	int vertex;
	int id;
}edge_t;

#define edge_init(dest,id) (edge_t){dest,id};

typedef struct vertex_t{
	edge_t *edges;
	int cnt;
}vertex_t;

#define vertex_init() (vertex_t){0}

typedef struct graph_t{
	vertex_t* vertexes;
	int cnt;
	int id_cnt;
}graph_t;

#define graph_init() (graph_t){0}

void graph_free(graph_t graph);
edge_t vertex_pop_edge(vertex_t *vertex);
int vertex_add_edge(vertex_t *vertex,int dest,int id);
int graph_add_vertex(graph_t *graph);
int graph_add_edge(graph_t *graph,int src,int dest);
int graph_copy(graph_t* src,graph_t* copy);

#endif
