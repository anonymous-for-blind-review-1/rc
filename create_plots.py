# Import python libraries
import matplotlib.pyplot as plt

# Import RapidChiplet Files
import helpers as hlp

colors = {	"C2C" : "#000099",
			"C2M" : "#009900",
			"C2I" : "#990000",
			"M2I" : "#990099"
		 }

markers = {	"C2C" : "o",
			"C2M" : "^",
			"C2I" : "s",
			"M2I" : "d"
		 }

maxsize = 10


def create_latency_plot():
	(fig, ax) = plt.subplots(1, 1, figsize = (6, 3))
	plt.subplots_adjust(left=0.15, right = 0.975, top = 0.9, bottom = 0.19)


	# Plot Mesh	
	sizes = list(range(2,maxsize + 1))
	traffic_classes = ["C2C","C2M","C2I","M2I"]
	mesh_data = {tc : {} for tc in traffic_classes}
	for x in sizes:
		path = "results/mesh_%dx%d.json" % (x,x)	
		results = hlp.read_file(path)
		for tc in traffic_classes:
			mesh_data[tc][x] = results["ici_latency"][tc]["avg"]	
	for tc in traffic_classes:
		xvals, yvals = zip(*[(x, mesh_data[tc][x]) for x in sizes if x in mesh_data[tc]])
		ax.plot(xvals, yvals, label = tc, color = colors[tc], marker = markers[tc], markersize = 2)

	# Plot CMesh	
	sizes_ = list(range(2,int(maxsize/2) + 1))
	traffic_classes = ["C2C","C2M","C2I","M2I"]
	cmesh_data = {tc : {} for tc in traffic_classes}
	for x in sizes_:
		path = "results/cmesh_%dx%d.json" % (x,x)	
		results = hlp.read_file(path)
		for tc in traffic_classes:
			cmesh_data[tc][2*x] = results["ici_latency"][tc]["avg"]	
	for tc in traffic_classes:
		xvals, yvals = zip(*[(2*x, cmesh_data[tc][2*x]) for x in sizes_ if (2*x) in cmesh_data[tc]])
		ax.plot(xvals, yvals, label = tc, color = colors[tc], marker = markers[tc], markersize = 2)

	ax.grid()
	ax.legend()
	ax.set_xticks(sizes)
	ax.set_xticklabels([x**2 for x in sizes])
	ax.set_xlabel("Number of compute chiplets")
	ax.set_ylabel("Latency [cycles]")
	ax.set_yscale("log")

	plt.savefig("plots/latency.pdf")

def create_runtime_plot():
	(fig, ax) = plt.subplots(1, 1, figsize = (6, 3))
	plt.subplots_adjust(left=0.12, right = 0.995, top = 0.95, bottom = 0.15)

	# Plot Mesh	
	sizes = list(range(2,maxsize + 1))
	mesh_data = {}
	for x in sizes:
		path = "results/mesh_%dx%d.json" % (x,x)	
		results = hlp.read_file(path)
		for key in results["runtime"]:
			if key not in mesh_data:
				mesh_data[key] = []
			mesh_data[key].append(results["runtime"][key])
	for key in mesh_data:
		xvals = sizes
		yvals = mesh_data[key]
		ax.plot(xvals, yvals, label = key, markersize = 3, marker = "o")

	# Plot
	ax.grid()
	ax.legend()
	ax.set_xticks(sizes)
	ax.set_xticklabels([x**2 for x in sizes])
	ax.set_xlabel("Number of compute chiplets")
	ax.set_ylabel("Runtime [s]")
	ax.set_yscale("log")
	ax.set_yticks([10**x for x in range(-6,2)])
	ax.set_xlim(1.5,maxsize + 0.5)
	ax.set_ylim(1e-6,1e1)

	plt.savefig("plots/runtime.pdf")

def create_speedup_plot():
	(fig, ax) = plt.subplots(1, 1, figsize = (6, 3))
	plt.subplots_adjust(left=0.12, right = 0.995, top = 0.95, bottom = 0.15)

	# Plot Mesh	
	sizes = list(range(2,maxsize + 1))
	mesh_data = []
	for x in sizes:
		rc_path = "results/mesh_%dx%d.json" % (x,x)	
		bs_path = "results/sim_mesh_%dx%d.json" % (x,x)	
		rc_results = hlp.read_file(rc_path)
		bs_results = hlp.read_file(bs_path)
		rc_time = rc_results["runtime"]["total_runtime"]
		bs_time = sum([bs_results[x]["total_run_time"] for x in bs_results])
		mesh_data.append(bs_time / rc_time)
	ax.plot(sizes, mesh_data, markersize = 3, marker = "o")

	# Plot
	ax.grid(True, which='both')
	ax.legend()
	ax.set_xticks(sizes)
	ax.set_xticklabels([x**2 for x in sizes])
	ax.set_xlabel("Number of compute chiplets")
	ax.set_ylabel("Speedup")
	ax.set_yscale("log")
	ax.set_xlim(1.5,maxsize + 0.5)
	ax.set_ylim(1e2,1e5)
	plt.savefig("plots/speedup.pdf")

