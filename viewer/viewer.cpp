#include<dslab.h>
#include<iostream>
#include<vector>
#include<stdint.h>

#include "datasystem.h"
using namespace std;

enum {
	MENU_ZOOMFIT=500,
	MENU_ZOOMIN,
	MENU_ZOOMOUT,
	MENU_FILEOPEN
};


class MyDataEngine :public DataEngine
{
	private:
	double theta[3];
	dsOrthoZoomPan zoompan;
	DataSystem ds;
	public:
	
	virtual void Init()
	{
		cout << "Initialization" << endl;
		zoompan.setMBR(0,10,0,10);
		glEnable(GL_DEPTH_TEST);
	    wxToolBar *toolbar;
		toolbar = new wxToolBar(getFrame(),-1);

		toolbar->AddTool(MENU_ZOOMIN,wxT("Zoom In"),wxBitmap((const char *const *) &xpm_viewmagp));
		toolbar->AddTool(MENU_ZOOMOUT,wxT("Zoom Out"),wxBitmap((const char *const *) &xpm_viewmagm));
		toolbar->AddTool(MENU_ZOOMFIT,wxT("Zoom Fit"),wxBitmap((const char *const *) &xpm_viewmag1));
		
		
		toolbar->AddSeparator();
		toolbar->AddTool(wxID_ABOUT,wxT("About"),wxBitmap((const char *const *) &xpm_mdsg));
		toolbar->Realize();
		getFrame()->SetToolBar(toolbar);

		
		
		
	}
	virtual void think(double iElapsed)
	{
		theta[0] += 0.1*3.1415926*(iElapsed / 1E12);
		theta[1] += 0.06*3.1415926*(iElapsed / 1E12);
	}
	virtual void createMenu(wxMenu *menuDataEngine)
	{
		// start of from 500
		menuDataEngine->Append(MENU_FILEOPEN,wxT("Open File..."),wxT("Open an AtlasHDF File for viewing"));
		menuDataEngine->Append(501,wxT("Second"),wxT("Help2"));
	}
	virtual void extendViewMenu(wxMenu *menuDataEngine)
	{
		// start of from 500
		menuDataEngine->Append(502,wxT("First View"),wxT("Help"));
		menuDataEngine->Append(503,wxT("Second View"),wxT("Help2"));
		DS_start_rendering();
	}
		
		
		virtual void handleMenu(int id)
		{
		  std::vector<double> mbr;
		  wxFileDialog	openH5Dialog(NULL, _("Open AtlasHDF file"), _(""), _(""),
					     _("HDF5 (*.H5)|*.h5"), wxFD_OPEN|wxFD_FILE_MUST_EXIST);
			switch (id)
			{
				case MENU_ZOOMFIT:
					zoompan.zoomFit(); break;
				case MENU_ZOOMIN:
					zoompan.zoom(1); break;
				case MENU_ZOOMOUT:
					zoompan.zoom(-1); break;
				case MENU_FILEOPEN:
				    
				    if (openH5Dialog.ShowModal() == wxID_CANCEL)
						return; 
				   ds.Load(std::string(openH5Dialog.GetPath().mb_str()));
				   mbr = ds.getMBR();
				   zoompan.setMBR(mbr[0],mbr[1],mbr[2],mbr[3]);
				   zoompan.zoomFit(); 
				  
				    break;
				default:
					cout << "Menu Item " << id << " ignored" << endl;
					break;
			}
		}

		virtual void beforeQuit(){
			// Do some data cleanup / file sync / close
			cout << "Preparing DataEngine for exit" << endl;
		};
		
				
		virtual void render(size_t width, size_t height)
		{
		  
		  zoompan.setViewport(0,0,width,height);
		  zoompan.glViewport();
		  
		  glMatrixMode( GL_PROJECTION );
		  glLoadIdentity( );
		  zoompan.glProject();

			glMatrixMode( GL_MODELVIEW );
			glClearColor( 1, 1, 1, 1.0 );
			glClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT ); 

   		glColor3f(0.094,0.44,0.71  );
		
		for (const auto &line : ds.index)
		{
		    glBegin(GL_LINE_STRIP);
		    for (size_t i=line[0]; i < line[1]; i++)
		      glVertex2f(ds.coords[i][0],ds.coords[i][1]);
		   glEnd();
		}

		// render filled polygons
		glColor3f(0,0,0); // black
		int warnings=0; 
		glBegin(GL_TRIANGLES);
		for (const auto &t: ds.triangles_idx)
		{
		    for (int i=t[0]; i < t[1]; i+= 3) // a triangle forward
		    {
			// @todo: hack: there are data problems 0/0 in coordinates
			if (
			    (fabs(ds.triangles[i][0])<0.001 && fabs(ds.triangles[i][1])<0.001) || 
			    (fabs(ds.triangles[i+1][0])<0.001 && fabs(ds.triangles[i+1][1])<0.001) || 
			    (fabs(ds.triangles[i+2][0])<0.001 && fabs(ds.triangles[i+2][1])<0.001)
			    )
			    {
			    warnings ++;
			    continue;
			    }
			glVertex2f(ds.triangles[i][0],ds.triangles[i][1]);
			glVertex2f(ds.triangles[i+1][0],ds.triangles[i+1][1]);
			glVertex2f(ds.triangles[i+2][0],ds.triangles[i+2][1]);
			
		    }
		}
		glEnd();
		

	        }
		
		virtual void mouseClick(size_t x, size_t y)
		{
		    auto loc = zoompan.clientProject(x,y);
		    std::cout << "Clicked: " << loc.first << "/" << loc.second << std::endl;
		}
		
		virtual void mouseDragging(size_t from_x,size_t from_y, size_t to_x,size_t to_y)
		{
			auto from = zoompan.clientProject(from_x,from_y);
			auto to = zoompan.clientProject(to_x,to_y);
			zoompan.x -=  (to.first - from.first);
			zoompan.y -=  (to.second - from.second);
		}
		virtual void mouseWheel(size_t x, size_t y, int steps) {
			zoompan.fixZoom(x,y,steps);
		};
};

/*Instantiate it and make it available to the library*/
MyDataEngine eng;
DataEngine *getDataEngineImplementation()
{
   return (DataEngine*) &eng;
}

