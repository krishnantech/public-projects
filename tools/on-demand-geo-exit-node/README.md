# on-demand-geo-exit-node

On-demand Tailscale exit nodes in any Azure region. Pick a country, and the tool spins up a temporary exit node there that deletes itself when you're done.

Run one command (`exitnode.ps1`) to get a temporary [Tailscale](https://tailscale.com) exit node in the Azure region
of your choice. Your PC's traffic then leaves from that region. When you're done, everything is
deleted, or the VM deletes itself. Nothing is left running or billing between uses.

Typical uses: reaching your own accounts (banking, utilities, government portals) that only accept
connections from the country they serve while you're abroad, testing how your own site behaves
from another region, or securing traffic on untrusted Wi-Fi.

> **You are responsible for how you use this.** Using a VPN is restricted or illegal in some
> countries, and many websites' terms of service forbid hiding your location. Check the laws
> where you are and where the exit node is, and the terms of the services you access.

## How it works
- `up` creates a resource group and a small Ubuntu VM in the chosen region. The VM gets a
  [cloud-init](cloud-init.yaml) file that installs Tailscale and joins your tailnet as an
  exit node, using a single-use, ephemeral auth key that you paste in.
- The VM has **no inbound ports open to the internet**; Tailscale needs only outgoing connections.
- The VM has a managed identity limited to **its own resource group**. A cron job deletes that group
  after N idle minutes or M hours in total.
- `down` switches your PC back to its normal connection and deletes the resource group.

## Requirements
- Windows 10/11 with PowerShell 5.1+ or PowerShell 7
- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli-windows): `winget install -e --id Microsoft.AzureCLI`
- [Tailscale for Windows](https://tailscale.com/download), signed in
- An Azure subscription where you're **Owner**, because the script assigns a role to the VM's identity

## Setup
```powershell
git clone https://github.com/<you>/on-demand-geo-exit-node.git
cd on-demand-geo-exit-node
Unblock-File .\exitnode.ps1, .\cloud-init.yaml
```
Recommended: set an Azure budget alert (Cost Management → Budgets), for example $5/month.

## Usage
```powershell
.\exitnode.ps1 regions                                   # list region names
.\exitnode.ps1 up -Region centralindia -FallbackRegions southindia
.\exitnode.ps1 status -Region centralindia
.\exitnode.ps1 down -Region centralindia
.\exitnode.ps1 list                                      # all exit nodes this tool created
.\exitnode.ps1 down -All                                 # tear down everything
```

`up` asks for:
1. **Azure login**, only if you aren't already signed in.
2. **Tailscale auth key.** Create one at https://login.tailscale.com/admin/settings/keys with
   *Reusable* off and *Ephemeral* on. It's used once.
3. **VM admin username.** SSH uses your existing `~/.ssh` key, or generates one. You'll rarely need it.
4. **Idle timeout and maximum lifetime** (defaults 30 min / 4 h), or pass `-IdleMinutes` / `-MaxHours`.

It then waits for the node (named like `exit-centralindia-1122-1910`), lets you approve it as an
exit node, switches your PC to it and prints your new public IP and country.

You can run several regions at once. Each gets its own resource group (`exitnode-<region>-rg`).

### Skip the manual exit-node approval
In the Tailscale admin console → Access controls:
```json
"autoApprovers": { "exitNode": ["you@example.com"] }
```

## Caveats
- **If the VM deletes itself while your PC is still using it, your internet will stop.**
  Choose Exit node → None in the Tailscale tray icon, run `tailscale set --exit-node=`,
  or run `.\exitnode.ps1 down`.
- Exit traffic comes from a **cloud datacenter IP**. Some services (banks especially) block
  these regardless of country.
- Some Azure regions need a quota or access request before you can create VMs there. The script
  tries `-FallbackRegions` and several VM sizes before giving up.
- Cost is a few cents per hour while running, plus outbound data, and about $0 when it's down.

## Debugging
- SSH over Tailscale: `ssh azureuser@exit-<region>-<stamp>`, then read `/var/log/cloud-init-output.log`.
- If Tailscale never came up:
  `az vm run-command invoke -g exitnode-<region>-rg -n exitnode-vm1 --command-id RunShellScript --scripts "tail -50 /var/log/cloud-init-output.log"`
- To keep a VM alive longer: `sudo rm /etc/cron.d/exitnode-idle` on the VM. Then remember to run `down`.

## Security notes
- The auth key is single-use and ephemeral. Setup deletes it from the VM after joining.
- The VM's managed identity can only modify its own resource group.
- No secrets are stored in this repo or on your PC by the script.

## GitHub topics
Suggested: `tailscale`, `azure`, `exit-node`, `vpn`, `geo`, `powershell`, `cloud-init`, `ephemeral`

## Disclaimer
Not affiliated with or endorsed by Tailscale Inc. or Microsoft. "Tailscale" and "Azure" are
trademarks of their respective owners. Provided as-is under the MIT License; see [LICENSE](LICENSE).
