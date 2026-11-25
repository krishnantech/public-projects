<#
.SYNOPSIS
    on-demand-geo-exit-node: a Tailscale exit node in any Azure region, created when needed, deleted when done.
    https://github.com/<you>/on-demand-geo-exit-node

.DESCRIPTION
    up       Create a VM in -Region, install Tailscale as an exit node, wait until it is online,
             then (after you approve it) route this PC's traffic through it.
    down     Switch this PC back to its normal connection and delete the region's resources.
    status   Show what exists in Azure for -Region (or all regions with -All).
    list     List all exit-node resource groups this tool has created.
    regions  List Azure regions you can pass to -Region.
    render   Print the rendered cloud-init (debugging; uses a dummy key).

    Each VM deletes itself after -IdleMinutes of no traffic, or -MaxHours in total.

.EXAMPLE
    .\exitnode.ps1 up -Region centralindia -FallbackRegions southindia
    .\exitnode.ps1 down -Region centralindia
    .\exitnode.ps1 up -Region japaneast -IdleMinutes 20 -MaxHours 2
    .\exitnode.ps1 down -All
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0, Mandatory)]
    [ValidateSet('up', 'down', 'status', 'list', 'regions', 'render')]
    [string]$Action,

    [string]  $Region,                                   # e.g. centralindia, uksouth, japaneast
    [string[]]$FallbackRegions = @(),                    # tried in order if $Region has no capacity
    [switch]  $All,                                      # down/status: every exit-node group
    [string[]]$Sizes        = @('Standard_B2ats_v2', 'Standard_B1s', 'Standard_B2s'),
    [string]  $Image        = 'Ubuntu2404',
    [int]     $IdleMinutes  = 0,     # 0 = ask (default 30)
    [int]     $MaxHours     = 0,     # 0 = ask (default 4)
    [int]     $ActiveKB     = 64,    # traffic per 5 min that counts as "in use"
    [string]  $Prefix       = 'exitnode'
)

$ErrorActionPreference = 'Stop'
$ScriptDir    = Split-Path -Parent $MyInvocation.MyCommand.Path
$StateDir     = Join-Path $env:USERPROFILE '.exitnode'
$TemplateFile = Join-Path $ScriptDir 'cloud-init.yaml'
$AdminConsole = 'https://login.tailscale.com/admin/machines'

# ---------------------------------------------------------------- helpers

function Write-Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "!!  $msg" -ForegroundColor Yellow }

function Invoke-Az {
    $out = & az @args
    if ($LASTEXITCODE -ne 0) { throw "az $($args -join ' ') failed (exit $LASTEXITCODE)" }
    return $out
}

function Read-WithDefault([string]$prompt, [string]$default) {
    $v = Read-Host "$prompt [$default]"
    if ([string]::IsNullOrWhiteSpace($v)) { return $default } else { return $v.Trim() }
}

function Read-Secret([string]$prompt) {
    $s = Read-Host $prompt -AsSecureString
    $b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($b) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }
}

function Get-TailscaleCli {
    $c = Get-Command tailscale -ErrorAction SilentlyContinue
    if ($c) { return $c.Source }
    $p = Join-Path $env:ProgramFiles 'Tailscale\tailscale.exe'
    if (Test-Path $p) { return $p }
    return $null
}

function Connect-Azure {
    if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
        throw "Azure CLI not found. Install it: winget install -e --id Microsoft.AzureCLI"
    }
    & az account show -o none 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Step "Signing in to Azure (a browser window will open)..."
        Invoke-Az login -o none | Out-Null
    }
    Write-Step "Using Azure subscription: $(Invoke-Az account show --query name -o tsv)"
}

function Get-RgName([string]$region) { return "$Prefix-$region-rg" }
function Get-StateFile([string]$rg)  { return (Join-Path $StateDir "$rg.txt") }

function Get-ExitNodeGroups {
    $names = Invoke-Az group list --query "[?starts_with(name, '$Prefix-')].name" -o tsv
    return @($names | Where-Object { $_ })
}

function Require-Region {
    if (-not $Region) {
        $script:Region = (Read-Host 'Azure region (e.g. centralindia, uksouth, japaneast; run "regions" to list)').Trim().ToLower()
    }
    if (-not $Region) { throw "A region is required." }
}

function Get-RenderedCloudInit([string]$authKey, [string]$tsHost, [int]$idle, [int]$maxH) {
    if (-not (Test-Path $TemplateFile)) { throw "Missing $TemplateFile (keep it next to exitnode.ps1)." }
    $t = [IO.File]::ReadAllText($TemplateFile)
    $t = $t.Replace('__TS_AUTHKEY__', $authKey).Replace('__TS_HOST__', $tsHost)
    $t = $t.Replace('__IDLE_MIN__', "$idle").Replace('__MAX_HOURS__', "$maxH").Replace('__ACTIVE_KB__', "$ActiveKB")
    return ($t -replace "`r`n", "`n")   # Linux needs LF endings
}

