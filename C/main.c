#define _POSIX_C_SOURCE 199309L
#include <string.h>
#include <time.h>

#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include "lib/cJSON.h"
#include "algorithm/graph.h"
#include "algorithm/eulerian/hierholzer.h"
#include "algorithm/hamiltonian/backtracking.h"

int main(int argc,char** argv){
	FILE *json = fopen(argv[2],"r");
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
	cJSON_Delete(root);
	struct timespec start, end;

	if (strcmp(argv[1],"eulerian") == 0) {
		clock_gettime(CLOCK_MONOTONIC, &start);
		hierholzer(&graph);
		clock_gettime(CLOCK_MONOTONIC, &end);
		graph_free(graph);
	}else{
		clock_gettime(CLOCK_MONOTONIC, &start);
		backtracking(&graph);
		clock_gettime(CLOCK_MONOTONIC, &end);
		graph_free(graph);
	}
	double elapsed_ms = (end.tv_sec - start.tv_sec) * 1000.0 +
	                    (end.tv_nsec - start.tv_nsec) / 1e6;
	printf("%.6f\n", elapsed_ms);

	return 0;
}
