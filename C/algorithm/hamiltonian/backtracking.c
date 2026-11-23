#include "../list.h"
#include "../graph.h"

int handle(graph_t* graph,int cur,list_t *path){
	if (graph->cnt == path->cnt) {
		return 0;
	}
	for(int i = 0; i < graph->vertexes[cur].cnt;++i){
		edge_t edge = graph->vertexes[cur].edges[i];
		if (list_is_in(path,edge.vertex))
			continue;
		list_append(path,edge.vertex);
		if (handle(graph,edge.vertex,path) < 0) {
			list_pop(path);
			continue;
		}
		return 0;
	}
	return -1;
}

list_t backtracking(graph_t* graph){
	list_t path = list_init();
	for(int i = 0;i < graph->cnt;++i){
		list_append(&path,i);
		if (handle(graph,i,&path) < 0){
			list_pop(&path);
			continue;
		}
		return path;
	}
	return list_init();
}