function Get-IdleSettings {
    $script:IdleMinutes = if ($IdleMinutes -gt 0) { $IdleMinutes } else { [int](Read-WithDefault 'Delete VM after how many idle minutes?' '30') }
    $script:MaxHours    = if ($MaxHours    -gt 0) { $MaxHours }    else { [int](Read-WithDefault 'Delete VM after how many hours regardless?' '4') }
}

# ---------------------------------------------------------------- actions

function Invoke-Up {
    Require-Region
    Connect-Azure
    $ts = Get-TailscaleCli
    if (-not $ts) { Write-Warn "Tailscale for Windows not found - install it from https://tailscale.com/download (the VM will still be created)." }

    $rg = Get-RgName $Region
    if ((Invoke-Az group exists -n $rg) -eq 'true') {
        throw "Resource group '$rg' already exists. Run 'status' or 'down' for -Region $Region first."
    }

    Write-Host ""
    Write-Host "Create a Tailscale auth key at https://login.tailscale.com/admin/settings/keys" -ForegroundColor Gray
    Write-Host "  (Reusable: OFF, Ephemeral: ON)" -ForegroundColor Gray
    $authKey = Read-Secret 'Paste Tailscale auth key (input hidden)'
    if ($authKey -notmatch '^tskey-') { throw "That doesn't look like a Tailscale auth key (should start with 'tskey-')." }

    $adminUser = Read-WithDefault 'VM admin username' 'azureuser'
    Get-IdleSettings

    $tsHost = "exit-$Region-" + (Get-Date -Format 'MMdd-HHmm')
    $pub = @('id_ed25519.pub', 'id_rsa.pub') | ForEach-Object { Join-Path $env:USERPROFILE ".ssh\$_" } |
           Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($pub) { $sshArgs = @('--ssh-key-values', $pub); Write-Step "Using SSH key $pub" }
    else      { $sshArgs = @('--generate-ssh-keys');    Write-Step "No SSH key found - Azure CLI will generate one in ~\.ssh" }

    $ciPath = Join-Path ([IO.Path]::GetTempPath()) "exitnode-cloud-init-$([guid]::NewGuid()).yaml"
    [IO.File]::WriteAllText($ciPath, (Get-RenderedCloudInit $authKey $tsHost $IdleMinutes $MaxHours), (New-Object Text.UTF8Encoding $false))

    try {
        Write-Step "Creating resource group $rg..."
        Invoke-Az group create -n $rg -l $Region --tags "createdBy=exitnode" -o none | Out-Null
        $rgId = Invoke-Az group show -n $rg --query id -o tsv

        $created = $false; $i = 0
        foreach ($r in @($Region) + $FallbackRegions) {
            foreach ($size in $Sizes) {
                $i++
                Write-Step "Creating VM ($size in $r) - takes 1-3 minutes..."
                & az vm create -g $rg -n "exitnode-vm$i" -l $r `
                    --image $Image --size $size `
                    --admin-username $adminUser @sshArgs `
                    --nsg-rule NONE --public-ip-sku Standard --storage-sku Standard_LRS `
                    --custom-data $ciPath `
                    --assign-identity '[system]' --role Contributor --scope $rgId `
                    --only-show-errors -o none
                if ($LASTEXITCODE -eq 0) { $created = $true; break }
                Write-Warn "That size/region didn't work, trying the next option..."
            }
            if ($created) { break }
        }
        if (-not $created) {
            Write-Warn "Could not create a VM with any size/region. Cleaning up..."
            Invoke-Az group delete -n $rg --yes --no-wait | Out-Null
            throw "VM creation failed. Some regions need quota or access requests - try another region."
        }
    }
    finally {
        Remove-Item $ciPath -Force -ErrorAction SilentlyContinue
        $authKey = $null
    }

    New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
    Set-Content -Path (Get-StateFile $rg) -Value $tsHost
    Write-Step "VM created. Waiting for Tailscale node '$tsHost' to come online (usually 1-3 min)..."

    if (-not $ts) { Write-Host "Install Tailscale, then pick Exit node -> $tsHost from the tray icon." -ForegroundColor Green; return }

    $deadline = (Get-Date).AddMinutes(8); $online = $false
    while ((Get-Date) -lt $deadline) {
        & $ts ping -c 1 --timeout 3s $tsHost *> $null
        if ($LASTEXITCODE -eq 0) { $online = $true; break }
        Start-Sleep -Seconds 10
        Write-Host "." -NoNewline
    }
    Write-Host ""
    if (-not $online) { Write-Warn "Node not reachable yet. Check $AdminConsole, then run: tailscale set --exit-node=$tsHost"; return }

    Write-Step "Node is online."
    Write-Host "If exit nodes aren't auto-approved in your tailnet, open $AdminConsole," -ForegroundColor Gray
    Write-Host "click '...' on $tsHost -> Edit route settings -> tick 'Use as exit node'." -ForegroundColor Gray
    Read-Host "Press Enter to route this PC through $Region (Ctrl+C to skip)" | Out-Null

    for ($try = 1; $try -le 6; $try++) {
        & $ts set "--exit-node=$tsHost" --exit-node-allow-lan-access=true
        if ($LASTEXITCODE -eq 0) { break }
        Write-Warn "Exit node not usable yet (approved?). Retrying in 10s..."
        Start-Sleep -Seconds 10
    }
    if ($LASTEXITCODE -ne 0) { Write-Warn "Couldn't set the exit node. Approve it in $AdminConsole and pick it from the tray icon."; return }

    Start-Sleep -Seconds 3
    try {
        $ip = Invoke-RestMethod -Uri 'https://ipinfo.io/json' -TimeoutSec 15
        Write-Step "Your public IP is now $($ip.ip) ($($ip.city), $($ip.country))"
    } catch { Write-Warn "Couldn't verify public IP: $($_.Exception.Message)" }

    Write-Host ""
    Write-Host "All set. When done: .\exitnode.ps1 down -Region $Region" -ForegroundColor Green
    Write-Host "(The VM deletes itself after $IdleMinutes idle min or $MaxHours h; if your internet stops, run: tailscale set --exit-node=)" -ForegroundColor Gray
}

