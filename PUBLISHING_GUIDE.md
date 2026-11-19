# How to publish this repository

Use the unzipped folder `PlanB_Code_Repository_Upload_Ready_20261118`, not the ZIP itself.

## Option A: GitHub Desktop, recommended for a non-technical first upload

1. Create a GitHub account and sign in.
2. Install GitHub Desktop from the official GitHub site.
3. In GitHub Desktop choose **File > Add local repository** and select the folder `PlanB_Code_Repository_Upload_Ready_20261118`.
4. If GitHub Desktop says the folder is not a Git repository, choose **create a repository** in that folder.
5. Enter a repository name such as `planb-cardiac-transcriptomics` and a description: `Reproducibility package for cross-dataset cardiac single-cell and spatial transcriptomic analyses`.
6. Commit the files with the message `Initial reproducibility package`.
7. Click **Publish repository** and leave **Keep this code private** unchecked. The repository must be public for the manuscript link.
8. Copy the public URL from the repository page, for example:
   `https://github.com/<account>/planb-cardiac-transcriptomics`
9. Add a release tag such as `v1.0-submission` before the final submission if the journal asks for a versioned link.

## Option B: command line

```powershell
cd "G:\Codex所有文件\ChatGPT\心脏肿瘤学\PlanB_Repro_v1\PlanB_Code_Repository_Upload_Ready_20261118"
git init
git add .
git commit -m "Initial reproducibility package"
git branch -M main
git remote add origin https://github.com/<account>/<repository>.git
git push -u origin main
```

Create the empty repository on GitHub or GitLab first. Do not commit raw GEO data into the repository; the prepared package links to the GEO accessions instead.

## GitLab

The same workflow applies. Create an empty public GitLab project, then set:

`git remote add origin https://gitlab.com/<account>/<repository>.git`

Commit and push as above.

## DOI after acceptance

For a citable DOI, use the repository release rather than an arbitrary commit:

1. Create a tagged release, for example `v1.0.0`, after acceptance.
2. Connect the GitHub repository to Zenodo.
3. Archive the tagged release in Zenodo.
4. Paste the Zenodo DOI into the manuscript during proof/camera-ready stage.

A GitHub/GitLab URL is sufficient for initial submission; the DOI can be added after acceptance if the journal permits.

## Before making the repository public

- Confirm that all authors agree to publish the code and derived result tables.
- Choose a licence. No licence has been selected in this staging package.
- Do not add patient-identifiable data, credentials, API keys, `.env` files or raw controlled-access data.
- Confirm that the GEO accessions and data-availability wording match the manuscript.
