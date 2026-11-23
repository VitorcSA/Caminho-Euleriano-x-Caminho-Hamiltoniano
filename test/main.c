#include "../C/lib/cJSON.h"
#include "../C/algorithm/graph.h"
#include "../C/algorithm/eulerian/hierholzer.h"
#include "../C/algorithm/hamiltonian/backtracking.h"
#include <stdio.h>
#include <stdlib.h>

int main(int argc,char** argv){
	FILE *json = fopen(argv[1],"r");
	fseek(json,0,SEEK_END);
	size_t size = ftell(json);
	rewind(json);
	char *buffer = malloc(sizeof(char)* (size+1));
	size_t read = fread(buffer,sizeof(char),size,json);
	buffer[read] = '\0';
	fclose(json);

	cJSON *root = cJSON_Parse(buffer);
	free(buffer);

	graph_t graph = graph_init();
	if (cJSON_IsArray(root)) {
		cJSON *vertex = NULL;
		cJSON_ArrayForEach(vertex,root){
			graph_add_vertex(&graph);
		}
		vertex = NULL;
		int i = 0;
		cJSON_ArrayForEach(vertex,root){
			cJSON *value = NULL;
			cJSON_ArrayForEach(value, vertex){
				if (cJSON_IsNumber(value)) {
					int number = value->valueint;
					if (number < i)
						continue;
					graph_add_edge(&graph,i,number);
				}
			}
			++i;
		}
		
	}
	graph_t copy = graph_init();
	graph_copy(&graph,&copy);

	list_t hierholzer_result = hierholzer(&graph);
	list_t backtracking_result = backtracking(&copy);


	list_print(&hierholzer_result);
	putchar('\n');
	list_print(&backtracking_result);
	putchar('\n');
}
