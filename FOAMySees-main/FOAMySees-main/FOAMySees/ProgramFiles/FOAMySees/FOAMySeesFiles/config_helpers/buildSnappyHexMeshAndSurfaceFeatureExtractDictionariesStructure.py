def buildSnappyHexMeshAndSurfaceFeatureExtractDictionariesStructure(nameOfCoupledPatchOrSurfaceFile,writeHere):
	print('Building SHM and Surface Feature Extract Dictionaries')
	
	patchLayers='''
			{}'''.format(nameOfCoupledPatchOrSurfaceFile)+'''
			{
				nSurfaceLayers 1;
			}
				'''
				
	geomSHM='''
			{}'''.format(nameOfCoupledPatchOrSurfaceFile)+'''
		{
			type triSurfaceMesh;
			file "'''+'''{}'''.format(nameOfCoupledPatchOrSurfaceFile)+'''.stl";
		}
			''' 
			
	featExtFeats='''
			{
				file "'''+'''{}'''.format(nameOfCoupledPatchOrSurfaceFile)+'''.eMesh";
				level 3;
			}
			'''
	 
	refineSurfs='''
			{}'''.format(nameOfCoupledPatchOrSurfaceFile)+'''
			{
				level	(1 3);
				patchInfo
				{
					type wall;
				}
			}
			'''
	
	SHMDict=['''
	FoamFile
	{
		version	 2.0;
		format	  ascii;
		class	   dictionary;
		object	  snappyHexMeshDict;
	}
	// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

	// Which of the steps to run
	castellatedMesh true;
	snap			true;
	addLayers	   false;


	// Geometry. Definition of all surfaces. All surfaces are of class
	// searchableSurface.
	// Surfaces are used
	// - to specify refinement for any mesh cell intersecting it
	// - to specify refinement for any mesh cell inside/outside/near
	// - to 'snap' the mesh boundary to the surface
	geometry
	{
		'''+geomSHM+'''
	};

	// Settings for the castellatedMesh generation.
	castellatedMeshControls
	{
		// Refinement parameters
		// ~~~~~~~~~~~~~~~~~~~~~

		// If local number of cells is >= maxLocalCells on any processor
		// switches from from refinement followed by balancing
		// (current method) to (weighted) balancing before refinement.
		maxLocalCells 10000000;

		// Overall cell limit (approximately). Refinement will stop immediately
		// upon reaching this number so a refinement level might not complete.
		// Note that this is the number of cells before removing the part which
		// is not 'visible' from the keepPoint. The final number of cells might
		// actually be a lot less.
		maxGlobalCells 200000000;

		// The surface refinement loop might spend lots of iterations refining just a
		// few cells. This setting will cause refinement to stop if <= minimumRefine
		// are selected for refinement. Note: it will at least do one iteration
		// (unless the number of cells to refine is 0)
		minRefinementCells 10;

		// Number of buffer layers between different levels.
		// 1 means normal 2:1 refinement restriction, larger means slower
		// refinement.
		nCellsBetweenLevels 2;

		// Explicit feature edge refinement
		// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

		// Specifies a level for any cell intersected by its edges.
		// This is a featureEdgeMesh, read from constant/triSurface for now.
		features
		(
			'''+featExtFeats+'''
		);

		// Surface based refinement
		// ~~~~~~~~~~~~~~~~~~~~~~~~

		// Specifies two levels for every surface. The first is the minimum level,
		// every cell intersecting a surface gets refined up to the minimum level.
		// The second level is the maximum level. Cells that 'see' multiple
		// intersections where the intersections make an
		// angle > resolveFeatureAngle get refined up to the maximum level.

		refinementSurfaces
		{
	'''+refineSurfs+'''
		}

		// Resolve sharp angles
		resolveFeatureAngle 30;

		// Region-wise refinement
		// ~~~~~~~~~~~~~~~~~~~~~~

		// Specifies refinement level for cells in relation to a surface. One of
		// three modes
		// - distance. 'levels' specifies per distance to the surface the
		//   wanted refinement level. The distances need to be specified in
		//   descending order.
		// - inside. 'levels' is only one entry and only the level is used. All
		//   cells inside the surface get refined up to the level. The surface
		//   needs to be closed for this to be possible.
		// - outside. Same but cells outside.

		refinementRegions
		{
		}

		// Mesh selection
		// ~~~~~~~~~~~~~~

		// After refinement patches get added for all refinementSurfaces and
		// all cells intersecting the surfaces get put into these patches. The
		// section reachable from the locationInMesh is kept.
		// NOTE: This point should never be on a face, always inside a cell, even
		// after refinement.
		locationInMesh (1.01 0.010 0.001);

		// Whether any faceZones (as specified in the refinementSurfaces)
		// are only on the boundary of corresponding cellZones or also allow
		// free-standing zone faces. Not used if there are no faceZones.
		allowFreeStandingZoneFaces true;
	}
		
	snapControls
	{
		//- Number of patch smoothing iterations before finding correspondence
		//  to surface
		nSmoothPatch 5; // or 15; 
		
		//- Relative distance for points to be attracted by surface feature point
		//  or edge. True distance is this factor times local
		//  maximum edge length.
		tolerance 0.1;  // or 0.1;
		
		//- Number of mesh displacement relaxation iterations.
		nSolveIter 10;

		//- Maximum number of snapping relaxation iterations. Should stop
		//  before upon reaching a correct mesh.
		nRelaxIter 50;

		// Feature snapping

			//- Number of feature edge snapping iterations.
			//  Leave out altogether to disable.
			nFeatureSnapIter 20;

			//- Detect (geometric only) features by sampling the surface
			//  (default=false).
			implicitFeatureSnap true;

			//- Use castellatedMeshControls::features (default = true)
			explicitFeatureSnap true;

			//- Detect points on multiple surfaces (only for explicitFeatureSnap)
			multiRegionFeatureSnap true;
	}

	// Settings for the layer addition.
	addLayersControls
	{
		// Are the thickness parameters below relative to the undistorted
		// size of the refined cell outside layer (true) or absolute sizes (false).
		relativeSizes true;

		// Per final patch (so not geometry!) the layer information
		layers
		{
	'''+patchLayers+'''
		}
		// Maximum non-orthogonality allowed; 180 disables
		maxNonOrtho 65;
		// Expansion factor for layer mesh
		expansionRatio 1.0;

		// Wanted thickness of final added cell layer. If multiple layers
		// is the thickness of the layer furthest away from the wall.
		// Relative to undistorted size of cell outside layer.
		// See relativeSizes parameter.
		finalLayerThickness 0.5;

		// Minimum thickness of cell layer. If for any reason layer
		// cannot be above minThickness do not add layer.
		// Relative to undistorted size of cell outside layer.
		minThickness 0.25;

		// If points get not extruded do nGrow layers of connected faces that are
		// also not grown. This helps convergence of the layer addition process
		// close to features.
		// Note: changed(corrected) w.r.t 17x! (didn't do anything in 17x)
		nGrow 0;

		// Advanced settings

		// When not to extrude surface. 0 is flat surface, 90 is when two faces
		// are perpendicular
		featureAngle 60;

		// At non-patched sides allow mesh to slip if extrusion direction makes
		// angle larger than slipFeatureAngle.
		slipFeatureAngle 30;

		// Maximum number of snapping relaxation iterations. Should stop
		// before upon reaching a correct mesh.
		nRelaxIter 3;

		// Number of smoothing iterations of surface normals
		nSmoothSurfaceNormals 1;

		// Number of smoothing iterations of interior mesh movement direction
		nSmoothNormals 3;

		// Smooth layer thickness over surface patches
		nSmoothThickness 10;

		// Stop layer growth on highly warped cells
		maxFaceThicknessRatio 0.5;

		// Reduce layer growth where ratio thickness to medial
		// distance is large
		maxThicknessToMedialRatio 0.3;

		// Angle used to pick up medial axis points
		// Note: changed(corrected) w.r.t 17x! 90 degrees corresponds to 130 in 17x.
		minMedianAxisAngle 90;

		// Create buffer region for new layer terminations
		nBufferCellsNoExtrude 0;

		// Overall max number of layer addition iterations. The mesher will exit
		// if it reaches this number of iterations; possibly with an illegal
		// mesh.
		nLayerIter 50;
	}

	// Generic mesh quality settings. At any undoable phase these determine
	// where to undo.
	meshQualityControls
	{
		
		maxNonOrtho	65;
		maxBoundarySkewness	20;
		maxInternalSkewness	4;
		maxConcave	80;
		minFlatness	0.5;
		minVol 1.00E-13;
		minTetQuality 1.00E-13;
		minArea	-1;
		minTwist 0.05;
		minDeterminant 0.001;
		minFaceWeight 0.05;
		minVolRatio	0.01;
		minTriangleTwist -1;
		nSmoothScale 4;
		errorReduction 0.75;

		// Advanced

		//- Number of error distribution iterations
		nSmoothScale 4;
		//- amount to scale back displacement at error points
		errorReduction 0.5;
	}

	// Settings for the snapping.
	// Merge tolerance. Is fraction of overall bounding box of initial mesh.
	// Note: the write tolerance needs to be higher than this.
	mergeTolerance 1e-6;

	// ************************************************************************* //
	''']

	with open(writeHere+'/system/snappyHexMeshDict','w') as f:
		f.seek(0)
		for x in SHMDict:
			for line in x:
				f.write(line)
				f.truncate()
				

	surfaceFeats='''{}'''.format(nameOfCoupledPatchOrSurfaceFile)+'''.stl
	{
		// How to obtain raw features (extractFromFile || extractFromSurface)
		extractionMethod	extractFromSurface;

		extractFromSurfaceCoeffs
		{
			// Mark edges whose adjacent surface normals are at an angle less
			// than includedAngle as features
			// - 0  : selects no edges
			// - 180: selects all edges
			includedAngle   180;
		}

		subsetFeatures
		{
			// Keep nonManifold edges (edges with >2 connected faces)
			nonManifoldEdges	   no;

			// Keep open edges (edges with 1 connected face)
			openEdges	   yes;
		}


		// Write options

			// Write features to obj format for postprocessing
			writeObj				yes;
	}'''
	
	   
	SFEDict=['''
	FoamFile
	{
		version	 2.0;
		format	  ascii;
		class	   dictionary;
		object	  surfaceFeatureExtractDict;
	}
	// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
	''',surfaceFeats,'''

	// ************************************************************************* //
	''']
	with open(writeHere+'/system/surfaceFeatureExtractDict','w') as f:
		f.seek(0)
		for x in SFEDict:
			for line in x:
				f.write(line)
				f.truncate()
				
