
tab2:
	echo "Outputting data for table 2."

tab3:
	echo "Outputting data for table 3."

tab4:
	echo "Outputting data for table 4."

toppaths:
	echo "Outputting data for top paths in text on page 9."

fig2:
	echo "Making Figure 2."

fig3:
	echo "Making Figure 3."

fig4:
	echo "Making Figure 4."

fig5:
	echo "Making Figure 5."

fig6:
	echo "Making Figure 6."
	python clustering/main.py -s postgresdb -U lupe -P lupe -D lupe -p 9 -f filters01 -l filters -n -d 10 -o results/fig6.clusters -u results/fig6.mouseovers -t results/fig6.features

fig7:
	echo "Making Figure 7."
	python clustering/main.py -s postgresdb -U lupe -P lupe -D lupe -p 9 -f augments01 -l augments -n -d 2 -o results/fig7.clusters -u results/fig7.mouseovers -t results/fig7.features

fig8:
	echo "Making Figure 8."
	python clustering/main.py -s postgresdb -U lupe -P lupe -D lupe -p 9 -f aggregates01 -l aggregates -n -d 100 -o results/fig8.clusters -u results/fig8.mouseovers -t results/fig8.features
