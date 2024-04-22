# Import python libraries
import os
import numpy as np
import matplotlib.pyplot as plt

# Import RapidChiplet Files
import helpers as hlp


colors = ["#990099","#999900","#000099","#006600","#00aa66","#22dd99","#990000","#0066cc","#66ccff","#000000"]
markers = ["o","d","s","x","+","^","*","D","p","h"]

# Create the runtime plot
def create_runtime_plot(max_size, reps):
	(fig, ax) = plt.subplots(1, 2, figsize = (6, 3))
	plt.subplots_adjust(left=0.12, right = 0.995, top = 0.92, bottom = 0.25, wspace = 0.35)

	sizes = list(range(2,max_size + 1))
	for (i, topo) in enumerate(["mesh","cmesh"]):
		data = {}
		for x in sizes:
			for rep in range(reps):
				path = "results/%s_%dx%d_%d.json" % (topo,x,x,rep)	
				if os.path.exists(path):
					results = hlp.read_file(path)
					for key in results["runtime"]:
						if key not in data:
							data[key] = {}
						if x not in data[key]:
							data[key][x] = []
						data[key][x].append(results["runtime"][key])
		for (j, key) in enumerate(data):
			xvals = list(data[key].keys())
			yvals = [sum(x) / len(x) for x in data[key].values()]
			ylow = [min(x) for x in data[key].values()]
			yhigh = [max(x) for x in data[key].values()]
			ax[i].plot(xvals, yvals, label = key, markersize = 3, marker = markers[j], color = colors[j], linewidth = 1, markerfacecolor = "none")
			ax[i].fill_between(xvals, ylow, yhigh, color = colors[j], alpha = 0.5)
		# Plot
		sizes_ = sizes if topo == "mesh" else [x for x in sizes if x%2==0]
		ax[i].set_title("2D Mesh" if topo == "mesh" else "Concentrated 2D Mesh")
		ax[i].grid(which = "major", linewidth = 1.0, axis = "y", color = "#666666")
		ax[i].grid(which = "minor", linewidth = 0.25, axis = "y", color = "#666666")
		ax[i].set_xticks(sizes_)
		ax[i].set_xticklabels(["%dx%d" % (x,x) for x in sizes_], rotation = 90)
		ax[i].set_xlabel("Scale")
		ax[i].set_ylabel("Runtime [s]")
		ax[i].set_yscale("log")
		ax[i].set_yticks([10**x for x in range(-6,1)])
		ax[i].set_xlim(1.5,max_size + 0.5)
		ax[i].set_ylim(1e-6,1e0)
	plt.savefig("plots/runtime.pdf")

