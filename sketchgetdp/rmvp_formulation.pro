/* =============================================================================
    Main script for the reduced magnetic vector potential (RMVP) simulation.

    Author: Laura D'Angelo
  ============================================================================= */

// LOAD DATA
Include "physical_identifiers.pro";
Include "physical_values.pro"
/* These data files define the following parameters:

Physical identifiers 
---------------------------
    - domain_coil_positive (int)
    - domain_coil_negative (int)
    - domain_Va (int)
    - domain_Vi_iron (int)
    - domain_Vi_air (int)
    - boundary_gamma (int)
    - boundary_out (int)

Physical values
----------------------------
    - Isource (float)
    - mu0 (float)
    - nu0 (float)
    - nu_iron_linear (float)
*/

DefineConstant[
    des_dir = "results"
];

// -----------------------------------------------------------------------------

// DEFINE REGION GROUPS
Group {
    // Coil domain 
    Domain_Coil_Positive = Region[ {domain_coil_positive} ];
    Domain_Coil_Negative = Region[ {domain_coil_negative} ];
    Domain_Coil_Total = Region[ {domain_coil_positive, domain_coil_negative} ];

    // Source domain
    Domain_Va = Region[ {domain_Va} ];
    Domain_Va_closed = Region[ {domain_Va, boundary_gamma} ];

    // Source-free domains (iron and/or air)
    Domain_Vi_Iron = Region[ {domain_Vi_iron} ];
    Domain_Vi_Air = Region[ {domain_Vi_air} ];
    
    // Cumulated domain without coils
    Domain_V = Region[ {domain_Va, domain_Vi_iron, domain_Vi_air} ];
    Domain_V_closed = Region[ {domain_Va, domain_Vi_iron, domain_Vi_air, boundary_gamma, boundary_out} ];

    // Interface boundary 
    Boundary_Gamma = Region[ {boundary_gamma} ];

    // Computational domain boundary 
    Boundary_Out = Region[ {boundary_out} ];
}//Group

// -----------------------------------------------------------------------------

// DEFINE JACOBIAN
Jacobian {
  { Name Vol; Case { { Region All; Jacobian Vol; } } }
  { Name Sur; Case { { Region All; Jacobian Sur; } } }
  { Name Lin; Case { { Region All; Jacobian Lin; } } }
}//Jacobian

// -----------------------------------------------------------------------------

// DEFINE NUMERICAL INTEGRATOR
Integration {
	{	Name Int;
		Case {
			{ Type Gauss;
				Case {
          { GeoElement Point;    NumberOfPoints 1; }
          { GeoElement Line;     NumberOfPoints 3; }
          { GeoElement Triangle; NumberOfPoints 4; }
				}//Case
			}//Type Gauss
		}//Case
	}//Name
}//Integration

// -----------------------------------------------------------------------------

// DEFINE FUNCTIONS
Function {
  // Source current (line current)
  Jsource[Domain_Coil_Positive] = + Isource * UnitVectorZ[];
  Jsource[Domain_Coil_Negative] = - Isource * UnitVectorZ[];

  // Reluctivity distribution
  nu[Domain_Va] = nu0;
  nu[Domain_Vi_Air] = nu0;
  nu[Domain_Vi_Iron] = nu_iron_linear;

}//Function

// -----------------------------------------------------------------------------

// DEFINE CONSTRAINTS
Constraint {
    // Boundary condition for domain boundary (homogeneous Dirichlet BC)
    { Name MVP_Boundary_Condition;
      Case {
        { Region Boundary_Out; Type Assign; Value 0; }
      }//Case
    }//Name
}//Constraint

// -----------------------------------------------------------------------------

