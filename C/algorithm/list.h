#ifndef LIST_H
#define LIST_H

typedef struct list_t {
  int *array;
  int size;
  int capacity;
} list_t;

#define list_init() (list_t){0}

void list_free(list_t list);
int list_append(list_t* list,int value);
int list_pop(list_t* list);
int list_lookup(list_t* list);
_Bool list_is_in(list_t* list,int value);
void list_print(list_t* list);

#endif
