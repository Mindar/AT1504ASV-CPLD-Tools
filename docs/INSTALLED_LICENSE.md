# Installed license and shared workspace

## License installation

The supplied `G:\license.dat` was copied to:

```text
C:\ATMEL_PLS_Tools\Licenses\license.dat
```

`MGLS_LICENSE_FILE` was configured for the current Windows user to include that location, preserving any existing entries. The source license remains at `G:\license.dat`; its contents are not reproduced here.

**Precision accepted the license** and completed target-specific VHDL and Verilog synthesis and EDIF fitting with verified pin assignments. The saved project reopened successfully, and the Verilog flow exported offline SVF. See [ProChip validation](PROCHIP_VALIDATION.md) for reproducible builds, the observed startup stall/retry, and current limits.

ModelSim is separately licensed and is not required for the requested synthesis workflow. Further routine checks now cover Precision only; the checker offers `--modelsim` if simulator testing is wanted later.

Restart an already-open ProChip/Precision application to inherit the new user environment. The project's Python runner also supplies the installed license location when `MGLS_LICENSE_FILE` is absent from an older terminal's environment.

## Shared workspace

The project was copied to **`G:\Standardprojekt`**, now the session's working directory and primary location for new documentation, code, tests, and results. The previous Documents copy was retained. Precision's intermittent pre-banner startup stall is handled by the Python startup handshake/retry described in [ProChip validation](PROCHIP_VALIDATION.md).

The shared drive corresponds to `\\VBoxSvr\shared_dir`. Prefer mapped `G:` paths for legacy tools. The first Precision check accepted the license but warned about its transcript path after expansion to UNC. A repeat check using `G:` successfully created its native transcript in the shared folder. The runner preserves mapped working-directory paths, and the checker captures console output separately from Precision's own `precision.log`.

Run a fresh check from PowerShell:

```powershell
Set-Location G:\Standardprojekt
python research\check_installed_license.py
```

Each check creates a new directory under `research\license_checks`. The successful mapped-path check is in:

```text
research\license_checks\20261111-215035-384415
```

This installation/configuration applies to the Windows VM. Direct execution on the host requires the corresponding host installation and valid licensing for that host.
