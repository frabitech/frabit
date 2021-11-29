#!/usr/bin/env bash
# (c) 2020 Frabit Project maintained and limited by Blylei < blylei.info@gmail.com >
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# You should have received a copy of the GNU General Public License
# along with Barman.  If not, see <http://www.gnu.org/licenses/>.

set -eu

BASE="$(dirname $(cd $(dirname "$0"); pwd))"
cd "$BASE"

release_version=$1
if [ -n "${2:-}" ]
then
    release_date=$(LANG=C date +"%B %-d, %Y" -d "$2")
else
    release_date="Month DD, YYYY"
fi

require_clean_work_tree () {
    git rev-parse --verify HEAD >/dev/null || exit 1
    git update-index -q --ignore-submodules --refresh
    err=0

    if ! git diff-files --quiet --ignore-submodules
    then
        echo >&2 "Cannot $1: You have unstaged changes."
        err=1
    fi

    if ! git diff-index --cached --quiet --ignore-submodules HEAD --
    then
        if [ $err = 0 ]
        then
            echo >&2 "Cannot $1: Your index contains uncommitted changes."
        else
            echo >&2 "Additionally, your index contains uncommitted changes."
        fi
        err=1
    fi

    if [ $err = 1 ]
    then
        # if there is a 2nd argument print it
        test -n "${2+1}" && echo >&2 "$2"
        exit 1
    fi
}

require_clean_work_tree "set version"

if branch=$(git symbolic-ref --short -q HEAD) && [ $branch = 'master' ]
then
    echo "Setting version ${release_version}"
else
    echo >&2 "Release is not possible because you are not on 'master' branch ($branch)"
    exit 1
fi


sed -i -e "3s/^%.*/% ${release_date} (${release_version})/" \
    doc/manual/00-head.en.md
sed -i -e "s/__version__ = .*/__version__ = '${release_version}'/" \
    barman/version.py

make -C doc

git add doc/manual/00-head.en.md \
    barman/version.py
git commit -sm "Version set to ${release_version}"

echo "Version set to ${release_version}"