// DEFINE FUNCTION SPACES
FunctionSpace {
    // 2D edge function space for the source MVP
    { Name HCurl_As; Type Form1P;

      BasisFunction {
        { Name wi; NameOfCoef as; Function BF_PerpendicularEdge; Support Domain_Va_closed; Entity NodesOf[All];  }
      }//BasisFunction

    }//Name

    // 2D edge function space for the image MVP
    { Name HCurl_Am; Type Form1P;

      BasisFunction {
        { Name wi; NameOfCoef am; Function BF_PerpendicularEdge; Support Domain_Va_closed; Entity NodesOf[All];  }
      }//BasisFunction

    }//Name

    // 2D edge function space for the adapted MVP
    { Name HCurl_Ag; Type Form1P;

      BasisFunction {
        { Name wi; NameOfCoef ai; Function BF_PerpendicularEdge; Support Domain_V_closed; Entity NodesOf[All]; }
      }//BasisFunction

      Constraint {
        { NameOfCoef ai; EntityType NodesOf; NameOfConstraint MVP_Boundary_Condition; }
      }//Constraint

    }//Name

    // 2D edge function space for source H-field
    { Name HCurl_Hs; Type Form1;

      BasisFunction {
        { Name wi; NameOfCoef ai; Function BF_Edge; Support Domain_Va_closed; Entity EdgesOf[All]; }
      }//BasisFunction

    }//Name

    // 2D edge function space of the source surface current density component
    { Name HCurl_nxHs; Type Form1P;

      BasisFunction {
        { Name ws; NameOfCoef nxhs; Function BF_PerpendicularEdge; Support Boundary_Gamma; Entity NodesOf[All]; }
      }//BasisFunction

    }//Name

    // 2D edge function space of the reaction surface current density component
    { Name HCurl_nxHm; Type Form1P;

      BasisFunction {
        { Name ws; NameOfCoef nxhm; Function BF_PerpendicularEdge; Support Boundary_Gamma; Entity NodesOf[All]; }
      }//BasisFunction

    }//Name

}//FunctionSpace

// -----------------------------------------------------------------------------

// DEFINE FORMULATION
Formulation {

    // Biot-Savart formulation
    { Name BiotSavart;  Type FemEquation;

        Quantity {
            // Source MVP
            { Name as;             Type Local;     NameOfSpace HCurl_As; }

            // Coulomb integrand
            { Name coulomb_int;    Type Integral;  NameOfSpace HCurl_As;
                [ mu0 *  Laplace[]{2D} * Jsource[]  ];
                In Domain_Coil_Total;
                Jacobian Lin;
                Integration Int;
            }//Name

        }//Quantity

        Equation {
            // Computing the source MVP from the Biot-Savart integral in the source domain...
            Galerkin{ [ Dof{as}, {as} ];                    In Domain_Va; Jacobian Vol; Integration Int; }
            Galerkin{ [ -{coulomb_int}, {as} ];             In Domain_Va; Jacobian Vol; Integration Int; }
            // ...and on the interface boundary
            Galerkin{ [ Dof{as}, {as} ];                    In Boundary_Gamma; Jacobian Sur; Integration Int; }
            Galerkin{ [ -{coulomb_int}, {as} ];             In Boundary_Gamma; Jacobian Sur; Integration Int; }
        }//Equation

    }//Name

    { Name BiotSavartHs;  Type FemEquation;
        Quantity {
            // Source MVP
            { Name as;              Type Local;     NameOfSpace HCurl_As; }

            // Source H-field
            { Name hs;              Type Local;     NameOfSpace HCurl_Hs; }

            // Source surface current density component
            { Name nxhs;            Type Local;     NameOfSpace HCurl_nxHs; }
        }//Quantity

        Equation {
            // Computing the surface current component of the source field
            Galerkin{ [ nu0 * {d as}, {hs} ];                                 In Domain_Va; Jacobian Vol; Integration Int; }
            Galerkin{ [ -Dof{hs}, {hs} ];                                     In Domain_Va; Jacobian Vol; Integration Int; }

            // Projection for image H-field
            Galerkin{ [ - Cross[ Normal[], Dof{hs} ], {nxhs} ];               In Boundary_Gamma; Jacobian Sur; Integration Int; }
            Galerkin{ [ Dof{nxhs}, {nxhs} ];                                  In Boundary_Gamma; Jacobian Sur; Integration Int; }
        }//Equation

    }//Name

    // Image formulation
    { Name Image_Problem;  Type FemEquation;

        Quantity {
            // Image MVP
            { Name am;              Type Local;       NameOfSpace HCurl_Am; }

            // Normal x Image H-field
            { Name nxhm;            Type Local;       NameOfSpace HCurl_nxHm;  }

            // Source MVP
            { Name as;              Type Local;       NameOfSpace HCurl_As; }
        }//Quantity

        Equation {
            Galerkin{ [ nu0 * Dof{d am}, {d am} ];                      In Domain_Va; Jacobian Vol; Integration Int; }
            Galerkin{ [ Dof{nxhm}, {am} ];                              In Boundary_Gamma; Jacobian Sur; Integration Int; }
            Galerkin{ [ Dof{am}, {nxhm} ];                              In Boundary_Gamma; Jacobian Sur; Integration Int; }
            Galerkin{ [ {as}, {nxhm} ];                                 In Boundary_Gamma; Jacobian Sur; Integration Int; }
        }//Equation

    }//Name

    // Reduced formulation
    { Name Reduced_Formulation;  Type FemEquation;

        Quantity {
            // Reduced MVP
            { Name ag;          Type Local;     NameOfSpace HCurl_Ag;   }

            // Image MVP
            { Name am;          Type Local;     NameOfSpace HCurl_Am;   }

            // Source MVP
            { Name as;          Type Local;     NameOfSpace HCurl_As;   }

            // Normal x Source H-field
            { Name nxhs;        Type Local;     NameOfSpace HCurl_nxHs; }

            // Normal x Image H-field
            { Name nxhm;        Type Local;     NameOfSpace HCurl_nxHm; }

        }//Quantity

        Equation {
            // Curlcurl
            Galerkin{ [ nu[] * Dof{d ag}, {d ag} ];         In Domain_V;        Jacobian Vol; Integration Int; }

            // Surface current density on right-hand side
            Galerkin{ [ -{nxhs}, {ag} ];                    In Boundary_Gamma;  Jacobian Sur; Integration Int; }
            Galerkin{ [ -{nxhm}, {ag} ];                    In Boundary_Gamma;  Jacobian Sur; Integration Int; }
        }//Equation

    }//Name

}//Formulation

