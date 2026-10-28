# Shared deployment workflows

## Deploy a selected branch or commit

Use `.github/workflows/deploy-ref-rsync.yml@v1.5.0` to deploy a branch, tag, or full commit SHA from the calling repository. It snapshots the live server to the `snapshot` branch before deploying, uses the same concurrency group as the standard single-directory deployment, and returns the resolved commit as the `deployed_sha` output and in the run summary. An invalid ref or missing source directory fails before accessing the server.

Add this manual workflow to the application repository's default branch, replacing the example server and directory settings:

```yaml
name: Deploy selected commit
run-name: Deploy ${{ inputs.deploy_ref }}

on:
  workflow_dispatch:
    inputs:
      deploy_ref:
        description: Branch, tag, or full commit SHA to deploy
        required: true
        type: string

permissions:
  contents: write

jobs:
  deploy:
    uses: hamidrg-deployments/deployment-workflows/.github/workflows/deploy-ref-rsync.yml@v1.5.0
    with:
      deploy_ref: ${{ inputs.deploy_ref }}
      deploy_host: example.com
      deploy_port: "22"
      deploy_user: deploy
      deploy_path: /srv/application
      source_path: application
    secrets:
      ssh_private_key: ${{ secrets.SERVER_SSH_KEY }}
      ssh_known_hosts: ${{ secrets.SERVER_KNOWN_HOSTS }}
```

In **Actions → Deploy selected commit → Run workflow**, keep the workflow branch set to the default branch and enter the revision to deploy in `deploy_ref`. For a particular commit on any branch, supply its full SHA. For the current tip of a branch, supply its branch name, such as `feature/example`; use `refs/heads/feature/example` to disambiguate a branch from a tag with the same name.

The workflow resolves the requested revision once and uses that checkout throughout deployment. It does not execute application scripts. Like the standard deployment, rsync preserves destination-only files and excludes `.git/` and `.env`. Other configuration files already tracked in the selected revision are included in deployment; select a revision appropriate for the target server.

## Multiple deployment directories

Use `deploy-ref-multiple-rsync.yml@v1.5.0` with `deploy_ref` and the same `deployments_json` mappings as `deploy-multiple-rsync.yml`. All source directories are validated before connecting to the server; all live directories are snapshotted before deploying any of them. The selected commit is used for every mapping and returned as `deployed_sha`.

## Repositories without a configured target

The manual `Deploy selected commit` action in this repository and `kasb-center` requires the source subdirectory and SSH destination at run time. Configure `SERVER_SSH_KEY` and `SERVER_KNOWN_HOSTS` with access to that destination before running it. Repositories with existing deployment mappings retain those mappings in their own manual actions.

Sources must be subdirectories within the selected checkout. Git submodules are not deployed by these workflows; deploy their source repositories directly. In particular, the `kasb-center` integration repository's `backend`, `api`, and `cms` directories are submodules.