function Invoke-Down {
    $ts = Get-TailscaleCli
    if ($ts) { Write-Step "Switching this PC back to its normal connection..."; & $ts set --exit-node= 2>$null }
    if (-not $All) { Require-Region }
    Connect-Azure
    $groups = if ($All) { Get-ExitNodeGroups } else { @(Get-RgName $Region) }
    foreach ($rg in $groups) {
        if ((Invoke-Az group exists -n $rg) -eq 'true') {
            Write-Step "Deleting $rg (runs in the background, ~2-5 min)..."
            Invoke-Az group delete -n $rg --yes --no-wait | Out-Null
        } else {
            Write-Step "Nothing to delete - $rg doesn't exist."
        }
        Remove-Item (Get-StateFile $rg) -ErrorAction SilentlyContinue
    }
    if ($groups.Count -eq 0) { Write-Step "No exit-node resource groups found." }
    Write-Host "Done." -ForegroundColor Green
}

function Invoke-Status {
    if (-not $All) { Require-Region }
    Connect-Azure
    $ts = Get-TailscaleCli
    $groups = if ($All) { Get-ExitNodeGroups } else { @(Get-RgName $Region) }
    if ($groups.Count -eq 0) { Write-Step "No exit-node resource groups - nothing running, nothing billing."; return }
    foreach ($rg in $groups) {
        if ((Invoke-Az group exists -n $rg) -ne 'true') { Write-Step "$rg doesn't exist - nothing billing there."; continue }
        Write-Step "$rg ($(Invoke-Az group show -n $rg --query properties.provisioningState -o tsv)):"
        Invoke-Az vm list -g $rg -d --query "[].{Name:name, Location:location, Size:hardwareProfile.vmSize, Power:powerState}" -o table
        $sf = Get-StateFile $rg
        if ($ts -and (Test-Path $sf)) {
            $tsHost = (Get-Content $sf).Trim()
            & $ts ping -c 1 --timeout 3s $tsHost *> $null
            $state = if ($LASTEXITCODE -eq 0) { 'reachable' } else { 'not reachable' }
            Write-Host "Tailscale node $tsHost is $state."
        }
    }
}

function Invoke-List {
    Connect-Azure
    Invoke-Az group list --query "[?starts_with(name, '$Prefix-')].{Name:name, Location:location, State:properties.provisioningState}" -o table
}

function Invoke-Regions {
    Connect-Azure
    Invoke-Az account list-locations --query "[?metadata.regionType=='Physical'].{Region:name, Name:displayName, Geography:metadata.geographyGroup}" -o table
}

function Invoke-Render {
    Get-IdleSettings
    Get-RenderedCloudInit 'tskey-auth-XXXXXXXX' 'exit-preview' $IdleMinutes $MaxHours
}

switch ($Action) {
    'up'      { Invoke-Up }
    'down'    { Invoke-Down }
    'status'  { Invoke-Status }
    'list'    { Invoke-List }
    'regions' { Invoke-Regions }
    'render'  { Invoke-Render }
}