// -----------------------------------------------------------------------------

// DEFINE RESOLUTION
Resolution {
    { Name Magnetostatic_Resolution;
        System {
        { Name SysBS;     NameOfFormulation BiotSavart; }
        { Name SysBSH;    NameOfFormulation BiotSavartHs; }
        { Name SysImag;   NameOfFormulation Image_Problem; }
        { Name SysMain;   NameOfFormulation Reduced_Formulation; }
        }//System

        Operation {
            CreateDirectory[des_dir];

            Generate[SysBS];
            Solve[SysBS];
            SaveSolution[SysBS];

            Generate[SysBSH];
            Solve[SysBSH];
            SaveSolution[SysBSH];

            Generate[SysImag];
            Solve[SysImag];
            SaveSolution[SysImag];

            Generate[SysMain];
            Solve[SysMain];
            SaveSolution[SysMain];
        }//Operation
    }//Name

}//Resolution

// -----------------------------------------------------------------------------

// DEFINE POST-PROCESS
PostProcessing {
  // Post processing for the reduced main problem
  { Name Reduced_PostProcessing; NameOfFormulation Reduced_Formulation;
    Quantity {
      // Source MVP
      { Name as;
        Value { Local { [ {as} ];                               In Domain_Va;  Jacobian Vol; } }
      }//Name

      // Source MVP magntiude
      { Name as_mag;
        Value { Local { [ Norm[{as}] ];                         In Domain_Va;  Jacobian Vol; } }
      }//Name

      // Image MVP
      { Name am;
        Value { Local { [ {am} ];                               In Domain_Va;  Jacobian Vol; } }
      }//Name

      // Image MVP magnitude
      { Name am_mag;
        Value { Local { [ Norm[{am}] ];                         In Domain_Va;  Jacobian Vol; } }
      }//Name

      // Adapted MVP
      { Name ag;
        Value { Local { [ {ag} ];                               In Domain_V;  Jacobian Vol; } }
      }//Name

      // Adapted MVP magnitude
      { Name ag_mag;
        Value { Local { [ Norm[{ag}] ];                         In Domain_V;  Jacobian Vol; } }
      }//Name

      // Total MVP
      { Name a;
        Value { Local { [ {as} + {am} + {ag} ];                 In Domain_V;  Jacobian Vol; } }
      }//Name

      // Total MVP magnitude
      { Name a_mag;
        Value { Local { [ Norm[ {as} + {am} + {ag} ] ];         In Domain_V;  Jacobian Vol; } }
      }//Name

      // Surface current contribution by source field
      { Name nxhs;
        Value { Local { [ {nxhs} ];                             In Boundary_Gamma;  Jacobian Sur; } }
      }//Name

      // Surface current contribution by reaction field
      { Name nxhm;
        Value { Local { [ {nxhm} ];                             In Boundary_Gamma;  Jacobian Sur; } }
      }//Name

      // Surface current density
      { Name Jg;
        Value { Local { [ {nxhs} + {nxhm} ];                    In Boundary_Gamma;  Jacobian Sur; } }
      }//Name

      // Source B-field
      { Name bs;
        Value { Local { [ {d as} ];                             In Domain_Va;  Jacobian Vol; } }
      }//Name

      // Source B-field magnitude
      { Name bs_mag;
        Value { Local { [ Norm[{d as}] ];                       In Domain_Va;  Jacobian Vol; } }
      }//Name

      // Reaction B-field
      { Name bm;
        Value { Local { [ {d am} ];                             In Domain_Va;  Jacobian Vol; } }
      }//Name

      // Reaction B-field magnitude
      { Name bm_mag;
        Value { Local { [ Norm[{d am}] ];                       In Domain_Va;  Jacobian Vol; } }
      }//Name

      // Adapted B-field
      { Name bg;
        Value { Local { [ {d ag} ];                             In Domain_V;  Jacobian Vol; } }
      }//Name

      // Source B-field magnitude
      { Name bg_mag;
        Value { Local { [ Norm[{d ag}] ];                       In Domain_V;  Jacobian Vol; } }
      }//Name

      // Total B-field
      { Name b;
        Value { Local { [ {d as} + {d am} + {d ag} ];           In Domain_V;  Jacobian Vol; } }
      }//Name

      // Total B-field magnitude
      { Name b_mag;
        Value { Local { [ Norm[ {d as} + {d am} + {d ag} ] ];   In Domain_V;  Jacobian Vol; } }
      }//Name

      // Source current
      { Name Jsrc;
        Value { Local { [ Jsource[] ];                         In Domain_Coil_Total; Jacobian Vol; } }
      }//Name 

    }//Quantity
  }//Name

}//PostProcessing

