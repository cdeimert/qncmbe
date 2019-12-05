import matplotlib.pyplot as plt

from cycler import cycler

light = '#FFFFFF'
grey = '#AAAAAA'
dark = '#222222'

plt.rc('font', family='Arial')
plt.rc('lines', linewidth = 1.5)
plt.rc('axes', titlesize = 14)
plt.rc('axes', labelsize = 11)	
plt.rc('axes', facecolor = light)
plt.rc('axes', edgecolor = dark)
plt.rc('axes', labelcolor = dark)
plt.rc('axes', grid = True)
plt.rc('figure', facecolor = light)
plt.rc('grid', color = grey)
plt.rc('grid', linestyle = '--')
plt.rc('grid', linewidth = 0.5)
plt.rc('xtick', color = dark)
plt.rc('xtick', labelsize = 11)
plt.rc('ytick', color = dark)
plt.rc('ytick', labelsize = 11)
plt.rc('text', color = dark)
plt.rc('legend', facecolor="FFFFFF")
plt.rc('legend', fontsize = 11)

color_schemes = {
	'deep': ["#4C72B0", "#55A868", "#C44E52", "#8172B2", "#CCB974", "#64B5CD", "#36454f"],
	'muted': ["#4878CF", "#6ACC65", "#D65F5F", "#B47CC7", "#C4AD66", "#77BEDB"],
	'flatui': ["#9b59b6", "#3498db", "#95a5a6", "#e74c3c", "#34495e", "#2ecc71"],
	'set1': ['#E41A1C', '#377EB8', '#4DAF4A', '#984EA3', '#FF7F00', '#FFFF33', '#A65628', '#F781BF', '#36454f'],
	'set2': ['#66C2A5', '#FC8D62', '#8DA0CB', '#E78AC3', '#A6D854', '#FFD92F', '#E5C494', '#B3B3B3'],
	'dark2': ['#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e', '#e6ab02', '#a6761d', '#a6761d', '#666666'],
	'parula': ['#0072bd', '#d95319', '#edb120', '#7e2f8e', '#77ac30', '#4dbeee', '#a2142f', '#36454f'],
	'accent': ['#333333', '#BF5B17', '#F0027F', '#386CB0', '#FFFF99', '#FDC086', '#BEAED4', '#7FC97F'],
	'ggplot': ["#555555", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"]
}

def set_color_scheme(scheme_name):
	color_cycle = color_schemes[scheme_name]
	plt.rc('axes', prop_cycle = cycler('color', color_cycle))

color_cycle = color_schemes['set1']
set_color_scheme('set1')
