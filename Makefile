
tab2:
	echo "TODO: Outputting data for table 2."

tab3:
	echo "TODO: Outputting data for table 3."

tab4:
	python subsequences/lcs.py -s postgresdb -P lupe -D lupe -U lupe -o results/tab4.csv -q scheduled

toppaths:
	echo "Outputting data for top paths in text on page 9."
	python statemachines/main.py -s postgresdb -U lupe -P lupe -D lupe -o results/fig3 -t path -q scheduled

fig2:
	python transformations/barchart.py -s postgresdb -U lupe -P lupe -D lupe -o results/fig2 -q scheduled

fig3:
	# TODO: doesn't match paper figure
	python statemachines/main.py -s postgresdb -U lupe -P lupe -D lupe -o results/fig3 -t user -q scheduled

fig4:
	python statemachines/main.py -s postgresdb -U lupe -P lupe -D lupe -o results/fig4 -t solaris3-web-access -r 0.0 -q scheduled

fig5:
	python statemachines/main.py -s postgresdb -U lupe -P lupe -D lupe -o results/fig5 -t vmware:perf: -r 0.0 -q scheduled

fig6:
	python clustering/main.py -s postgresdb -U lupe -P lupe -D lupe -p 9 -f filters01 -l filters -n -d 10 -o results/fig6.clusters -u results/fig6.mouseovers -t results/fig6.features -q scheduled

fig7:
	python clustering/main.py -s postgresdb -U lupe -P lupe -D lupe -p 9 -f augments01 -l augments -n -d 2 -o results/fig7.clusters -u results/fig7.mouseovers -t results/fig7.features -q scheduled

fig8:
	python clustering/main.py -s postgresdb -U lupe -P lupe -D lupe -p 9 -f aggregates01 -l aggregates -n -d 100 -o results/fig8.clusters -u results/fig8.mouseovers -t results/fig8.features -q scheduled
