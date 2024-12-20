from dependencies import *


# /*--------------------------------*- C++ -*----------------------------------*\
# | =========                                               ____/_________\____     _.*_*.             |
# | \\      /      F ield           |   |  S tructural      ||__|/\|___|/\|__||      \ \ \\.           |
# |  \\    /       O peration       |___|  E ngineering &   ||__|/\|___|/\|__||       | | | \._        |
# |   \\  /        A nd                 |  E arthquake      ||__|/\|___|/\|__||      _/_/_/ | .\.__... |
# |    \\/         M anipulation    |___|  S imulation      ||__|/\|___|/\|__||   __/, / _ \___...     |
# |_________________________________________________________||  |/\| | |/\|  ||__/,_/__,_____/...______|
	# \*---------------------------------------------------------------------------*/

# The work within this thesis was funded by the National Science Foundation (NSF) and Joy Pauschke (program manager) through Grants CMMI-1726326, CMMI-1933184, and CMMI-2131111. 
# Thank you to NHERI Computational Modeling and Simulation Center (SimCenter), as well as their developers, funding sources, and staff for their continued support. 
# It was a great experience to work with the SimCenter to implement this tool allowing for partitioned coupling of OpenSees and OpenFOAM as part of a digital-twin module within the NHERI SimCenter Hydro-UQ framework.
# Much of the development work of the research tool presented was conducted using University of Washington's HYAK Supercomputing resources. 
# Thank you to UW HYAK and to the support staff of the UW HPC resources for their maintenance of the supercomputer cluster and for offering a stable platform for HPC development 
# and computation, as well as for all of the great support over the last few years.  



sys.path.insert(0, './FOAMySees')

#########################################################################################

noOpenSeessubsteps=config.numOpenSeesStepsPerCouplingTimestep
noOpenFOAMsubsteps=config.numOpenFOAMStepsPerCouplingTimestep
explicitStabilizationAttempt=0
with open('FOAMySeesCouplingDriver.log', 'a+') as f:
	print('@ line'+str(30),file=f)

#########################################################################################
OpenSees_dt=config.SolutionDT
with open('FOAMySeesCouplingDriver.log', 'a+') as f:
	print('OpenSees Solution Maximum dT=',config.SolutionDT,file=f)
	print("Initializing FOAMySees Coupling Driver",file=f)



#################################################################################################	
parser = argparse.ArgumentParser()
parser.add_argument("configurationFileName", help="Name of the xml config file.", nargs='?', type=str,
					default="precice-config.xml")
parser.add_argument("CouplingDataProjectionMesh", help="Name of the file to load as the Coupling Data Projection Mesh", nargs='?', type=str,
					default="CouplingDataProjectionMesh.obj")
try:
	args = parser.parse_args()
except SystemExit:
	with open('FOAMySeesCouplingDriver.log', 'a+') as f:
		print("Something is wrong! Exiting. The argument parser is telling you that you need to include something...",file=f)


#################################################################################################	

#################################################################################################
FOAMySees=FOAMySeesInstance(OpenSees_dt,config)
#################################################################################################
configFileName = args.configurationFileName
with open('FOAMySeesCouplingDriver.log', 'a+') as f:
	print('@ line'+str(60),file=f)