# Create the accuracy plot
def create_accuracy_plot(max_size):
	# One plot for latency, one for throughput
	for metric in ["latency","throughput"]:
		(fig, ax) = plt.subplots(1, 2, figsize = (6, 2.5))
		plt.subplots_adjust(left=0.093, right = 0.99, top = 0.9, bottom = 0.3, wspace = 0.3)
		sizes = list(range(2,max_size + 1))
		# One subplot per topology
		for (i, topo) in enumerate(["mesh","cmesh"]):
			# One data series per traffic class
			for (j, traffic) in enumerate(["C2C","C2M","C2I","M2I"]):
				# Read data
				metric_rc = {}
				metric_bs = {}
				for x in sizes:
					path_rc = "results/%s_%dx%d_%d.json" % (topo,x,x,0)	
					path_bs = "results/sim_%s_%dx%d_%s.json" % (topo,x,x,traffic)	
					# RapidChiplet
					if os.path.exists(path_rc):
						results_rc = hlp.read_file(path_rc)
						if metric == "latency":
							metric_rc[x] = results_rc["ici_latency"][traffic]["avg"]
						else:
							metric_rc[x] = 100 * results_rc["ici_throughput"][traffic]["fraction_of_theoretical_peak"]
					# BookSim
					if os.path.exists(path_bs):
						results_bs = hlp.read_file(path_bs)
						if metric == "latency":
							metric_bs[x] = results_bs["0.001"]["packet_latency"]["avg"]
						else:
							metric_bs[x] = 100 * max([float(key) for key in results_bs if float(key) <= 3 * results_bs["0.001"]["packet_latency"]["avg"]])
				# Plot data
				colors1 = ["#000066","#006600","#660000","#660066"]
				colors2 = ["#6666FF","#66FF66","#FF6666","#FF66FF"]
				# RapidChiplet
				xvals = list(metric_rc.keys())
				yvals = list(metric_rc.values())
				ax[i].plot(xvals, yvals, label = traffic + " (RC)", markersize = 3, marker = markers[j+4], color = colors1[j], linewidth = 1, markerfacecolor = "none", linestyle = "--")
				# BookSim 
				xvals = list(metric_bs.keys())
				yvals = list(metric_bs.values())
				ax[i].plot(xvals, yvals, label = traffic + " (BS)", markersize = 3, marker = markers[j+4], color = colors2[j], linewidth = 1, markerfacecolor = "none", linestyle = ":")
				# Compute and print average relative error
				rel_errors = []
				for x in sizes:
					if x in metric_rc and x in metric_bs:
						rel_errors.append(abs(metric_rc[x] - metric_bs[x]) / metric_bs[x])
				if len(rel_errors) > 0:
					avg_rel_error = sum(rel_errors) / len(rel_errors) * 100
					print("%s %s %s AVG relative error: %.2f%%" % (metric, topo, traffic, avg_rel_error))

			# Plot
			real_sizes = sizes if topo == "mesh" else [x for x in sizes if x%2==0]
			ax[i].set_title("2D Mesh" if topo == "mesh" else "Concentrated 2D Mesh")
			ax[i].grid(which = "major", linewidth = 1.0, axis = "y", color = "#666666")
			ax[i].grid(which = "minor", linewidth = 0.25, axis = "y", color = "#666666")
			ax[i].set_xticks(real_sizes)
			ax[i].set_xticklabels(["%dx%d" % (x,x) for x in real_sizes], rotation = 90)
			ax[i].set_xlabel("Scale")
			ax[i].set_ylabel("Latency [cycles]" if metric == "latency" else "Throughput [%]")
			if metric == "throughput":
				ax[i].set_ylim(bottom = 0)
			if metric == "latency" and i == 0:	
				ax[i].set_ylim(0,600)
			if metric == "latency" and i == 1:	
				ax[i].set_ylim(0,150)
			ax[i].set_xlim(1.5,max_size + 0.5)
		# Add legend and store plot
		# ax[0].legend(ncol = 1, bbox_to_anchor = (2.275,-0.1), loc = "lower left", frameon = False, columnspacing = 1.375, handletextpad = 0.2, handlelength = 1.5)
		plt.savefig("plots/accuracy_%s.pdf" % metric)

