import argparse
from typing import List
from git.objects.commit import Commit
import yaml
import json
import fnmatch
from git import Repo, config

class CommitFile():
    def __init__(self, path: str) -> None:
        self.path = path
        self._commits = []
        self._authors = []
        self._large_commit = {}

    def to_dict(self):
        return {
            'path': self.path,
            'authors': self.authors(),
            'commit_count': self.commit_count(),
            'author_count': self.author_count(),
            'large_commit_count': len(self._large_commit),
            'large_commit': self._large_commit,
            #'commit': {c.hexsha: {'total': c.stats.total} for c in self._commits},
            'risk': self.risk(),
        }

    def add_commit(self, commit: Commit):
        self._commits.append(commit)
        self._authors.append(commit.author.name)

    def add_large_commit(self, commit: Commit):
        self._large_commit[commit.hexsha] = commit.stats.total['lines']

    def authors(self) -> List:
        return list(set(self._authors))

    def commit_count(self) -> int:
        return len(self._commits)

    def author_count(self) -> int:
        return len(self.authors())

    def risk(self) -> float:
        return self.commit_count() * self.author_count()

class CommitFileJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, CommitFile):
            return o.to_dict()
        return super().default(o)

def parse_repo(path, branch, depth, exclude, large_commit_lines):
    repo = Repo(path)

    commits = repo.iter_commits(branch, max_count=depth)

    authors = dict()
    files = dict()
    total_commits = 0

    # exlude rename
    exclude.append('**{* => *}')

    for commit in commits:
        # マージコミットは無視する
        if len(commit.parents) > 1:
            continue

        total_commits += 1

        is_large_commit = commit.stats.total['lines'] > large_commit_lines

        author = commit.author.name

        if author in authors:
            authors[author] += 1
        else:
            authors[author] = 1

        for file in commit.stats.files:
            if any([fnmatch.fnmatch(file, e) for e in exclude]):
                continue

            if file not in files:
                files[file] = CommitFile(file)

            files[file].add_commit(commit)

            if is_large_commit:
                files[file].add_large_commit(commit)

    return total_commits, files, authors

def load_config(path):
    with open(path, 'r') as yml:
        config = yaml.safe_load(yml)
    return config

def argument():
    parser = argparse.ArgumentParser(description='Find bugspot in git repo.')
    parser.add_argument('path', default='./', type=str, help='repository path')
    parser.add_argument('--branch', default='master', dest='branch', type=str)
    parser.add_argument('--depth', default=None, dest='depth', type=int)
    parser.add_argument('--exclude', nargs='+', default=[], dest='exclude', action='append', type=str)
    parser.add_argument('--top', default=-1, dest='top', type=int)
    parser.add_argument('--member', nargs='+', dest='member', default=[], action='append', type=str)
    parser.add_argument('--config', dest='config', default='', type=str)
    parser.add_argument('--show-summary', dest='show_summary', default=True, type=bool)

    return parser.parse_args()

def print_summary(result):
    print("summary")
    print(f" total commits={result['total_commits']}")
    print(f" total files={result['total_files']}")
    print(f" authors={result['authors']}")
    print('')

def main():
    args = argument()
    path = args.path
    branch = args.branch
    depth = args.depth
    top = args.top
    exclude = sum(args.exclude, [])
    member = sum(args.member, [])

    if args.config:
        config = load_config(args.config)
        branch = config['parse']['branch']
        depth = config['parse']['depth']
        large_commit_lines = config['parse']['large_commit_lines']
        top = config['output']['top']
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

    print("config")
    print(f" path={path}")
    print(f" branch={branch}")
    print(f" depth={depth}")
    print(f" top={top}")
    print(f" exclude={exclude}")
    print(f" member={member}")
    print('')

    total_commits, files, authors = parse_repo(path, branch, depth, exclude, large_commit_lines)

    result = {
        'total_commits': total_commits,
        'total_files': len(files),
        'authors': list(authors.keys()),
        'files': files,
    }

    # print_summary(result)
    # print_order_by_number_of_authors(files, top)
    # print_order_by_change_count(files, top)
    # print_no_employee(files, employee)
    # for r in ranking:
    #     print(r)

    # o = only_one_author(files)
    # a = filter(lambda x: 'iwata-n' in x[1]['author'], o)
    # print(json.dumps(list(a), sort_keys=True, indent=2))

    #print(result)
    print(json.dumps({'parameter': parameter, 'result': result}, sort_keys=True, indent=2, cls=CommitFileJSONEncoder))

if __name__ == '__main__':
    main()