CouplingDataProjectionMesh = args.CouplingDataProjectionMesh
#################################################################################################
if __name__ == '__main__':# and rank==0:

	solverName = "FOAMySeesCouplingDriver"  
	#################################################################################################	
	# measuring the length of the coupled nodes list 
	N = len(FOAMySees.coupledNodes) # number of coupled ops.nodes
	# reporting
	with open('FOAMySeesCouplingDriver.log', 'a+') as f:
		print("Number of Coupled OpenSees Nodes: " + str(N),file=f)
	#################################################################################################
	# reporting
	with open('FOAMySeesCouplingDriver.log', 'a+') as f:
		print("Configuring preCICE library",file=f)
	interface = precice.Interface(solverName, configFileName, 0, 1)
	with open('FOAMySeesCouplingDriver.log', 'a+') as f:
		print("preCICE successfully configured",file=f)
	#################################################################################################
	# returning the dimensions defined by the coupling library
	dimensions = interface.get_dimensions()
	dimensions=3 # overruling that
	#################################################################################################

	isSurfLoaded=0	# initializing this
	with open('FOAMySeesCouplingDriver.log', 'a+') as f:
		print('@ line'+str(90),file=f)	
	while isSurfLoaded==0:	# waiting until the Coupling Data Projection Mesh file has been successfully loaded
		try:
			#Using PyVista to Read STL or OBJ containing points of Coupling Surface for CFD Mesh 
			# Branches = pv.read("FluidCouplingSurface.obj").points
		
			#Using PyVista to Calculate Cell Centers of faces 
			Branches= pv.read(CouplingDataProjectionMesh).cell_centers().points
			isSurfLoaded=1	# woo! we are good to move forward
		except: 
			# still not loaded
			isSurfLoaded=0
	with open('FOAMySeesCouplingDriver.log', 'a+') as f:
		print('@ line'+str(90),file=f)	
	#################################################################################################		  
	# using SciPy to calculate the K-means clustering  
		#   .... from scipy.spatial import KDTree
	Tree=KDTree(FOAMySees.nodeLocs)
	BranchToNodeRelationships=Tree.query(Branches)[1]
	CellToNodeRelationships=Tree.query(Branches)[1]		

	#################################################################################################
	# initializing a bunch of arrays of the same size
	verticesDisplacement=Branches
	verticesForce=Branches
	verticesDisplacement=np.array(verticesDisplacement)
	verticesForce=np.array(verticesForce)
	FOAMySees.verticesDisplacement=verticesDisplacement
	FOAMySees.verticesForce=verticesForce
	BranchTransform=np.zeros(np.shape(verticesDisplacement))
	Displacement = np.zeros(np.shape(verticesDisplacement))	
	Forces = np.zeros(np.shape(verticesForce))
	FOAMySees.moment = np.zeros([len(FOAMySees.coupledNodes),3])
	#################################################################################################
	# building the FEM node to Branch Group relationships
	with open('FOAMySeesCouplingDriver.log', 'a+') as f:
		print('@ line'+str(120),file=f)	

	NodeToBranchNodeRelationships=[]
	NodeToCellFaceCenterRelationships=[]
	for n in range(len(FOAMySees.nodeLocs)):
		NodeToCellFaceCenterRelationships.append([n])
	for node in range(len(CellToNodeRelationships)):
		NodeToCellFaceCenterRelationships[CellToNodeRelationships[node]].append(node)		
	for n in range(len(FOAMySees.nodeLocs)):
		NodeToBranchNodeRelationships.append([n])
	for node in range(len(BranchToNodeRelationships)):
		NodeToBranchNodeRelationships[BranchToNodeRelationships[node]].append(node)
	FOAMySees.NodeToBranchNodeRelationships=NodeToBranchNodeRelationships
	FOAMySees.NodeToCellFaceCenterRelationships=NodeToCellFaceCenterRelationships		
	#################################################################################################	
	# reporting to file
	with open('BranchesLOCS.log', 'a+') as f:
		f.seek(0)
		f.truncate()
		print(NodeToBranchNodeRelationships,file=f)
		print(verticesDisplacement,file=f)
		print(np.shape(verticesDisplacement),file=f)
		print(NodeToCellFaceCenterRelationships,file=f)
		print(verticesForce,file=f)
		print(np.shape(verticesForce),file=f)
	
	#################################################################################################
	
	# performing initial gravity and structural analysis routines

	with open('FOAMySeesCouplingDriver.log', 'a+') as f:
		print('@ line'+str(150),file=f)		
	if FOAMySees.config.ApplyGravity=="Yes":
		FOAMySees.prelimAnalysis.runGravity(FOAMySees)
		Displacement=FOAMySees.projectDisplacements(Displacement)
	#################################################################################################
	#retrieving displacements from these to apply as initial conditions in OpenFOAM
	
	if FOAMySees.config.runPreliminaryAnalysis=="Yes":
		FOAMySees.prelimAnalysis.runPreliminaryAnalysis(FOAMySees)
		Displacement=FOAMySees.projectDisplacements(Displacement)
	
	#################################################################################################		
	with open('FOAMySeesCouplingDriver.log', 'a+') as f:
		print("FOAMySees Coupling Driver: Initializing Coupling with preCICE",file=f)

	# preCICE action - returns ID of mesh 
	meshID = interface.get_mesh_id("Coupling-Data-Projection-Mesh")

	# preCICE action - assigns locations to mesh nodes
	vertexIDsDisplacement = interface.set_mesh_vertices(meshID, verticesDisplacement)

	# preCICE action - returns ID of data array
	displacementID = interface.get_data_id("Displacement", meshID)

	# force and displacement are currently applied and calculated at the face centers of the OpenFOAM patch cells
	vertexIDsForce = vertexIDsDisplacement
	

	with open('FOAMySeesCouplingDriver.log', 'a+') as f:
		print('@ line'+str(180),file=f)	

	# preCICE action - returns ID of data array
	forceID = interface.get_data_id("Force", meshID)

	# preCICE action - gives initial coupling timestep, initializes coupling
	precice_dt = interface.initialize()

	#################################################################################################

	# reporting
	with open('FOAMySeesCouplingDriver.log', 'a+') as f:
		print('OpenSeesPy (FOAMySees Projected) Initial Displacements (from preliminary analysis)',Displacement,file=f)

	
	#################################################################################################
	# preCICE action
	if interface.is_action_required(action_write_initial_data()):
		with open('FOAMySeesCouplingDriver.log', 'a+') as f:
			print('Initial Displacement',Displacement,file=f)
		interface.write_block_vector_data(displacementID, vertexIDsDisplacement, Displacement)
		interface.mark_action_fulfilled(action_write_initial_data())

	#################################################################################################
	# preCICE action
	interface.initialize_data()
	
	#################################################################################################	
	# Cleaning up and making storage directories for OpenSees
	Popen('rm -rf SeesCheckpoints', shell=True, stdout=DEVNULL).wait()
	Popen('mkdir SeesCheckpoints', shell=True, stdout=DEVNULL).wait()
	Popen('mkdir SeesCheckpoints/checkpoints/', shell=True, stdout=DEVNULL).wait()
	
	
	#################################################################################################	
	# preCICE action	
	if interface.is_read_data_available():
		force = interface.read_block_vector_data(forceID, vertexIDsForce)

	#################################################################################################
	# preCICE action	
	if interface.is_action_required(action_write_iteration_checkpoint()):
		ops.database('File',"SeesCheckpoints/checkpoint")
		ops.save(0)
		interface.mark_action_fulfilled(action_write_iteration_checkpoint())
		thisTime=copy.deepcopy(ops.getTime())
		with open('What is Happening With OpenSees.log', 'a+') as f:
			print('Wrote a checkpoint at opensees time = ',thisTime,file=f)		
		
	#################################################################################################	
	# creating a PVD file for the initial state of the OpenSees model
	FOAMySees.createRecorders.createPVDRecorder(FOAMySees)
	
	#################################################################################################
	# creating all recorders for the initial state of the OpenSees model
	FOAMySees.createRecorders.createNodeRecorders(FOAMySees,FOAMySees.nodeRecInfoList)				

	#if interface.is_action_required(action_read_initial_data()):
	#	print('Initial Force',Force)
	#	interface.read_block_vector_data(forceID, vertexIDsForce, Force)
	#	interface.mark_action_fulfilled(action_read_initial_data())
	
	#################################################################################################	
	# intializing some things
	stepOut=1
	FOAMySees.lastForces=copy.deepcopy(FOAMySees.force)
	FOAMySees.lastMoments=copy.deepcopy(FOAMySees.moment)
	observe_node_num=1
	tOUT=0
	tLIST=[]
	StepCheck=1
	newStep=1
	FOAMySees.lastForceandmoment=copy.deepcopy(FOAMySees.forceandmoment)
	LastForces=copy.deepcopy(Forces)
	LastDisplacement=copy.deepcopy(Displacement)
	iteration=1
	#################################################################################################
	# creating the OpenSees analysis objects, if they have not been created already	
	FOAMySees.timeInt()

	#################################################################################################	
	# defining the number of OpenSees substeps
	FOAMySees.CurrSteps=1

	#################################################################################################
	# preCICE action - entering the coupling loop
	while interface.is_coupling_ongoing():
		#################################################################################################
		# preCICE action - checking if a database needs to be written (implicit only)
		if (interface.is_action_required(precice.action_write_iteration_checkpoint())) or newStep==1:

			# summons database save in OpenSees
			FOAMySees.writeCheckpoint(stepOut)

			# telling preCICE we are done restoring the checkpoint
			interface.mark_action_fulfilled(precice.action_write_iteration_checkpoint())

		#################################################################################################		
		# creating OpenSees recorders for the timestep				
		FOAMySees.createRecorders.createNodeRecorders(FOAMySees,FOAMySees.nodeRecInfoList)


		#################################################################################################
		# gathering forces from preCICE
		Forces=interface.read_block_vector_data(forceID, vertexIDsForce)
	
		for substep in range(1,noOpenSeessubsteps+1):						
			currForces=(copy.deepcopy(Forces)-LastForces)*(substep/noOpenSeessubsteps) + LastForces

			#################################################################################################		
			# looping through the branch groups and determining applied FEM nodal forces
			for node in FOAMySees.NodeToCellFaceCenterRelationships:
				FOAMySees.force[node[0],:]=np.sum(currForces[node[1:],:],axis=0)
			#################################################################################################		
			# looping through the branch groups and determining applied FEM nodal moments
			FOAMySees.calculateUpdatedMoments(currForces)

			#################################################################################################		
			# stepping forward in time with a variableTransient time integration
			# the forces and moments are applied to the coupled nodes here
			StepCheck=FOAMySees.stepForward(FOAMySees.dt/noOpenSeessubsteps)
				   

			#################################################################################################		
			# reporting
			with open('FOAMySeesCouplingDriver.log', 'a+') as f:
				print(ops.getTime(),' = OpenSees time\n', substep,'/',noOpenSeessubsteps, ' = substep/noOpenSeessubsteps',file=f)

			#################################################################################################
			# did the step converge?
			if (StepCheck!=0):
				with open('FOAMySeesCouplingDriver.log', 'a+') as f:
					print(' OpenSeesPy Step did not converge :(',FOAMySees.thisTime,file=f)
				
		#################################################################################################			
		# projecting the displacement field from OpenSees to the coupling data projection mesh				
		Displacement=FOAMySees.projectDisplacements(Displacement)
		
		
		
		#################################################################################################			
		# calculating the Work
				
		FOAMySees.WorkIn=np.sum(FOAMySees.forceandmoment*(FOAMySees.displacement-FOAMySees.lastDisplacements))
		FOAMySees.WorkOut=0
		
		
		for substep in range(1,noOpenFOAMsubsteps+1):
			FOAMySees.WorkOut+=np.sum((Forces)*(Displacement-LastDisplacement)*(1/noOpenFOAMsubsteps))
			with open('FOAMySeesCouplingDriver.log', 'a+') as f:
				print('iteration:',iteration,', Time: ',ops.getTime(),'Work In/Out -- error (%)',(FOAMySees.WorkIn-FOAMySees.WorkOut)/FOAMySees.WorkIn,' In/Out (Ratio)',FOAMySees.WorkIn/FOAMySees.WorkOut,', Work In (Joules): ',FOAMySees.WorkIn,', Work Out (Joules): ',FOAMySees.WorkOut,file=f)
		
			#################################################################################################
			# sending the projected displacements to preCICE to be mapped to OpenFOAM during the next iteration or timestep
			interface.write_block_vector_data(displacementID, vertexIDsDisplacement, LastDisplacement+(Displacement-LastDisplacement)*(substep/noOpenFOAMsubsteps))
			#################################################################################################		
			# Advancing the coupling scheme -
