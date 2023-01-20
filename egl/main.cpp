
#include<iostream>
#include <GL/glew.h>
#include <EGL/egl.h>
#include<cstring>
#include<vector>
#include "prepare_ogl.h"
#include "hdf5.h"
#include "svpng.inc"
#include "tictoc.hpp"


static const EGLint configAttribs[] = {
          EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
          EGL_BLUE_SIZE, 8,
          EGL_GREEN_SIZE, 8,
          EGL_RED_SIZE, 8,
          EGL_DEPTH_SIZE, 8,
          EGL_RENDERABLE_TYPE, EGL_OPENGL_BIT,
          EGL_NONE
  };    

  static const int pbufferWidth = 224;
  static const int pbufferHeight = 224;

  static const EGLint pbufferAttribs[] = {
        EGL_WIDTH, pbufferWidth,
        EGL_HEIGHT, pbufferHeight,
        EGL_NONE,
  };

#include<random>
void random_patch()
{
   //gluOrtho2D(, );
   double lower_bound = 0;
   double upper_bound = 10000;
   static  std::uniform_real_distribution<double> xd(10.7259, 13.0813);
   static  std::uniform_real_distribution<double> yd(47.391,49.0725);
   static std::default_random_engine re;
   std::vector<double> ortho{xd(re), xd(re), yd(re),yd(re)};
   gluOrtho2D(std::min(ortho[0],ortho[1]),std::max(ortho[0],ortho[1]),std::max(ortho[2],ortho[3]),std::min(ortho[2],ortho[3]));
}
  


  


  
int main(int argc, char *argv[])
{
   std::vector<double> vertex_array;
   std::vector<uint32_t> index_array;
   load_opengl(argv[1], vertex_array, index_array);
    std::cout << "vertices:" << vertex_array.size() << std::endl;
    std::cout << "indices:" << index_array.size() << std::endl;


  // 1. Initialize EGL
  EGLDisplay eglDpy = eglGetDisplay(EGL_DEFAULT_DISPLAY);

  EGLint major, minor;

  eglInitialize(eglDpy, &major, &minor);

  // 2. Select an appropriate configuration
  EGLint numConfigs;
  EGLConfig eglCfg;

  eglChooseConfig(eglDpy, configAttribs, &eglCfg, 1, &numConfigs);

  // 3. Create a surface
  EGLSurface eglSurf = eglCreatePbufferSurface(eglDpy, eglCfg, 
                                               pbufferAttribs);

  // 4. Bind the API
  eglBindAPI(EGL_OPENGL_API);

  // 5. Create a context and make it current
  EGLContext eglCtx = eglCreateContext(eglDpy, eglCfg, EGL_NO_CONTEXT, 
                                       NULL);

  eglMakeCurrent(eglDpy, eglSurf, eglSurf, eglCtx);

  // from now on use your OpenGL context
    GLenum err = glewInit();
    if (GLEW_OK != err && err != GLEW_ERROR_NO_GLX_DISPLAY)
    {
      /* Problem: glewInit failed, something is seriously wrong. */
      fprintf(stderr, "Error: %s\n", glewGetErrorString(err));
    }
   fprintf(stdout, "Status: Using GLEW %s\n", glewGetString(GLEW_VERSION));

 // Transmit Data
    GLuint points_vbo = 0;
    glGenBuffers(1, &points_vbo);
    glBindBuffer(GL_ARRAY_BUFFER, points_vbo);
    glBufferData(GL_ARRAY_BUFFER, vertex_array.size()* sizeof(double), &vertex_array[0], GL_STATIC_DRAW);
    glVertexPointer(2, GL_DOUBLE, 0, NULL);

    GLuint index_ibo = 0;
    glGenBuffers(1, &index_ibo);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, index_ibo);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, index_array.size() * sizeof(uint32_t), index_array.data(), GL_STATIC_DRAW);


  // Set up view
    glClearColor(1.0f, 0.0f, 0.0f, 1.0f); 
    glDisable(GL_TEXTURE_2D);   // textures
    glEnable(GL_COLOR_MATERIAL);
    glEnable(GL_BLEND);
    glDisable(GL_DEPTH_TEST);
    glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);
 
    glViewport(0, 0,pbufferWidth,pbufferHeight);
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
    glEnableClientState(GL_VERTEX_ARRAY);
    glEnableClientState(GL_INDEX_ARRAY);
    glBindBuffer(GL_ARRAY_BUFFER, points_vbo);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, index_ibo);
    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();
    glMatrixMode(GL_PROJECTION);
    uint8_t* ImageBuffer = new uint8_t[pbufferWidth*pbufferHeight * 4];
    std::cout << "Running 1000 frames" << std::endl;
    {tictoc t("1000 frames");
    for (size_t i=0; i < 1000; i++)
    {
	glLoadIdentity();
	random_patch();
	//gluOrtho2D(10.7259, 13.0813, 49.0725,47.391);
	glClear(GL_COLOR_BUFFER_BIT);
	glDrawElements(
	    GL_TRIANGLES,
	    index_array.size(),
	    GL_UNSIGNED_INT,
	    NULL
	);
    glFinish();
    eglSwapBuffers( eglDpy, eglSurf);
    // Here we should read back our buffer
    
    memset(ImageBuffer, 0, pbufferWidth*pbufferHeight * 4);
    glReadPixels(0, 0, pbufferWidth, pbufferHeight, GL_RGBA, GL_UNSIGNED_BYTE, ImageBuffer);
    char fname[1024]; snprintf(fname,1024, "out-%04d.png", i);
    FILE *f = fopen(fname,"wb");
    svpng(f, pbufferWidth,pbufferHeight, ImageBuffer, 1);
    fclose(f);

    }
    } // tictoc
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0);
    
    
    FILE *f = fopen("out.png","wb");
    svpng(f, pbufferWidth,pbufferHeight, ImageBuffer, 1);
    fclose(f);
   
  

  // 6. Terminate EGL when finished
  eglTerminate(eglDpy);
  return 0;
}
