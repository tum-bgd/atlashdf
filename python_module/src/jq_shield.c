/*JQ uses some names that are incompatible with C++, 
most importantly template. Therefore, we shield it in a single C file*/

#include "compile.h"
#include "jv.h"
#include "jq.h"
#include "jv_alloc.h"

#include "util.h"
//#include "version.h"
#include<string.h>

#include<stdlib.h>

void *c_jq_init()
{
   jq_state *jq = NULL;
   jq = jq_init();
    if (jq == NULL) {
       perror("malloc");
       return NULL;
    }
    return (void *)jq;
}
int c_jq_free(void *_jq)
{
    jq_state *jq = (jq_state*)_jq;
    if (jq == NULL) {
       printf("FATAL: c_jq used without c_jq_init (c_jq ==NULL)");
       return -1;
    };
    jq_teardown(&jq);
    jq = NULL;
    return 0;
}


int c_jq_setquery(void *_jq, const char *query)
{
    jq_state *jq = (jq_state*)_jq;
    if (jq == NULL) {
       printf("FATAL: c_jq used without c_jq_init (c_jq ==NULL)");
       return -1;
    };
   int c = jq_compile(jq,query);
   if (!c)
   {
      printf("Program did not compile: %s", query);
      return -1;
   }
   return 0;    
}


int c_jq(void *_jq, const char *data, char *output, int capacity)
{
  
    jq_state *jq = (jq_state *)_jq;
    if (jq == NULL) {
       printf("FATAL: c_jq used without c_jq_init (c_jq ==NULL)");
       return -1;
    };

   jv input = jv_parse(data);
   if (!jv_is_valid(input)) {
      printf("*** Input is invalid on %s", data);
      return -1;
   }

    int flags = 0;
    jq_start(jq, input, 0);

    jv result;
    char *p = output;
    while (jv_is_valid(result = jq_next(jq)))
    {
        //fwrite(jv_string_value(result), 1, jv_string_length_bytes(jv_copy(result)), stdout);
	jv as_string;
	if (jv_get_kind(result) == JV_KIND_STRING)
	{
            as_string = jv_copy(result);
	}else{
            as_string = jv_dump_string(jv_copy(result), flags); //remark: this does add the " "s for strings
	}

	size_t len = jv_string_length_bytes(jv_copy(as_string));
	if (capacity > len){
	    strncpy(p, jv_string_value(as_string) , len );
	    p += len;
	    *p = '\0';
	    capacity -= len;
	 }else{
	    jv_free(result);
	    jv_free(as_string);
	    return -2;
	 }
	 jv_free(as_string);
	 jv_free(result);
    }
     return 0;
}

