# TEMPLATE: requires a licensed Precision OEM install and a configured .psp.
# Run in the directory containing design.psp. The project must already select
# the ATF1504ASV target, the 100-pin TQFP, sources, timing, and pin constraints.

if {[catch {
    open_project design.psp
    compile
    synthesize
    report_timing
    save_project
} message]} {
    puts stderr "BUILD_FAILED: $message"
    exit -force
}
puts "BUILD_COMPLETED: inspect reports and the expected fresh EDIF output"
exit -force
