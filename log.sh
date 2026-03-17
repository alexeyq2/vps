source dc.inc.sh
$DC logs -n 1000 -f $*

# $DC logs -n 1000 -t $* | awk '{sub(/\.[0-9]+Z/, "", $3); print}'
