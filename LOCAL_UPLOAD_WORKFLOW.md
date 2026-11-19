# Local GitHub Desktop upload workflow

## Use this exact folder

`G:\Codex所有文件\ChatGPT\心脏肿瘤学\PlanB_Repro_v1\PlanB_Code_Repository_Upload_Ready_20261118`

Expected size:

- 277 files
- approximately 78 MB

If GitHub Desktop reports 2552 files, the wrong folder was selected. Stop and do not publish.

## Step 1: remove a wrong local repository from GitHub Desktop

This only removes the repository from GitHub Desktop. It does not delete local files.

1. In GitHub Desktop, click the current repository name in the toolbar.
2. Choose **Remove** or use **File/Repository > Remove Repository**.
3. Do not delete the folder from disk.
4. Do not click Publish or Push for the wrong repository.

## Step 2: add the correct folder

1. Click **File > Add Local Repository**.
2. Select exactly:
   `G:\Codex所有文件\ChatGPT\心脏肿瘤学\PlanB_Repro_v1\PlanB_Code_Repository_Upload_Ready_20261118`
3. If GitHub Desktop says the folder is not a Git repository, choose **create a repository**.
4. Repository name:
   `planb-cardiac-transcriptomics`
5. Keep the local path as the prepared folder.
6. Click **Create Repository**.

The Changes tab should show about 277 files. If it shows thousands of files, the path is wrong.

## Step 3: commit locally

1. Open the **Changes** tab.
2. In Summary, enter:
   `Initial reproducibility package`
3. Click **Commit to main**.

Committing is local. It does not upload anything to GitHub.

## Step 4: publish to GitHub

1. Wait until the commit spinner finishes.
2. Click **Publish repository**.
3. Do not check **Keep this code private**. The repository must be Public.
4. Click **Publish repository** again to confirm.
5. Wait while GitHub Desktop shows **Pushing...**. There is no percentage progress bar.

## Step 5: get the public link

1. Open **Repository > View on GitHub**.
2. Confirm the repository page shows:
   - `README.md`
   - `scripts`
   - `outputs`
   - `figures`
   - `supplementary`
3. Copy the URL, for example:
   `https://github.com/YOUR_USERNAME/planb-cardiac-transcriptomics`

## Common mistakes

- Do not upload the ZIP file.
- Do not select `PlanB_Repro_v1` itself.
- Do not select the parent `心脏肿瘤学` folder.
- Do not click Publish until the repository shows about 277 files.
- Do not share a GitHub password or token.