def create_accuracy_plot():
	(fig, ax) = plt.subplots(1, 1, figsize = (6, 3))
	plt.subplots_adjust(left=0.12, right = 0.995, top = 0.95, bottom = 0.15)

	# Plot Mesh	
	sizes = list(range(2,maxsize + 1))
	mesh_data_lat = []
	mesh_data_tp = []
	for x in sizes:
		rc_path = "results/mesh_%dx%d.json" % (x,x)	
		bs_path = "results/sim_mesh_%dx%d.json" % (x,x)	
		rc_results = hlp.read_file(rc_path)
		bs_results = hlp.read_file(bs_path)
		rc_lat = rc_results["ici_latency"]["C2C"]["avg"]
		bs_lat = bs_results["0.001"]["packet_latency"]["avg"]
		rc_tp = rc_results["ici_throughput"]["C2C"]["fraction_of_theoretical_peak"]
		bs_tp = max([float(key) for key in bs_results])
		mesh_data_lat.append((rc_lat - bs_lat) * 100 / bs_lat)
		mesh_data_tp.append((rc_tp - bs_tp) * 100 / bs_tp)
	ax.plot(sizes, mesh_data_lat, markersize = 3, marker = "o", color = "#009900", label = "Latency")
	ax.plot(sizes, mesh_data_tp, markersize = 3, marker = "o", color = "#000099", label = "Throughput")

	# Plot
	ax.grid(True, which='both')
	ax.legend()
	ax.set_xticks(sizes)
	ax.set_xticklabels([x**2 for x in sizes])
	ax.set_xlabel("Number of compute chiplets")
	ax.set_ylabel("Relative Error")
	ax.set_xlim(1.5,maxsize + 0.5)
	plt.savefig("plots/accuracy.pdf")

def create_value_plot():
	(fig, ax) = plt.subplots(1, 1, figsize = (6, 3))
	plt.subplots_adjust(left=0.12, right = 0.88, top = 0.95, bottom = 0.15)

	# Plot Mesh	
	sizes = list(range(2,maxsize + 1))
	mesh_data_lat_rc = []
	mesh_data_lat_bs = []
	mesh_data_tp_rc = []
	mesh_data_tp_bs = []
	for x in sizes:
		rc_path = "results/mesh_%dx%d.json" % (x,x)	
		bs_path = "results/sim_mesh_%dx%d.json" % (x,x)	
		rc_results = hlp.read_file(rc_path)
		bs_results = hlp.read_file(bs_path)
		mesh_data_lat_rc.append(rc_results["ici_latency"]["C2C"]["avg"])
		mesh_data_lat_bs.append(bs_results["0.001"]["packet_latency"]["avg"])
		mesh_data_tp_rc.append(rc_results["ici_throughput"]["C2C"]["fraction_of_theoretical_peak"])
		mesh_data_tp_bs.append(max([float(key) for key in bs_results]))

	ax.plot(sizes, mesh_data_lat_rc, markersize = 3, marker = "o", color = "#009900", label = "RapidChiplet")
	ax.plot(sizes, mesh_data_lat_bs, markersize = 3, marker = "o", color = "#000099", label = "BookSim")
	ax2 = ax.twinx()
	ax2.plot(sizes, mesh_data_tp_rc, markersize = 3, marker = "o", color = "#009900", label = "RapidChiplet")
	ax2.plot(sizes, mesh_data_tp_bs, markersize = 3, marker = "o", color = "#000099", label = "BookSim")


	# Plot
	ax.grid(True, which='both')
	ax.legend()
	ax.set_xticks(sizes)
	ax.set_xticklabels([x**2 for x in sizes])
	ax.set_xlabel("Number of compute chiplets")
	ax.set_ylabel("Latency [cycles]")
	ax.set_xlim(1.5,maxsize + 0.5)
	ax.set_ylim(bottom = 0)
	ax2.set_ylim(bottom = 0)
	plt.savefig("plots/values.pdf")


		
create_runtime_plot()
create_speedup_plot()
create_accuracy_plot()
create_value_plot()
