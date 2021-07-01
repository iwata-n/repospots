# repospots
parse git repository.

## python
```
pip3 install -r requirements.txt
python3 repospots.py --config=config.yml <REPOSITORY_PATH>
python3 analyze.py --member=MEMBER1 --member=MEMBER2 <RESULT.JSON>
```

## Docker
```
./bin/build_docker
./bin/run_docker <REPOSITORY_PATH>
```