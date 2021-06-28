import argparse
import fnmatch
from git import Repo

def load_repo(path, branch, max_count, exclude, employee):
    repo = Repo(path)

    commits = repo.iter_commits(branch, max_count=max_count)

    authors = dict()
    files = dict()
    total_commits = 0

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

        for file in commit.stats.files:
            if any([fnmatch.fnmatch(file, e) for e in exclude]):
                continue

            if file in files:
                files[file]['change_count'] += 1
                if author in files[file]:
                    files[file]['author'][author] += 1
                else:
                    files[file]['author'][author] = 1
            else:
                files[file] = {'author': {author: 1}, 'change_count':1}

    return total_commits, files, authors

def argument():
    parser = argparse.ArgumentParser(description='Find bugspot in git repo.')
    parser.add_argument('path', default='./', type=str, help='repository path')
    parser.add_argument('--branch', default='master', dest='branch', type=str)
    parser.add_argument('--max_commit', default=None, dest='max_commit', type=int)
    parser.add_argument('--exclude', nargs='+', default=[], dest='exclude', action='append', type=str)
    parser.add_argument('--top', default=-1, dest='top', type=int)
    parser.add_argument('--employee', nargs='+', dest='employee', default=[], action='append', type=str)

    return parser.parse_args()

def print_summary(total_commits, files, authors):
    print("summary")
    print(f" total commits={total_commits}")
    print(f" total files={len(files)}")
    print(f' authors={authors}')

def print_order_by_number_of_authors(files, top):
    print(f"Order by number of authors. top:{top}")
    change_authors = sorted(files.items(), key = lambda x: len(x[1]['author']), reverse=True)
    for k in change_authors[0:top]:
        a = k[1]['author']
        print(f" {k[0]} author_count={len(a)} {a}")

def print_order_by_change_count(files, top):
    print(f"Order by change count top{top}")
    change_count = sorted(files.items(), key = lambda x: x[1]['change_count'], reverse=True)
    for k in change_count[0:top]:
        print(f" {k[0]} count={k[1]['change_count']}")

def main():
    args = argument()

    print(args)

    exclude = sum(args.exclude, [])
    employee = sum(args.employee, [])

    total_commits, files, authors = load_repo(args.path, args.branch, args.max_commit, exclude, employee)

    print_summary(total_commits, files, authors)
    print_order_by_number_of_authors(files, args.top)
    print_order_by_change_count(files, args.top)

if __name__ == '__main__':
    main()


