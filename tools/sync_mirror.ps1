<#
.SYNOPSIS
  Re-sync the publication mirror from the three local project repositories.

.DESCRIPTION
  Records are written ONLY in the local project folders; this mirror is never
  edited by hand. This script pulls each project's branch into its subfolder with
  `git subtree pull` (history preserved, no squash) and re-imports the projects'
  annotated tags unchanged. It never adds a remote and never pushes: publishing
  is the Owner's own act.

  Run from anywhere:
    powershell -ExecutionPolicy Bypass -File tools\sync_mirror.ps1
#>
$ErrorActionPreference = 'Stop'

$Mirror    = Split-Path -Parent $PSScriptRoot
$Workspace = Split-Path -Parent (Split-Path -Parent $Mirror)   # ...\Quant trade

$Sources = @(
    @{ Prefix = 'Intraday Trend Strategy Framework'; Path = 'Intraday Trend Strategy Framework'; Branch = 'master'; Tags = @('mc-freeze-v1', 's0-freeze-v1') },
    @{ Prefix = 'nq-event-diffusion-research';       Path = 'nq-event-diffusion-research';       Branch = 'main';   Tags = @('r1-pre-seal', 'r1-s1-sealed', 'r1-s2-built', 'r1-final') },
    @{ Prefix = 'nq-letf-rebalancing-research';      Path = 'nq-letf-rebalancing-research';      Branch = 'main';   Tags = @() }
)

Push-Location $Mirror
try {
    if (git status --porcelain) { throw "mirror working tree is not clean; refusing to sync" }
    foreach ($s in $Sources) {
        $src = Join-Path $Workspace $s.Path
        if (git -C $src status --porcelain) {
            Write-Output "NOTE: $($s.Path) has uncommitted changes; only its committed $($s.Branch) is pulled."
        }
        Write-Output "== $($s.Prefix) <- $src ($($s.Branch))"
        git subtree pull --prefix="$($s.Prefix)" "$src" $s.Branch -m "Mirror: sync $($s.Prefix) from $($s.Branch)"
        if ($LASTEXITCODE -ne 0) { throw "subtree pull failed for $($s.Prefix)" }
        foreach ($t in $s.Tags) {
            git fetch "$src" "refs/tags/${t}:refs/tags/${t}"
            if ($LASTEXITCODE -ne 0) { throw "tag fetch failed for $t" }
        }
        Write-Output ("   source HEAD {0}" -f (git -C $src rev-parse $s.Branch))
    }
    Write-Output "Done. Review, run the projects' checks (README.md), then the Owner pushes."
} finally {
    Pop-Location
}