# Create the accuracy plot
def create_speedup_plot(max_size):
	# One plot for latency, one for throughput
	for metric in ["latency","throughput"]:
		(fig, ax) = plt.subplots(1, 2, figsize = (6, 2.5))
		plt.subplots_adjust(left=0.11, right = 0.99, top = 0.89, bottom = 0.3, wspace = 0.35)
		sizes = list(range(2,max_size + 1))
		# One subplot per topology
		for (i, topo) in enumerate(["mesh","cmesh"]):
			# One data series per traffic class
			time_rc = {}
			time_bs_1 = {}
			time_bs_2 = {}
			time_bs_3 = {}
			# Read data
			for x in sizes:
				path_rc = "results/%s_%dx%d_%d.json" % (topo,x,x,0)	
				# RapidChiplet
				if os.path.exists(path_rc):
					results_rc = hlp.read_file(path_rc)
					time_rc[x] = results_rc["runtime"]["total_runtime"]
				# BookSim
				for (j, traffic) in enumerate(["C2C","C2M","C2I","M2I"]):
					path_bs = "results/sim_%s_%dx%d_%s.json" % (topo,x,x,traffic)	
					if os.path.exists(path_bs):
						if x not in time_bs_1:
							time_bs_1[x] = 0
						if x not in time_bs_2:
							time_bs_2[x] = 0
						if x not in time_bs_3:
							time_bs_3[x] = 0
						results_bs = hlp.read_file(path_bs)
						if metric == "latency":
							time_bs_1[x] += results_bs["0.001"]["total_run_time"]
						else:
							time_bs_1[x] += sum([results_bs[load]["total_run_time"] for load in results_bs if round(float(load),1) == float(load)])
							time_bs_2[x] += sum([results_bs[load]["total_run_time"] for load in results_bs if round(float(load),2) == float(load)])
							time_bs_3[x] += sum([results_bs[load]["total_run_time"] for load in results_bs if round(float(load),3) == float(load)])
			# Plot data
			# RapidChiplet
			xvals = list(time_rc.keys())
			yvals = list(time_rc.values())
			ax[i].plot(xvals, yvals, label = traffic + " (RC)", markersize = 3, marker = "o", color = "#000000", linewidth = 1, markerfacecolor = "none", linestyle = "--")
			# BookSim 
			if len(time_bs_1) > 0:
				xvals = list(time_bs_1.keys())
				yvals = list(time_bs_1.values())
				ax[i].plot(xvals, yvals, label = traffic + " (BS)", markersize = 3, marker = "s", color = "#000099", linewidth = 1, markerfacecolor = "none", linestyle = ":")
			if len(time_bs_2) > 0:
				xvals = list(time_bs_2.keys())
				yvals = list(time_bs_2.values())
				ax[i].plot(xvals, yvals, label = traffic + " (BS)", markersize = 3, marker = "D", color = "#009900", linewidth = 1, markerfacecolor = "none", linestyle = ":")
			if len(time_bs_3) > 0:
				xvals = list(time_bs_3.keys())
				yvals = list(time_bs_3.values())
				ax[i].plot(xvals, yvals, label = traffic + " (BS)", markersize = 3, marker = "P", color = "#990000", linewidth = 1, markerfacecolor = "none", linestyle = ":")
			# Compute and print average relative error
			speedups_1 = []
			speedups_2 = []
			speedups_3 = []
			for x in sizes:
				if x in time_rc and x in time_bs_1:
					speedups_1.append(time_bs_1[x] / time_rc[x])
				if x in time_rc and x in time_bs_2:
					speedups_2.append(time_bs_2[x] / time_rc[x])
				if x in time_rc and x in time_bs_3:
					speedups_3.append(time_bs_3[x] / time_rc[x])
			if len(speedups_1) > 0:
				avg_speedup = sum(speedups_1) / len(speedups_1)
				print("%s %s AVG speedup 10%%: %.2fx" % (metric, topo, avg_speedup))
			if len(speedups_2) > 0:
				avg_speedup = sum(speedups_2) / len(speedups_2)
				print("%s %s AVG speedup 1%%: %.2fx" % (metric, topo, avg_speedup))
			if len(speedups_3) > 0:
				avg_speedup = sum(speedups_3) / len(speedups_3)
				print("%s %s AVG speedup 0.1%%: %.2fx" % (metric, topo, avg_speedup))

			# Plot
			real_sizes = sizes if topo == "mesh" else [x for x in sizes if x%2==0]
			ax[i].set_title("2D Mesh" if topo == "mesh" else "Concentrated 2D Mesh")
			ax[i].grid(which = "major", linewidth = 1.0, axis = "y", color = "#666666")
			ax[i].grid(which = "minor", linewidth = 0.25, axis = "y", color = "#666666")
			ax[i].set_xticks(real_sizes)
			ax[i].set_xticklabels(["%dx%d" % (x,x) for x in real_sizes], rotation = 90)
			ax[i].set_xlabel("Scale")
			ax[i].set_ylabel("Runtime [s]")
			ax[i].set_yscale("log")
			if metric == "latency":
				ax[i].set_ylim(1e-3,1e1)
			else:
				ax[i].set_yticks([10**x for x in range(-3,4,1)])
				ax[i].set_ylim(1e-3*0.7,1e3*1.3)
			ax[i].set_xlim(1.5,max_size + 0.5)
		plt.savefig("plots/speedup_%s.pdf" % metric)

