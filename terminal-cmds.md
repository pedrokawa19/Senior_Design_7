# Terminal Command Reference

A practical command reference for the Vision Metals Senior Design project. These examples assume macOS with `zsh` and a terminal opened in the project folder.

## Collaboration Workflow

### 1. Create a Branch

```bash
git checkout main # go into main
git fetch origin && git pull origin main # sync comp.
git checkout -b <branch-name> # create and switch into branch
```

### 2. Make and Commit Changes

1. Edit your files.
2. Stage the file you changed:

  ```bash
  git add <file-name>
  ```

3. Commit your changes:

  ```bash
  git commit -m "Your commit message"
  ```

4. Push your branch to GitHub:

  ```bash
  git push origin <branch-name>
  ```

### 3. Open a Pull Request

1. Go to the [github.com](https://github.com/pedrokawa19/Senior_Design_7/pulls) repo.
2. Open a pull request for your branch. 
 - `Compare * pull request`
 - `Creat pull request`
3. Assign someone to review it, if desired. 
4. When the pull request is ready, click `Ready to merge`
5. Merge the pull request and delete the branch.
 - `Merge pull request`
 - `Confirm merge`

Alternatively, in your terminal, you can run:

```bash
git checkout main
git merge <branch>
git push -u origin main
```
However, Github does the checking for you and provides a nicer UI to handle these things.

### 4. Update Your Local Main Branch

After the pull request has been merged, run:

```bash
git checkout main
git pull
```

Long Command
```bash
git add . && git commit -m "message" && git push origin branch && git checkout main && git merge branch && git push -u origin main && git checkout main && git pull && git branch -D branch
```

### Delete Branches
Run this if all the branches are deleted on Github too.
Github stores the branches in the repo and locally differently to allow one to recover lost information.
```bash
git fetch origin --prune # Be cautious of using this
```

## 1. GitHub Dictionary
### First-time setup

```bash
git init # Create a Git repository in the current directory.
git remote add origin https://github.com/USERNAME/REPOSITORY.git # Connect the local repo to GitHub.
git branch -M main # Rename the current branch to main.
```

Check whether a remote already exists before adding one:

```bash
git remote -v # Check whether a remote is already configured.
```

### Download a repository for the first time

```bash
git clone https://github.com/USERNAME/REPOSITORY.git # Download the repository from GitHub.
cd REPOSITORY # Enter the downloaded repository folder.
```

### Check status and changes
```bash
pwd # Show file path
git branch # Show active branch but as a little 'graph'
git branch -a # List local and remote branches.
git branch --show-current # Show the active branch.

git status # Show changed, staged, and untracked files.
git status -s # Show changes fast. Short.

git diff # Show unstaged line-by-line changes.
git diff --stat # Summarize unstaged changes by file.
git diff --staged # Show changes already staged for commit.

git ls-files --others --exclude-standard # List untracked files that are not ignored.
```

### Add files to a commit

```bash
git add path/to/file.md # Stage one specific file.
git add folder/ # Stage all changes inside the notes folder.
git add . # Stage all non-ignored changes below the current directory.
```

Review what will be committed:

```bash
git diff --staged # Review staged changes before committing.
git add --dry-run . # Review what would be added
```

### Commit and upload changes

```bash
git commit -m "feat: new feature" # Save the staged changes in a local commit.
git push origin main # Upload the main branch commits to GitHub.
```

### For a new branch:

```bash
git switch -c branch-name # Create and switch to a new feature branch.
git switch branch-name # switch to new branch
git add . # Stage the feature changes.
git commit -m "Describe the feature" # Save the feature changes in a local commit.
git push -u origin branch-name # Upload the new branch and set its upstream.
git branch -d branch-name # to delete a branch
git checkout main
git pull origin main
git merge branch-name
```

### Commit Format

Use a short, imperative subject line that explains the change:

```text
<type>: <short description>
```

Common types include:

- `feat`: Add user-facing functionality.
- `fix`: Correct a bug or unexpected behavior.
- `docs`: Update documentation or instructions.
- `refactor`: Restructure code without changing behavior.
- `test`: Add or update tests.
- `chore`: Update tooling, dependencies, or configuration.

Examples:

```text
feat: add profitability dashboard
fix: handle missing market dates
docs: clarify setup commands
```
### Download changes from GitHub

Fetch and pull info

```bash
git fetch origin # Download remote branch and commit information without merging.

git pull origin main # Download and merge the latest main branch changes.
```

### Review project history

```bash
git log --oneline
git log --oneline --decorate --graph -10 # Show the latest ten commits as a compact graph.
git show COMMIT_ID # Display the details of one commit.
git blame path/to/file.md # Show which commit last changed each line.
```

### Handle a merge conflict

1. Check which files have conflicts:

```bash
git status # Identify files with merge conflicts.
```

2. Open each conflicted file and resolve the sections between `<<<<<<<`, `=======`, and `>>>>>>>`.
3. Mark each resolved file:

```bash
git add path/to/resolved-file # Mark a manually resolved file as resolved.
```

4. Finish the merge:

```bash
git commit # Complete the merge with a commit.
```

### Stop before committing

Remove one file from staging while keeping its edits:

```bash
git restore --staged path/to/file # Remove one file from staging without deleting its edits.
```

Discard unstaged edits to one file only. Use carefully:

```bash
git restore path/to/file # Discard unstaged edits in one file.
```

Do not use destructive commands such as `git reset --hard` unless you intentionally want to discard all uncommitted work.


## 2. File and Directory Manipulation

### Navigate

```bash
pwd # Print the current directory.
ls # List visible files and folders.
ls -la # List all files, including hidden files, with details.
cd path/to/folder # Move into a specified folder.
cd .. # Move up one directory.
cd - # Return to the previous directory.
```

Useful project navigation:

```bash
cd "/Users/pedro/Desktop/GT 22-27 /ISyE/ISYE4106/Project" # Move to the project root.
find . -maxdepth 2 -type d | sort # List directories up to two levels deep.
find . -maxdepth 3 -type f | sort # List files up to three levels deep.
```

### Create files and directories

Create a directory:

```bash
mkdir new-folder # Create one directory.
mkdir -p parent-folder/child-folder # Create nested directories as needed.
```

Create an empty file:

```bash
touch notes/new-note.md # Create an empty Markdown file.
open notes/new-note.md # Open new file
code notes/new-note.md # Open or create the file in VS Code.
```

### Copy files and directories

```bash
cp source.md destination.md # Copy a file to a new filename.
cp source.md notes/source.md # Copy a file into another directory.
cp -R source-folder destination-folder # Copy a directory and its contents.
```

### Move and rename

```bash
mv old-name.md new-name.md # Rename a file.
mv file.md notes/file.md # Move a file into another directory.
mv old-folder/old-name.md notes/new-name.md # Move and rename a file at once.
git mv old-name.md new-name.md # Rename a tracked file and stage the rename.
```

### Delete

```bash
rm path/to/file.md # Delete one file permanently.
rmdir empty-folder # Delete an empty directory.
rm -r folder-name # Delete a directory and everything inside it.
```


### Inspect files

```bash
wc -l path/to/file.md # Count the file's lines.
file path/to/file.md # Identify the file type.
head -n 20 path/to/file.md # Show the first twenty lines.
tail -n 20 path/to/file.md # Show the last twenty lines.
```

### Check disk usage

```bash
du -sh ./* # Show the size of each top-level item.
du -sh .git # Show the size of the Git history folder.
```

Use `sed` with numeric values when previewing a range:

```bash
sed -n '1,80p' path/to/file.md # Print lines 1 through 80.
```

Search filenames and contents:

```bash
find . -iname '*keyword*' # Find filenames containing the keyword.
rg -n "keyword" . # Search all files for the keyword with line numbers.
rg -n "keyword" --glob '*.md' # Search only Markdown files.
```

### Rename many files carefully

Preview matching files before changing them:

```bash
find planning -type f -name '*.MD' -print # Preview uppercase-extension files before renaming.
```

Use a loop only after confirming the match set:

```bash
for file in planning/**/*.MD; do # Loop through matching uppercase-extension files.
  mv "$file" "${file%.MD}.md" # Rename the current file with a lowercase extension.
done # Finish the rename loop.
```

### Zsh settings

```bash
# Go to settings
code ~/.zshrc

# Save settings
source ~/.zshrc

# Show all colors
for code in {000..255}; do print -P -n -- "%F{$code}$code %f"; [ $((${code} % 16)) -eq 15 ] && echo; done 

# Set colors
PROMPT='%F{green}%1~ %# %F{blue}'

preexec() {
  print -rn -- $'\e[0m'
}


```