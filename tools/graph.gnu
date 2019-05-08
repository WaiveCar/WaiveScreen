set key outside
set style line 1 lw 14 ps 4
set style line 2 lw 14 ps 4
plot for [col=1:2] 'power-history' using 0:col with lines
pause 1
reread