// -----------------------------------------------------------------------------

// DEFINE POST-OPERATIONS
PostOperation {
  { Name Reduced_PostOp; NameOfPostProcessing Reduced_PostProcessing;
    Operation {
      // MVPs
      Print [ as,       OnElementsOf Domain_Va,    File StrCat[des_dir, "/as.pos"],        Name "A_s (Vs/m)" ];
      Print [ as_mag,   OnElementsOf Domain_Va,    File StrCat[des_dir, "/as_mag.pos"],    Name "A_s mag. (Vs/m)" ];
      Print [ am,       OnElementsOf Domain_Va,    File StrCat[des_dir, "/am.pos"],        Name "A_m (Vs/m)" ];
      Print [ am_mag,   OnElementsOf Domain_Va,    File StrCat[des_dir, "/am_mag.pos"],    Name "A_m mag. (Vs/m)" ];
      Print [ ag,       OnElementsOf Domain_V,      File StrCat[des_dir, "/ag.pos"],        Name "A_g (Vs/m)" ];
      Print [ ag_mag,   OnElementsOf Domain_V,      File StrCat[des_dir, "/ag_mag.pos"],    Name "A_g mag. (Vs/m)" ];
      Print [ a,        OnElementsOf Domain_V,      File StrCat[des_dir, "/a.pos"],         Name "Total A (Vs/m)" ];
      Print [ a_mag,    OnElementsOf Domain_V,      File StrCat[des_dir, "/a_mag.pos"],     Name "Total A mag. (Vs/m)" ];

      // Surface currents
      Print [ nxhs,     OnElementsOf Boundary_Gamma, File StrCat[des_dir, "/nxhs.pos"],     Name "nxhs (A/m)" ];
      Print [ nxhm,     OnElementsOf Boundary_Gamma, File StrCat[des_dir, "/nxhm.pos"],     Name "nxhm (A/m)" ];
      Print [ Jg,       OnElementsOf Boundary_Gamma, File StrCat[des_dir, "/Jg.pos"],       Name "J_g (A/m)" ];

      // Source current
      Print [ Jsrc,     OnElementsOf Domain_Coil_Total,   File StrCat[des_dir, "/Jsrc.pos"],      Name "Jsrc (A/m^2)" ];

      // B-fields
      Print [ bs,       OnElementsOf Domain_Va,    File StrCat[des_dir, "/bs.pos"],        Name "B_s (T)" ];
      Print [ bs_mag,   OnElementsOf Domain_Va,    File StrCat[des_dir, "/bs_mag.pos"],    Name "B_s mag. (T)" ];
      Print [ bm,       OnElementsOf Domain_Va,    File StrCat[des_dir, "/bm.pos"],        Name "B_m (T)" ];
      Print [ bm_mag,   OnElementsOf Domain_Va,    File StrCat[des_dir, "/bm_mag.pos"],    Name "B_m mag. (T)" ];
      Print [ bg,       OnElementsOf Domain_V,      File StrCat[des_dir, "/bg.pos"],        Name "B_g (T)" ];
      Print [ bg_mag,   OnElementsOf Domain_V,      File StrCat[des_dir, "/bg_mag.pos"],    Name "B_g mag. (T)" ];
      Print [ b,        OnElementsOf Domain_V,      File StrCat[des_dir, "/b.pos"],         Name "Total B (T)" ];
      Print [ b_mag,    OnElementsOf Domain_V,      File StrCat[des_dir, "/b_mag.pos"],     Name "Total B mag. (T)" ];
    }//Operation
  }//Name

}//PostOperation