#				precice_dt=interface.advance(precice_dt)			
			precice_dt_return=interface.advance(precice_dt/noOpenFOAMsubsteps)
			with open('FOAMySeesCouplingDriver.log', 'a+') as f:
				print('OpenFOAM substep ', substep,' of ', noOpenFOAMsubsteps, 'OpenSees time: ', ops.getTime(), 'OpenFOAM time: ', ops.getTime() -(substep-1)*precice_dt/noOpenFOAMsubsteps ,file=f)
		
		#  checking if residuals<tolerances & performing accleration (implicit), no accel/iter (explicit)	
		#################################################################################################		
		# checking with preCICE to see if we have converged, or if we need to try the timestep again with new coupling data
		if interface.is_action_required(precice.action_read_iteration_checkpoint()):
			#FOAMySees.CurrSteps+=1				
			FOAMySees.readCheckpoint(stepOut)
			# reading the previously saved database
			StepCheck=0
			# adding one to the iteration counter
			iteration+=1
			# letting preCICE know we are finished going back in time
			interface.mark_action_fulfilled(precice.action_read_iteration_checkpoint())		 			
		else:
			with open('FOAMySeesCouplingDriver.log', 'a+') as f:
				print(' Time: ',ops.getTime(),'Work In/Out -- error (%)',(FOAMySees.WorkIn-FOAMySees.WorkOut)/FOAMySees.WorkIn,' In/Out (Ratio)',FOAMySees.WorkIn/FOAMySees.WorkOut,', Work In (Joules): ',FOAMySees.WorkIn,', Work Out (Joules): ',FOAMySees.WorkOut,file=f)
			with open('WorkInAndOut.log', 'a+') as f:
				print(' Time: ',ops.getTime(),'Work In/Out -- error (%)',(FOAMySees.WorkIn-FOAMySees.WorkOut)/FOAMySees.WorkIn,' In/Out (Ratio)',FOAMySees.WorkIn/FOAMySees.WorkOut,', Work In (Joules): ',FOAMySees.WorkIn,', Work Out (Joules): ',FOAMySees.WorkOut,file=f)
			with open('WorkInAndArray.log', 'a+') as f:
				print(ops.getTime(),(FOAMySees.WorkIn-FOAMySees.WorkOut)/FOAMySees.WorkIn,FOAMySees.WorkIn/FOAMySees.WorkOut,FOAMySees.WorkIn,FOAMySees.WorkOut,file=f)	
			LastForces=copy.deepcopy(Forces)
			LastDisplacement=copy.deepcopy(Displacement)
			FOAMySees.StepsPerFluidStep=1
			
			
			#################################################################################################
			# saving these for some sort of surrogate model?
			FOAMySees.lastForceandmoment=copy.deepcopy(FOAMySees.forceandmoment)
			FOAMySees.lastForces=copy.deepcopy(FOAMySees.force)
			FOAMySees.lastDisplacements=copy.deepcopy(FOAMySees.displacement)	
			
			iteration=1
			# we are converged, or have given up!
			#################################################################################################			
			# doing some house keeping
			Popen("ls -t SeesCheckpoints/checkpoints/*| tail -n +100 | xargs -d '\n' rm", shell=True, stdin=None, stdout=None, stderr=None,)
			newStep=1
			tOUT+= precice_dt
			FOAMySees.CurrSteps=1
			stepOut+=1
			FOAMySees.StepsPerFluidStep=1
	
			#################################################################################################
			#ops.wipe()
			# calling all the recorders made
			ops.record()
			FOAMySees.createRecorders.appendRecords(FOAMySees,FOAMySees.nodeRecInfoList)		
			if tOUT>=FOAMySees.config.SeesVTKOUTRate:
				tOUT=0
				FOAMySees.createRecorders.createPVDRecorder(FOAMySees)

			#################################################################################################
	with open('FOAMySeesCouplingDriver.log', 'a+') as f:
		print("Exiting FOAMySees Coupling Driver",file=f)

	interface.finalize()
