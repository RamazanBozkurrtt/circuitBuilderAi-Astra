# PCB layout

Follow [AGENTS.md](../../AGENTS.md) and approved board constraints. Do
not place before schematic review/ERC; do not route before placement and
constraint approval. Protect Board A analog inputs from Board B switching
currents; control return paths, power loops, clocks, thermal paths and
connector geometry. Run DRC on each board and retain the reports. DRC PASS
does not establish EMC, thermal, SI/PI, manufacturing or product safety.
