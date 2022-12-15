#ifndef JQ_SHIELD
#define JQ_SHIELD
#ifdef __cplusplus
extern "C" {
#endif
#include<stdlib.h>

int c_jq(void *_jq, const char *data, char *output, int capacity);

int c_jq_setquery(void *_jq,const char *query);

void *c_jq_init();
int c_jq_free(void *_jq);

#ifdef __cplusplus
}
#endif

#endif
