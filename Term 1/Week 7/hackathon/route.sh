#!/bin/bash
# called by tar --to-command once per member
O=/tmp/claude-0/-home-claude/b7b01b37-c874-5069-acdc-043d423a73e5/scratchpad/inat/out
case "$TAR_FILENAME" in
  *observations.csv) mawk -F'\t' 'NR==1{for(i=1;i<=NF;i++)c[$i]=i; print; next}
       $c["quality_grade"]=="research" && $c["latitude"]>=50.75 && $c["latitude"]<=53.56 && $c["longitude"]>=3.36 && $c["longitude"]<=7.23' > $O/nl_obs.tsv ;;
  *photos.csv) mawk -F'\t' -v obs=$O/nl_obs.tsv 'BEGIN{while((getline l < obs)>0){split(l,f,"\t"); k[f[1]]=1}}
       NR==1{print; next} ($3 in k)' > $O/nl_photos.tsv ;;
  *observers.csv) cat > $O/observers.tsv ;;
  *taxa.csv) cat > $O/taxa.tsv ;;
  *) echo "member $TAR_FILENAME" >&2; cat > /dev/null ;;
esac
echo "done $TAR_FILENAME $(date)" >&2
