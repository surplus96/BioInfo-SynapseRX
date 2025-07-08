 
#include "../headers/dpmain.h"
/*
 * Copyright <2012> <Vincent Le Guilloux,Peter Schmidtke, Pierre Tuffery>
 * Copyright <2013-2018> <Peter Schmidtke, Vincent Le Guilloux>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

 */
/*

## -- GENERAL INFORMATION
##
## FILE 					dpmain.c
## AUTHORS					P. Schmidtke and V. Le Guilloux
## LAST MODIFIED			28-11-08
##
## -- SPECIFICATIONS
##
##	Top function to call dpocket routines. Get programm parameters,
##	call function and free memory.
##
## -- MODIFICATIONS HISTORY
##
##	28-11-08	(v)  Added COPYRIGHT DISCLAMER
##	01-04-08	(v)  Added comments and creation of history
##	01-01-08	(vp) Created (random date...)
##	
## -- TODO or SUGGESTIONS
##

*/

/**
   ## FUNCTION:
	int main(int argc, char *argv[])
   
   ## SPECIFICATION:
	Main program for dpocket!
   
*/
int main(int argc, char *argv[])
{
	s_dparams *par = get_dpocket_args(argc, argv) ;
	//print_dparams(par, stdout) ;

	dpocket(par) ;

	free_dparams(par) ;
  	free_all() ;

	return 0 ;
}

