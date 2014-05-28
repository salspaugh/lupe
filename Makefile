all: fig2 fig3

fig2:
	echo "Making Figure 2."

fig3:
	echo "Making Figure 3."

fig6:
	echo "Making Figure 6."
	python clustering/main.py -s postgresdb -U lupe -P lupe -D lupe -p 9 -f filters01 -l filters -n -d 10 -o clustering/results/fig6 -u clustering/results/fig6.visualization.d3.csv -t clustering/results/fig6.features

fig7:
	echo "Making Figure 7."
	python clustering/main.py -s postgresdb -U lupe -P lupe -D lupe -p 9 -f augments01 -l augments -n -d 2 -o clustering/results/fig7 -u clustering/results/fig7.visualization.d3.csv -t clustering/results/fig7.features

fig8:
	echo "Making Figure 8."
	python clustering/main.py -s postgresdb -U lupe -P lupe -D lupe -p 9 -f aggregates01 -l aggregates -n -d 100 -o clustering/results/fig8 -u clustering/results/fig8.visualization.d3.csv -t clustering/results/fig8.features
