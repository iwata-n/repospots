import argparse
from typing import Dict, List
from git.objects.commit import Commit
from git.refs.head import HEAD
import yaml
import json
import fnmatch
import re
from git import Repo

class CommitFile():
    def __init__(self, path: str) -> None:
        self.path = path
        self._commits = []
        self._authors = []
        self._diff = {}

    def to_dict(self):
        return {
            'path': self.path,
            'authors': self.authors(),
            'commit_count': self.commit_count(),
            'author_count': self.author_count(),
            'diff': self._diff,
        }

    def add_commit(self, commit: Commit, diff: Dict):
        self._commits.append(commit)
        self._authors.append(commit.author.name)
        self._diff[commit.hexsha] = {
            'datetime': commit.authored_datetime.strftime("%Y/%m/%d %H:%M:%S"),
            'diff': diff
        }

    def authors(self) -> List:
        return list(set(self._authors))

    def commit_count(self) -> int:
        return len(self._commits)

    def author_count(self) -> int:
        return len(self.authors())

class CommitFileJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, CommitFile):
            return o.to_dict()
        if isinstance(o, HEAD):
            return o.commit.hexsha
        return super().default(o)

def parse(path, branch, depth, exclude):
    repo = Repo(path)

    commits = repo.iter_commits(branch, max_count=depth)

    authors = dict()
    files = dict()
    total_commits = 0

    # exlude rename
    rename_re = re.compile(".*\{.* => .*\}.*")

    for commit in commits:
        # マージコミットは無視する
        if len(commit.parents) > 1:
            continue

        total_commits += 1

        author = commit.author.name

        if author in authors:
            authors[author] += 1
        else:
            authors[author] = 1

        for file in commit.stats.files.items():
            file_path = file[0]
            file_diff = file[1]

            if any([fnmatch.fnmatch(file_path, e) for e in exclude]):
                continue

            if rename_re.match(file_path):
                continue

            if file_path not in files:
                files[file_path] = CommitFile(file_path)

            files[file_path].add_commit(commit, file_diff)

    return total_commits, files, authors, repo.head

def _load_config(path):
    with open(path, 'r') as yml:
        config = yaml.safe_load(yml)
    return config

def _argument():
    parser = argparse.ArgumentParser(description='Find bugspot in git repo.')
    parser.add_argument('path', default='./', type=str, help='repository path')
    parser.add_argument('--branch', default='master', dest='branch', type=str)
    parser.add_argument('--depth', default=None, dest='depth', type=int)
    parser.add_argument('--exclude', nargs='+', default=[], dest='exclude', action='append', type=str)
    parser.add_argument('--top', default=-1, dest='top', type=int)
    parser.add_argument('--member', nargs='+', dest='member', default=[], action='append', type=str)
    parser.add_argument('--config', dest='config', default='', type=str)
    parser.add_argument('--output', dest='output', default='', type=str)
    parser.add_argument('--show-summary', dest='show_summary', default=True, type=bool)

    return parser.parse_args()

def main():
    args = _argument()
    path = args.path
    branch = args.branch
    depth = args.depth
    top = args.top
    is_debug = False
    output_file = args.output
    output_console = True
    exclude = sum(args.exclude, [])
    member = sum(args.member, [])

    if args.config:
        config = _load_config(args.config)
        branch = config['parse']['branch']
        depth = config['parse']['depth']
        large_commit_lines = config['parse']['large_commit_lines']
        top = config['output']['top']
        output_file = config['output']['file']
        output_console = config['output']['console']
        is_debug = config['debug']
        exclude = config['parse']['file']['exclude']
        member = config['parse']['member']

    parameter = {
        'path': path,
        'branch': branch,
        'depth': depth,
        'large_commit_lines': large_commit_lines,
        'top': top,
        'exclude': exclude,
        'member': member
    }

    if is_debug:
        print("config")
        print(f" path={path}")
        print(f" branch={branch}")
        print(f" depth={depth}")
        print(f" top={top}")
        print(f' output_file={output_file}')
        print(f" exclude={exclude}")
        print(f" member={member}")
        print('')

    total_commits, files, authors, head = parse(path, branch, depth, exclude)

    result = {
        'total_commits': total_commits,
        'total_files': len(files),
        'authors': list(authors.keys()),
        'head': head,
        'files': files,
    }

    json_result = json.dumps(
        {
            'parameter': parameter,
            'result': result
        },
        sort_keys=True,
        indent=2,
        cls=CommitFileJSONEncoder
    )

    if output_console:
        print(json_result)

    if output_file is not None:
        with open(output_file, 'w') as f:
            f.write(json_result)

if __name__ == '__main__':
    main()


