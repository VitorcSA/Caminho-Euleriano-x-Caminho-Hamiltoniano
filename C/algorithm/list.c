#include "list.h"
#include "stdlib.h"
#include <stdio.h>

int list_append(list_t* list,int value){
	if (list == NULL)
		return -1;
	if (list->array == NULL) {
		list->array = malloc(sizeof(int));
		++list->cnt;
	}else {
		list->array = realloc(list->array, sizeof(int) * (list->cnt+1));
		++list->cnt;
	}
	
	list->array[list->cnt-1] = value;
	return 0;
}

int list_pop(list_t* list){
	if (list == NULL)
		return -1;
	if (list->array == NULL)
		return -1;
	int value = list->array[--list->cnt];
	if (list->cnt <= 0) {
		free(list->array);
		list->array = NULL;
		return value;
	}
	list->array = realloc(list->array,sizeof(int) * list->cnt);
	if (list->array == NULL) {
		return -1;
	}
	return value;
}

int list_lookup(list_t* list){
	if (list == NULL)
		return -1;
	if (list->array == NULL)
		return -1;
	
	return list->array[list->cnt-1];
}

int list_remove(list_t* list,int value){

}

_Bool list_is_in(list_t* list,int value){
	if (list == NULL)
		return 0;
	for (int i = 0;i < list->cnt;++i) {
		if (list->array[i] == value) {
			return 1;
		}
	}
	return 0;
}

void list_free(list_t list){
	free(list.array);
}

void list_print(list_t *list){
	if(list == NULL) return;

	putchar('[');
	for (int i = 0;i < list->cnt;++i) {
		if (i != 0)
			putchar(' ');
		printf("%d",list->array[i]);
		if (i != (list->cnt-1))
			putchar(',');
	}
	putchar(']');
}
