/*
 * Copyright <2012> <Vincent Le Guilloux,Peter Schmidtke, Pierre Tuffery>
 * Copyright <2013-2018> <Peter Schmidtke, Vincent Le Guilloux>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

 */


#ifndef ENERGY_H
#define	ENERGY_H


#include "rpdb.h"
#include "grid.h"
#include "voronoi.h"
#include "pocket.h"
#include "voronoi_lst.h"
#include "calc.h"
#include "atom.h"
#include <sys/stat.h>
#include <sys/types.h>
//#include "math.h"

#define G_GRID_RESOLUTION 0.3
#define MAX_NUMBER_ATOMS_NEAR 1000
#define TINY_SPACING    1.0



typedef struct s_grid{
    float ***gridvalues;    /**< values of the md grid (i.e. number of alpha spheres nearby*/
    float *origin;          /**< origin of the grid (3 positons, xyz)*/
    int nx,ny,nz;           /**< gridsize at the x, y, z axis*/
    float resolution;       /**< resolution of the grid; in general 1A*/
}s_grid;


typedef struct s_pocket_energy_grid{
    s_grid *vdw_grid;       /**< */ 
    s_grid *elec_grid;       /**< */ 
    
} s_pocket_energy_grid;



typedef struct s_min_max_pocket
{
    float minx;             /**< minimum x coordinate of current pocket*/
    float miny;             /**< minimum y coordinate of current pocket*/
    float minz;             /**< minimum z coordinate of current pocket*/
    float maxx;             /**< maximum x coordinate of current pocket*/
    float maxy;             /**< maximum y coordinate of current pocket*/
    float maxz;             /**< maximum z coordinate of current pocket*/
} s_min_max_pocket;



/* ------------------------------ PUBLIC FUNCTIONS ---------------------------*/
void calculate_pocket_energy_grids(c_lst_pockets *pockets,s_fparams *params,s_pdb *pdb);
s_grid *init_pocket_grid(s_pocket *p);
unsigned short grid_point_overlaps_with_alpha_sphere(float pos[3],s_vvertice *vert);
void assign_energies(s_grid *g_elec,s_grid *g_vdw,s_pocket *p,s_pdb *pdb);
void get_atoms_contacted_by_vertices_overlapping_with_grid_point(float pos[3],s_pocket *p,int *n_atoms, s_atm **atom_ids);
void add_atom_ids_not_in_list(s_atm **atom_ids,int *n_atoms,s_vvertice *v);
void set_energies_to_grid_point(int cx, int cy,int cz,s_atm **atom_ids,int n_atoms,s_grid *g_elec,s_grid *g_vdw);
void write_grid(s_grid *g, FILE *f);
//short get_ff_type(char *atom_name);
void set_alpha_sphere_electrostatic_energy(s_vvertice *v,s_grid *g_elec);
s_min_max_pocket *float_get_min_max_from_pocket(s_pocket *pocket);
s_pocket_energy_grid *get_pocket_energy(s_pocket *p);
void add_atom_ids_from_grid_point(s_atm **atom_ids, int *n_atoms, s_atm **atoms_in_grid_point, int n_atoms_in_gridpoint);
void get_atoms_in_near_grid_points(float pos[3],  s_pdb_grid *g, int *n_atoms, s_atm **atom_ids);
void assign_mean_energies(s_grid *g,int devider);

    
    


#endif	/* ENERGY_H */

