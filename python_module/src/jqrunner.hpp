#ifndef JQRUNNER_HPP_INC
#define JQRUNNER_HPP_INC

#include "jq_shield.h"

class JQRunner{
private:
  void *_jq;
  char *scratch;
  int capacity=4096;
public:

  JQRunner(std::string program)
  { 
       _jq = c_jq_init();
       c_jq_setquery(_jq,program.c_str());
       scratch = new char [capacity];
       scratch[0] = '\0';
  }

  ~JQRunner(){
     c_jq_free(_jq);;
     delete[] scratch;
     scratch = NULL;
  }
  bool set_capacity(int _capacity)
  {
     capacity = _capacity;
     delete[] scratch;
     scratch = new char[capacity];
     return (scratch != NULL);
  }

  std::string operator()(std::string data)
  {
    scratch[0]='\0';
    while (c_jq(_jq,data.c_str(),scratch, capacity) == -2) // capacity
    {
       set_capacity(2*capacity);
       //std::cerr << "INFO: Capacity escalated to " << capacity << std::endl;
    }
    std::string ret(scratch);
    return ret;
  }
};

#endif