def plot_case_study_results():
	c_shg = "#999999"
	c_2dt = "#DD6666"
	c_1dt = "#DD66DD"
	c_m = "#DDDD66"
	c_fb = "#6666DD"
	c_tp = "#33DD33"
	c_lat = "#33DDDD"
	# Read and pre-process data
	results = hlp.read_file("results/case_study_results.json")
	# Replace throughput with reverse throughput
	for x in results:
		x["throughput_rev"] = 1 / x["throughput"]
	results_tmp = []
	# Remove close-to-identical entries to avoid having 64k lines in the same plot which crashes my pdf viewer
	keys = ["area","power","cost","latency","throughput_rev"]
	max_values = {key : max([x[key] for x in results]) for key in keys}
	round_values = {key : -1 if max_values[key] >= 100 else (0 if max_values[key] >= 10 else 1) for key in keys}
	res_as_tuples = [tuple([round(x[key], round_values[key]) for key in keys]) for x in results]
	unique_design_points = []
	for i in range(len(results)):
		if res_as_tuples[i] not in unique_design_points or i == len(results) - 1:
			unique_design_points.append(res_as_tuples[i])
			results_tmp.append(results[i])
	print("Reducing %d to %d unique design points" % (len(results), len(results_tmp)))
	results = results_tmp
	# Find the 1D and 2D Torus Points
	_1d_torus_idx = []
	_2d_torus_idx = []
	n = max([max(max(x["SR"] + [0]), max(x["SC"] + [0])) for x in results])
	for (idx, d) in enumerate(results):
		if (d["SR"] == [n] and d["SC"] == []) or (d["SR"] == [] and d["SC"] == [n]):
			_1d_torus_idx.append(idx)
		if (d["SR"] == [n] and d["SC"] == [n]):
			_2d_torus_idx.append(idx)
	# Find highest throughput and lowest latency at 10% / 40% area overhead 
	min_area = min([x["area"] for x in results])
	tmp_tp, tmp_lat  = float("inf"), float("inf")
	tp_idx, lat_idx = None, None
	for (idx, d) in enumerate(results):
		if d["area"] <= (min_area * 1.1) and d["throughput_rev"] < tmp_tp: # Reverse TP
			tmp_tp = d["throughput_rev"]
			tp_idx = idx
		if d["area"] <= (min_area * 1.4) and d["latency"] < tmp_lat:
			tmp_lat = d["latency"]
			lat_idx = idx
	print("Max. TP @110%% Area: SR = %s, SC = %s" % (str(results[tp_idx]["SR"]), str(results[tp_idx]["SC"])))
	print("Min. Lat @140%% Area: SR = %s, SC = %s" % (str(results[lat_idx]["SR"]), str(results[lat_idx]["SC"])))
	# Prepare radar plot
	data = [{key : res[key] for key in keys} for res in results]
	maxs = {key : max([x[key] for x in data]) for key in keys}	
	data = [{key : x[key] / maxs[key] for key in keys} for x in data]
	labels = ["   Area", "Power", "Cost  ", "Latency      ", "Throughput"]
	num_vars = len(labels)
	angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
	data = [list(d.values()) for d in data]
	data = [d + d[:1] for d in data]
	angles += angles[:1]
	fig, ax = plt.subplots(figsize=(10, 4), subplot_kw=dict(polar=True))
	fig.subplots_adjust(left=0.005, right = 0.5, top = 0.95, bottom = 0.05)
	plt.xticks(angles[:-1], labels, fontsize = 16)
	ax.set_rlabel_position(0)
	ax.set_yticks([x/10 for x in range(11)])
	ax.set_yticklabels(["" for x in range(11)])
	label_flags = [True for i in range(5)]
	for (idx, d) in enumerate(data):
		if idx == 0:
			ax.plot(angles, d, color = c_m, linewidth = 3, linestyle = "solid", label = "2D Mesh" if label_flags[0] else "", zorder = 3)
			label_flags[0] = False
		elif idx in _1d_torus_idx:
			ax.plot(angles, d, color = c_1dt, linewidth = 3, linestyle = "--", label = "Semi-Torus" if label_flags[1] else "", zorder = 3)
			label_flags[1] = False
		elif idx in _2d_torus_idx:
			ax.plot(angles, d, color = c_2dt, linewidth = 3, linestyle = "-.", label = "2D Torus" if label_flags[2] else "", zorder = 3)
			label_flags[2] = False
		elif idx == len(data) - 1:
			ax.plot(angles, d, color = c_fb, linewidth = 3, linestyle = ":", label = "Flattened Butterfly" if label_flags[3] else "", zorder = 3)
			label_flags[3] = False
		else:
			col, zord, lwd = (c_tp, 3, 2) if idx == tp_idx else (c_lat, 3, 2) if idx == lat_idx else (c_shg, 0, 1)
			lab = "Max. TP @110% Area" if idx == tp_idx else "Min. Lat @140% Area" if idx == lat_idx else ("Sparse Hamming Graph" if label_flags[4] else "")
			ax.plot(angles, d, color = col, linewidth = lwd, linestyle = "solid", label = lab, zorder = zord)
			label_flags[4] = False
	# Reorder labels in legend
	handles, labels = plt.gca().get_legend_handles_labels()
	order = [1,0,2,5,6,3,4]
	handles = [handles[idx] for idx in order]
	labels = [labels[idx] for idx in order]
	# Add legend and store plot
	ax.legend(handles, labels, loc = "upper right", bbox_to_anchor = (2.2, 1.05), frameon = False, fontsize = 16)
	plt.savefig("plots/case_study_results.pdf")
	# Prepare Scatter Plot
	base_area = results[0]["area"]
	area_overheads = [x["area"] / base_area for x in results]
	latencies = [x["latency"] for x in results]
	throughputs = [x["throughput"] for x in results]
	# Identify points that are latency-pareto-optimal
	lowest_lat_idx = {}
	for (idx, d) in enumerate(results):
		if area_overheads[idx] not in lowest_lat_idx or latencies[idx] < latencies[lowest_lat_idx[area_overheads[idx]]]:
			lowest_lat_idx[area_overheads[idx]] = idx
	# Identify points that are throughput-pareto-optimal
	highest_thp_idx = {}
	for (idx, d) in enumerate(results):
		if area_overheads[idx] not in highest_thp_idx or throughputs[idx] > throughputs[highest_thp_idx[area_overheads[idx]]]:
			highest_thp_idx[area_overheads[idx]] = idx
	# Create Scatter Plot
	fig, ax = plt.subplots(1, 2, figsize=(6, 3))
	fig.subplots_adjust(left=0.12, right = 0.995, top = 0.91, bottom = 0.15, wspace = 0.35)
	# Create Scatter Plot for Latency
	ax[0].scatter(area_overheads, latencies, color = c_shg, label = "SHG", s = 5, zorder = 3, marker = "o")
	ax[0].scatter(area_overheads[-1], latencies[-1], color = c_fb, label = "FB", zorder = 3, marker = "v")
	ax[0].scatter(area_overheads[0], latencies[0], color = c_m, label = "2D Mesh", zorder = 3, marker = "o")
	ax[0].scatter([area_overheads[i] for i in _1d_torus_idx], [latencies[i] for i in _1d_torus_idx], color = c_1dt, label = "Semi-Torus", s = 15, marker = "s", zorder = 3)
	ax[0].scatter([area_overheads[i] for i in _2d_torus_idx], [latencies[i] for i in _2d_torus_idx], color = c_2dt, label = "2D Torus", s = 15, marker = "D", zorder = 3)
	ax[0].set_ylabel("Latency [cycles]")
	# Create Scatter Plot for Throughput
	ax[1].scatter(area_overheads, throughputs, color = c_shg, label = "SHG", s = 5, zorder = 3, marker = "o")
	ax[1].scatter(area_overheads[-1], throughputs[-1], color = c_fb, label = "FB", zorder = 3, marker = "v")
	ax[1].scatter(area_overheads[0], throughputs[0], color = c_m, label = "2D Mesh", zorder = 3, marker = "o")
	ax[1].scatter([area_overheads[i] for i in _1d_torus_idx], [throughputs[i] for i in _1d_torus_idx], color = c_1dt, label = "Semi-Torus", s = 15, marker = "s", zorder = 3)
	ax[1].scatter([area_overheads[i] for i in _2d_torus_idx], [throughputs[i] for i in _2d_torus_idx], color = c_2dt, label = "2D Torus", s = 15, marker = "D", zorder = 3)
	ax[1].set_ylabel("Throughput [bits/cycle/core]")
	# Highlight Pareto-Optimal Points (Latency)
	xvals = [area_overheads[i] for i in lowest_lat_idx.values()]
	ax[0].plot(xvals, [latencies[i] for i in lowest_lat_idx.values()], color = c_lat, markersize = 6, marker = "x", zorder = 3, label = "Latency Opt", linestyle = "none", mew = 0.75)
	ax[1].plot(xvals, [throughputs[i] for i in lowest_lat_idx.values()], color = c_lat, markersize = 6, marker = "x", zorder = 3, label = "Latency Opt", linestyle = "none", mew = 0.75)
	# Highlight Pareto-Optimal Points (Throughput)
	xvals = [area_overheads[i] for i in highest_thp_idx.values()]
	ax[0].plot(xvals, [latencies[i] for i in highest_thp_idx.values()], color = c_tp, markersize = 6, marker = "+", zorder = 3, label = "Throughput Opt", linestyle = "none", mew = 0.75)
	ax[1].plot(xvals, [throughputs[i] for i in highest_thp_idx.values()], color = c_tp, markersize = 6, marker = "+", zorder = 3, label = "Throughput Opt", linestyle = "none", mew = 0.75)
	# Add Legend and Grid, configure axes
	ax[0].legend(ncol = 7, bbox_to_anchor = (-0.37,0.99), loc = "lower left", frameon = False, columnspacing = 0.5, handletextpad = 0.1, handlelength = 1.0)
	for i in range(2):
		ax[i].set_xlabel("Area Overhead [%]")
		ax[i].grid(zorder = 0)
		ax[i].set_xticks([1 + x / 10 for x in range(8)])
		ax[i].set_xticklabels(["%d" % (10 * x) for x in range(8)])	
	ax[0].set_ylim(50,225)
	ax[1].set_ylim(0,60)
	plt.savefig("plots/case_study_results_scatter.pdf")



def reproduce_plots_from_paper(reps, max_size):
	create_runtime_plot(max_size, reps)
	create_accuracy_plot(max_size)
	create_speedup_plot(max_size)
	plot_case_study_results()

if __name__ == "__main__":
	reproduce_plots_from_paper(10, 16)

