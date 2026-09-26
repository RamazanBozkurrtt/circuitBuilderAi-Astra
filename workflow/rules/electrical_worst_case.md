# Electrical worst-case verification

Follow [AGENTS.md](../../AGENTS.md). Guaranteed margins require
worst-case source, load, tolerance, temperature and operating-condition
bounds, not typical values. For supervision, check rising and falling
thresholds, hysteresis and tolerance against both valid-operation and fault
limits. Use regulator specifications only inside their guaranteed operating
conditions. Model startup and shutdown dependencies as an acyclic graph;
check brownout and power-off safe state. Mark unsupported margins UNKNOWN.
