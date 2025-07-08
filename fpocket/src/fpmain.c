
#include "../headers/fpmain.h"
/*
 * Copyright <2012> <Vincent Le Guilloux,Peter Schmidtke, Pierre Tuffery>
 * Copyright <2013-2018> <Peter Schmidtke, Vincent Le Guilloux>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

 */
/*

## GENERAL INFORMATION
##
## FILE 					fpmain.c
## AUTHORS					P. Schmidtke and V. Le Guilloux
## LAST MODIFIED			01-04-08
##
## SPECIFICATIONS
##
##	Top function to call fpocket routines. Get and check programm parameters,
##	call functions, write output and free memory.
##
## MODIFICATIONS HISTORY
##
##	19-01-09	(v)  Minor modif (print on the same line)
##	28-11-08	(v)  process_pdb added, list of pdb taken into account as input
##					 Comments UTD.
##	27-11-08	(v)  PDB file check moved here instead of fparams
##	01-04-08	(v)  Added comments and creation of history
##	01-01-08	(vp) Created (random date...)
##
## TODO or SUGGESTIONS
##

*/

/**
   ## FUNCTION:
        int main(int argc, char *argv[])

   ## SPECIFICATION:
        Main program!

*/

int main(int argc, char *argv[])
{

        s_fparams *params = get_fpocket_args(argc, argv);

        /* If parameters parsing is ok */
        if (params)
        {
                params->fpocket_running = 1;
                if (!params->db_run)
                        fprintf(stdout, "***** POCKET HUNTING BEGINS ***** \n");
                //                print_fparams(params,stdout);

                if (params->pdb_lst != NULL)
                {
                        /* Handle a list of pdb */
                        int i;
                        for (i = 0; i < params->npdb; i++)
                        {
                                printf("> Protein %d / %d : %s", i, params->npdb,
                                       params->pdb_lst[i]);
                                if (i == params->npdb - 1)
                                        fprintf(stdout, "\n");
                                else
                                        fprintf(stdout, "\r");
                                fflush(stdout);
                                process_pdb(params->pdb_lst[i], params);
                        }
                }
                else
                {
                        if (!params->pdb_path[0] || strlen(params->pdb_path) <= 0)
                        {
                                fprintf(stdout, "! Invalid pdb name given.\n");
                                print_pocket_usage(stdout);
                        }
                        else
                        {

                                process_pdb(params->pdb_path, params);
                        }
                }
                if (!params->db_run)
                        fprintf(stdout, "***** POCKET HUNTING ENDS ***** \n");
                free_fparams(params);
        }
        else
        {
                print_pocket_usage(stdout);
        }

        if (DEBUG)
                print_number_of_objects_in_memory();
        free_all();

        return 0;
}
/**
   ## FUNCTION:
        process_pdb

   ## SPECIFICATION:
        Handle a single pdb: check the pdb name, load data, and launch fpocket if
        the pdb file have been successfully read.

   ## PARAMETRES:
        @ char *pdbname     : Name of the pdb
        @ s_fparams *params : Parameters of the algorithm. See fparams.c/.h

   ## RETURN:
        void

*/
void process_pdb(char *pdbname, s_fparams *params)
{
        /* Check the PDB file */
        if (pdbname == NULL)
                return;
        if (DEBUG)
        {
                fprintf(DEBUG_STREAM, "Prior to process_pdb\n");
                print_number_of_objects_in_memory();
        }
        int len = strlen(pdbname);
        if (len >= M_MAX_PDB_NAME_LEN || len <= 0)
        {
                fprintf(stderr, "! Invalid length for the pdb file name. (Max: %d, Min 1)\n",
                        M_MAX_PDB_NAME_LEN);
                return;
        }

        /* Try to open it */
        if (DEBUG)
                print_number_of_objects_in_memory();

        s_pdb *pdb = open_file_format(pdbname, NULL, M_DONT_KEEP_LIG, params->model_number, params);
        s_pdb *pdb_w_lig = open_file_format(pdbname, NULL, M_KEEP_LIG, params->model_number, params);

        // s_pdb *pdb = open_mmcif(pdbname, NULL, M_DONT_KEEP_LIG, params->model_number, params);
        // s_pdb *pdb_w_lig = open_mmcif(pdbname, NULL, M_KEEP_LIG, params->model_number, params);

        // s_pdb *pdb = rpdb_open(pdbname, NULL, M_DONT_KEEP_LIG, params->model_number, params);
        // s_pdb *pdb_w_lig = rpdb_open(pdbname, NULL, M_KEEP_LIG, params->model_number, params);
        if (DEBUG)
                print_number_of_objects_in_memory();

        if (params->topology_path[0] != 0)
        {
                read_topology(params->topology_path, pdb);
        }

        if (pdb)
        {
                /* Actual reading of pdb data and then calculation */

                read_file_format(pdb, NULL, M_DONT_KEEP_LIG, params->model_number, params);
                read_file_format(pdb_w_lig, NULL, M_KEEP_LIG, params->model_number, params);

                // read_mmcif(pdb, NULL, M_DONT_KEEP_LIG, params->model_number, params);
                // read_mmcif(pdb_w_lig, NULL, M_KEEP_LIG, params->model_number, params);

                // rpdb_read(pdb, NULL, M_DONT_KEEP_LIG, params->model_number, params);
                // rpdb_read(pdb_w_lig, NULL, M_KEEP_LIG, params->model_number, params);

                //                        fprintf(stdout,"Init coordinate grid\n");
                create_coord_grid(pdb);
                //                        fprintf(stdout,"Done initing coordinate grid\n");

                /*free_pdb_atoms(pdb);
                        free_pdb_atoms(pdb_w_lig);
                        if(DEBUG)print_number_of_objects_in_memory();

                        return(NULL);*/

                c_lst_pockets *pockets = search_pocket(pdb, params, pdb_w_lig);

                //	c_lst_pocket_free(pockets) ;

                if (DEBUG)
                        print_number_of_objects_in_memory();

                if (pockets)
                {
                        if (params->db_run)
                        {
                                write_descriptors_DB(pockets, stdout);
                                write_out_fpocket_DB(pockets, pdb, pdbname);
                        }
                        else
                                write_out_fpocket(pockets, pdb, pdbname);
                        c_lst_pocket_free(pockets);
                }
                else
                {
                        if (!params->db_run)
                        {
                                printf("no pockets found\n");
                        }
                }

                if (DEBUG)
                {
                        print_number_of_objects_in_memory();
                        fprintf(DEBUG_STREAM, "freeing final pocket list\n");
                        print_number_of_objects_in_memory();
                }

                free_pdb_atoms(pdb);
                free_pdb_atoms(pdb_w_lig);

                if (DEBUG)
                {
                        fprintf(DEBUG_STREAM, "Closing PDB file and freeing data\n");

                        print_number_of_objects_in_memory();
                }
        }
        else {
                fprintf(stderr, "! Structure reading failed!\n");
                exit( EXIT_FAILURE );
        }
}

s_pdb *open_file_format(char *fpath, const char *ligan, const int keep_lig, int model_number, s_fparams *par)
{
        s_pdb *pdb;
        if (strstr(par->pdb_path, ".cif")) /*strstr finds the substring and here we search for the file extension we want */
                pdb = open_mmcif(fpath, NULL, keep_lig, par->model_number, par);
        else if (strstr(par->pdb_path, ".pdb"))
                pdb = rpdb_open(fpath, NULL, keep_lig, par->model_number, par);

        return pdb;
}

void read_file_format(s_pdb *pdb, const char *ligan, const int keep_lig, int model_number, s_fparams *par)
{

        if (strstr(par->pdb_path, ".cif"))
        { /*strstr finds the substring and here we search for the file extension we want */
                read_mmcif(pdb, NULL, keep_lig, par->model_number, par);
        }
        else if (strstr(par->pdb_path, ".pdb"))
                rpdb_read(pdb, NULL, keep_lig, par->model_number, par);
}