# -u means unbuffered print statements
source ~/Envs/pain/bin/activate
python -u painmachine.py > log.txt 2>&1 &
open "static/loading.html"
tail -f log.txt

