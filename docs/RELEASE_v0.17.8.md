# v0.17.8 · Clinical findings versus incidental equipment details

Live verification of v0.17.7 reached a second-screen rejection for unrequested
visible findings. The screen combined clinical signs with incidental lettering
and branding on medical equipment. This release narrows that check to clinical
contradictions. Ordinary cuff markings, electrode cables, bedside supplies,
unconnected equipment, fabric patterns and manufacturer lettering alone do not
indicate injury or an administered treatment.

Unrequested injury, bleeding, cyanosis, respiratory interfaces, active
interventions, diagnostic labels and conflicting monitor readings still fail.
All other screening rules and the explicit examination limitations introduced
in v0.17.7 remain. Pipeline version 6 refreshes the reviewer in running sessions.
No extra retries or model calls were introduced.

Only clinical-encounter-v0.13 is published. main and the IA branch are unchanged.

```bash
cd ~/Downloads
unzip -n management_reasoning_simulator_v0.17.8.zip
cd management_reasoning_simulator_v0.17.8
```
