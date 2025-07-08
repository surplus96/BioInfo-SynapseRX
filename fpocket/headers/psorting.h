/*
 * Copyright <2012> <Vincent Le Guilloux,Peter Schmidtke, Pierre Tuffery>
 * Copyright <2013-2018> <Peter Schmidtke, Vincent Le Guilloux>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

 */
#ifndef DH_PSORTING
#define DH_PSORTING

/* -----------------------------INCLUDES--------------------------------------*/

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#include "pocket.h"

/* ---------------------- PUBLIC STRUCTURES ----------------------------------*/


/* ----------------------------PROTOTYPES-------------------------------------*/

void sort_pockets(c_lst_pockets *pockets, 
				  int (*fcmp)(const node_pocket*, const node_pocket*)) ;

int compare_pockets_nasph(const node_pocket *p1, const node_pocket *p2) ;
int compare_pockets_volume(const node_pocket *p1, const node_pocket *p2) ; 
int compare_pockets_score(const node_pocket *p1, const node_pocket *p2) ;
int compare_pockets_corresp(const node_pocket *p1, const node_pocket *p2) ;
int compare_pockets_vol_corresp(const node_pocket *p1, const node_pocket *p2) ;

#define M_VOLUME_SORT_FUNCT &compare_pockets_volume
#define M_SCORE_SORT_FUNCT &compare_pockets_score
#define M_NASPH_SORT_FUNCT &compare_pockets_nasph

#endif
