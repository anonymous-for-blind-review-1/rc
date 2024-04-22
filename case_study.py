import design_generator as dgen
import helpers as hlp
import rapid_chiplet as rc

import math
import time


def create_radix_map(n): 
	radix_map = {}
	for as_int in range(2**n):
		as_str = bin(as_int)[2:]
		as_str = '0'*(n-len(as_str)) + as_str
		vals = [1] + [i for i in range(2, n) if as_str[-i+1] == '1']
		port_count = [0 for i in range(n)]	
		for src in range(n):
			for ll in vals:
				dst = src + ll
				if dst < n:
					port_count[src] += 1
					port_count[dst] += 1
		radix_map[tuple(vals)] = max(port_count)
	return radix_map

# Create one chiplet for a certain sparse hamming graph topology
def create_chiplet_for_shg(R, C, SR, SC, row_radix_map, col_radix_map, base_area, phy_area, base_power, phy_power, tech, lat, n_cores):
	n_h_phys = row_radix_map[tuple([1] + SR)]
	n_v_phys = col_radix_map[tuple([1] + SC)]
	area = base_area + (n_h_phys + n_v_phys) * phy_area
	power = base_power + (n_h_phys + n_v_phys) * phy_power
	(width, height) = (math.sqrt(area), math.sqrt(area))
	h_phys = [{"x" : i * (width / (n_h_phys + 2)), "y" : height * 0.2} for i in range(1, n_h_phys + 1)]
	v_phys = [{"x" : width * 0.2, "y" : i * (height / (n_v_phys + 2))} for i in range(1, n_v_phys + 1)]
	phy_map = {"H%d" % i : i for i in range(n_h_phys)} | {"V%d" % (i) : n_h_phys + i for i in range(n_v_phys)}
	chiplet = {
		"dimensions" : {"x" : width,"y" : height},
		"type" : "compute",
		"phys" : h_phys + v_phys,
		"technology" : tech,
		"power" : power,
		"relay" : True,
		"internal_latency" : lat,
		"unit_count" : n_cores
	}
	return (chiplet, phy_map)

def create_design_for_shg(chiplet_file, placement_file, topology_file):
	design = {
		"technology_nodes_file" : "inputs/technology_nodes/example_technologies.json",
		"chiplets_file" : chiplet_file,
		"chiplet_placement_file" : placement_file,
		"ici_topology_file" : topology_file,
		"packaging_file" : "inputs/packaging/example_packaging_ops.json",
		"thermal_config" : "inputs/thermal_config/example_thermal_config.json",
		"booksim_config" : "inputs/booksim_config/example_booksim_config.json"
	}
	return design


def perform_case_study(R, C, base_area, phy_area, base_power, phy_power, tech, lat, n_cores, f_power, bump_density, nndw):
	# Internal config
	chiplet_name = "case_study_chiplet"
	chiplets_file = "inputs/chiplets/chiplets_case_study.json"
	placement_file = "inputs/chiplet_placements/placement_case_study.json"
	topology_file = "inputs/ici_topologies/topology_case_study.json"
	design_file = "inputs/designs/design_case_study.json"
	# Create radix map
	row_radix_map = create_radix_map(R)
	col_radix_map = create_radix_map(C)
	results = []
	# Iterate through all valid per-row connectivity patterns
	start_time = time.time()
	n_SR = 2**(R-2)
	for SR_int in range(n_SR):
		print("Evaluating SR %d of %d | Time Taken: %.2fs" % (SR_int, n_SR, time.time() - start_time))
		SR_str = bin(SR_int)[2:]
		SR_str = '0'*(R-2-len(SR_str)) + SR_str
		SR = [i for i in range(2, R) if SR_str[-i+1] == '1']
		# Iterate through all valid per-column connectivity patterns
		n_SC = 2**(C-2)
		for SC_int in range(n_SC):
			SC_str = bin(SC_int)[2:]
			SC_str = '0'*(C-2-len(SC_str)) + SC_str
			SC = [i for i in range(2, C) if SC_str[-i+1] == '1']
			# Generate chiplet and topology
			(chiplet, phy_map) = create_chiplet_for_shg(R, C, SR, SC, row_radix_map, col_radix_map, base_area, phy_area, base_power, phy_power, tech, lat, n_cores)
			chiplets = {chiplet_name : chiplet}
			hlp.write_file(chiplets_file, chiplets)
			(placement, topology) = dgen.generate_sparse_hamming_graph(R, C, SR, SC, chiplets, chiplet_name, phy_map)
			hlp.write_file(placement_file, placement)
			hlp.write_file(topology_file, topology)
			design = create_design_for_shg(chiplets_file, placement_file, topology_file)
			# Run experiment
			rc_results = rc.compute_metrics(
					design = design,
					compute_area = True,
					compute_power = True,
					compute_link = False,
					compute_cost = True,
					compute_latency = True,
					compute_throughput = True,
					compute_thermal = False,
					routing = "random")
			# RapidChiplet gives us the throughput as the maximum injection rate (relative throughput)
			# We want to compare the absolute throughput which depends on the number of ubumps per PHY 
			# which in turn depends on the available chiplet area per PHY
			n_phys = len(phy_map)
			area_per_phy = ((base_area + n_phys * phy_area) * (1.0-f_power)) / n_phys
			bumps_per_phy = int(area_per_phy * bump_density)
			relative_throughput = rc_results["ici_throughput"]["C2C"]["fraction_of_theoretical_peak"]		# I percentage of peak injection
			absolute_throughput = relative_throughput * (bumps_per_phy - nndw)								# In bits per cycle
			entry = {	"SR" : SR, 
						"SC" : SC, 
						"area" : rc_results["area_summary"]["total_interposer_area"], 
						"power" : rc_results["power_summary"]["total_power"], 
						"cost" : rc_results["manufacturing_cost"]["total_cost"], 
						"latency" : rc_results["ici_latency"]["C2C"]["avg"], 
						"throughput" : absolute_throughput, 
					}
			results.append(entry)
	hlp.write_file("results/case_study_results.json", results)


if __name__ == "__main__":
	perform_case_study(10, 10, 16, 1, 1.5, 0.1, "tech_1", 5, 4, 0.33, 50, 12)

