#include "list.h"
#include "stdlib.h"
#include <stdio.h>

#define INITIAL_CAPACITY 2

int list_append(list_t* list, int value){
	if (list == NULL)
		return -1;

	if (list->size == list->capacity) {
		int new_capacity = list->capacity ? list->capacity * 2 : INITIAL_CAPACITY;
		int *tmp = realloc(list->array, sizeof(int) * new_capacity);
		if (tmp == NULL)
			return -1;
		list->array = tmp;
		list->capacity = new_capacity;
	}

	list->array[list->size++] = value;
	return 0;
}

int list_pop(list_t* list){
	if (list == NULL || list->size == 0)
		return -1;
	return list->array[--list->size];
}

int list_lookup(list_t* list){
	if (list == NULL || list->size == 0)
		return -1;
	return list->array[list->size - 1];
}

_Bool list_is_in(list_t* list, int value){
	if (list == NULL)
		return 0;
	for (int i = 0; i < list->size; ++i)
		if (list->array[i] == value)
			return 1;
	return 0;
}

void list_free(list_t list){
	free(list.array);
}

void list_print(list_t *list){
	if (list == NULL) return;

	putchar('[');
	for (int i = 0; i < list->size; ++i) {
		if (i != 0)
			putchar(' ');
		printf("%d", list->array[i]);
		if (i != list->size - 1)
			putchar(',');
	}
	putchar(']');
}
